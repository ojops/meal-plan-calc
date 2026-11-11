"""Propose a bounded, minimum-change schedule without mutating baseline data."""

from copy import deepcopy
from decimal import Decimal

from meal_plan_calc.evaluation import day_contributions
from meal_plan_calc.nutrition import NUTRIENTS
from meal_plan_calc.planning import eating_meal_entries
from meal_plan_calc.targets import Target
from meal_plan_calc.validation import nonnegative_decimal, validate_data

D = Decimal


def checked_object(value, allowed, required=()):
    if (
        not isinstance(value, dict)
        or set(value) - set(allowed)
        or set(required) - set(value)
    ):
        raise ValueError(
            f"Expected object with keys {sorted(allowed)}; required {sorted(required)}"
        )
    return value


def profile_targets(profile, days, exercise):
    """Resolve base + per_kg * weight + per_hour * day duration, in native units."""
    checked_object(
        profile,
        {"weight_kg", "duration_hours", "default", "exercise"},
        {"weight_kg", "default"},
    )
    weight = nonnegative_decimal(profile["weight_kg"], "weight_kg")
    if weight == 0:
        raise ValueError("weight_kg must be positive")
    durations = checked_object(profile.get("duration_hours", {}), days)
    durations = {
        day: nonnegative_decimal(v, f"{day} duration") for day, v in durations.items()
    }
    defaults = checked_object(profile["default"], NUTRIENTS)
    overrides = checked_object(profile.get("exercise", {}), set(exercise.values()))
    for values in overrides.values():
        checked_object(values, NUTRIENTS)
    result = {}
    for day in days:
        result[day] = {}
        for nutrient, spec in {**defaults, **overrides.get(exercise[day], {})}.items():
            checked_object(spec, {"base", "per_kg", "per_hour", "mode", "tolerance"})
            if not set(spec) & {"base", "per_kg", "per_hour"}:
                raise ValueError(f"{nutrient}: a target formula is required")
            base, per_kg, per_hour = (
                nonnegative_decimal(spec.get(k, 0), k)
                for k in ("base", "per_kg", "per_hour")
            )
            if per_hour and day not in durations:
                raise ValueError(
                    f"Supply duration_hours for {day}, including zero for rest"
                )
            result[day][nutrient] = Target(
                base + per_kg * weight + per_hour * durations.get(day, D(0)),
                spec.get("mode", "aim"),
                spec.get("tolerance", 0),
            )
        if not result[day]:
            raise ValueError(f"No targets for {day}")
    return result


def optimise(foods, meals, schedule, profile, preferences):
    """Solve a continuous LP and independently audit Decimal constraint residuals.

    Only explicitly adjustable food entries can change. Batch source quantities
    are variables shared by every consuming day. Unlisted foods remain fixed.
    """
    from scipy.optimize import linprog

    validate_data(foods, meals)
    checked_object(
        schedule,
        {"days", "exercise_split", "categories_split", "electrolytes_days"},
        {"days", "exercise_split", "categories_split"},
    )
    days, exercise = schedule["days"], schedule["exercise_split"]
    if (
        not isinstance(days, list)
        or not days
        or any(not isinstance(d, str) for d in days)
        or len(set(days)) != len(days)
    ):
        raise ValueError("Schedule days must be distinct names")
    checked_object(exercise, days, days)
    if any(not isinstance(kind, str) for kind in exercise.values()):
        raise ValueError("Exercise types must be names")
    fractions = checked_object(
        schedule["categories_split"], {f["category"] for f in foods.values()}
    )
    fractions = {k: nonnegative_decimal(v, k, maximum=1) for k, v in fractions.items()}
    extras = schedule.get("electrolytes_days", [])
    if (
        not isinstance(extras, list)
        or any(d not in days for d in extras)
        or len(set(extras)) != len(extras)
    ):
        raise ValueError("electrolytes_days must contain distinct schedule days")
    required = {*days, *exercise.values(), "snack", "breakfast", "supplements"}
    if extras:
        required.add("extra_electrolytes")
    if required - meals.keys():
        raise ValueError(f"Missing meals: {sorted(required - meals.keys())}")
    goals = profile_targets(profile, days, exercise)
    checked_object(preferences, {"adjustable", "groups", "minimums"}, {"adjustable"})
    adjustable = checked_object(preferences["adjustable"], foods)
    if not adjustable:
        raise ValueError("Select at least one adjustable food")
    bounds_by_food = {}
    for food, spec in adjustable.items():
        checked_object(spec, {"min_g", "max_g"}, {"min_g", "max_g"})
        low, high = (
            nonnegative_decimal(spec[k], f"{food}.{k}") for k in ("min_g", "max_g")
        )
        if low > high:
            raise ValueError(f"{food}: min_g exceeds max_g")
        bounds_by_food[food] = (low, high)
    groups = preferences.get("groups", {})
    if not isinstance(groups, dict):
        raise ValueError("groups must be an object of named food lists")
    for name, members in groups.items():
        if (
            not isinstance(members, list)
            or not members
            or any(not isinstance(f, str) or f not in foods for f in members)
            or len(set(members)) != len(members)
        ):
            raise ValueError(f"{name}: group must list distinct known foods")
    minimums = preferences.get("minimums", [])
    if not isinstance(minimums, list):
        raise ValueError("minimums must be a list")
    for spec in minimums:
        checked_object(spec, {"food", "group", "grams", "days"}, {"grams"})
        if ("food" in spec) == ("group" in spec):
            raise ValueError("Each minimum requires exactly one food or group")
        if ("food" in spec and spec["food"] not in foods) or (
            "group" in spec and spec["group"] not in groups
        ):
            raise ValueError("Unknown food or group in minimum")
        selected = spec.get("days", days)
        if (
            not isinstance(selected, list)
            or not selected
            or any(d not in days for d in selected)
            or len(set(selected)) != len(selected)
        ):
            raise ValueError("Minimum days must be distinct schedule day names")
        nonnegative_decimal(spec["grams"], "minimum grams")

    # Build consumed quantity coefficients using the existing allocation rules.
    consumption = {}
    used = set()
    for day in days:
        consumption[day] = {}
        for _, source, meal, split in eating_meal_entries(
            day, foods, meals, days, exercise, fractions, extras
        ):
            for food in meal:
                key = (source, food)
                fraction = split[foods[food]["category"]] if split is not None else D(1)
                consumption[day][key] = consumption[day].get(key, D(0)) + fraction
                used.add(key)
    missing = set(adjustable) - {food for _, food in used}
    if missing:
        raise ValueError(
            f"Adjustable foods not consumed by this schedule: {sorted(missing)}"
        )
    variables = sorted(key for key in used if key[1] in adjustable)
    index = {key: i for i, key in enumerate(variables)}
    baseline = [D(str(meals[source][food])) for source, food in variables]
    n = len(variables)
    rows = []

    def add_constraint(label, coefficients, upper):
        vector = [D(0)] * n
        fixed = D(0)
        for key, coefficient in coefficients.items():
            if key in index:
                vector[index[key]] += coefficient
            else:
                fixed += coefficient * D(str(meals[key[0]][key[1]]))
        rows.append((label, vector, upper - fixed))

    for day in days:
        for nutrient, target in goals[day].items():
            coeff = {
                key: fraction * D(str(foods[key[1]][nutrient])) / 100
                for key, fraction in consumption[day].items()
            }
            if target.mode != "minimum":
                add_constraint(
                    f"{day}.{nutrient}.maximum", coeff, target.value + target.tolerance
                )
            if target.mode != "maximum":
                add_constraint(
                    f"{day}.{nutrient}.minimum",
                    {k: -v for k, v in coeff.items()},
                    -max(D(0), target.value - target.tolerance),
                )
        for number, spec in enumerate(minimums):
            if day not in spec.get("days", days):
                continue
            members = [spec["food"]] if "food" in spec else groups[spec["group"]]
            add_constraint(
                f"{day}.food_minimum.{number}",
                {k: -v for k, v in consumption[day].items() if k[1] in members},
                -nonnegative_decimal(spec["grams"], "grams"),
            )
    bounds = [bounds_by_food[food] for _, food in variables]
    a, b = [], []
    for _, vector, upper in rows:
        scale = max(D(1), abs(upper), *(abs(x) for x in vector))
        a.append([float(x / scale) for x in vector] + [0.0] * n)
        b.append(float(upper / scale))
    # Auxiliary d_i encodes |x_i - baseline_i|; normalize by max(baseline, 50g).
    for i, original in enumerate(baseline):
        for sign in (1, -1):
            vector = [0.0] * (2 * n)
            vector[i], vector[n + i] = sign, -1
            a.append(vector)
            b.append(float(sign * original))
    result = linprog(
        [0.0] * n + [1 / float(max(v, D(50))) for v in baseline],
        A_ub=a,
        b_ub=b,
        bounds=[(float(lo), float(hi)) for lo, hi in bounds] + [(0, None)] * n,
        method="highs",
    )
    if not result.success:
        return {
            "status": "infeasible" if result.status == 2 else "solver_failure",
            "message": result.message,
            "proposed_meals": None,
            "guidance": "Check target ranges, portion bounds and food/group minimums together. Constraints have not been silently relaxed.",
        }
    quantities = [D(str(x)) for x in result.x[:n]]
    residuals = []
    for label, vector, upper in rows:
        residual = sum((x * c for x, c in zip(quantities, vector)), D(0)) - upper
        tolerance = D("0.000001") * max(D(1), abs(upper))
        residuals.append(
            {
                "constraint": label,
                "violation": max(D(0), residual),
                "numerical_tolerance": tolerance,
            }
        )
        if residual > tolerance:
            raise ValueError(f"Solver output failed independent check: {label}")
    for x, (low, high) in zip(quantities, bounds):
        if not low - D("0.000001") <= x <= high + D("0.000001"):
            raise ValueError("Solver output violates a portion bound")
    proposal = deepcopy(meals)
    changes = []
    for (source, food), old, new in zip(variables, baseline, quantities):
        proposal[source][food] = new
        if abs(new - old) > D("0.000001"):
            changes.append(
                {
                    "source": source,
                    "food": food,
                    "before_g": old,
                    "after_g": new,
                    "delta_g": new - old,
                }
            )
    daily = {}
    for day in days:

        def totals(plan):
            entries = day_contributions(
                day, foods, plan, days, exercise, fractions, extras
            )
            return {
                nutrient: sum((e["nutrients"][nutrient] for e in entries), D(0))
                for nutrient in NUTRIENTS
            }

        daily[day] = {
            "exercise": exercise[day],
            "targets": {
                k: {"value": t.value, "mode": t.mode, "tolerance": t.tolerance}
                for k, t in goals[day].items()
            },
            "baseline": totals(meals),
            "proposed": totals(proposal),
        }
    return {
        "status": "optimal",
        "objective": "minimise sum(abs(quantity-baseline)/max(baseline,50g))",
        "objective_value": sum(
            (abs(x - y) / max(y, D(50)) for x, y in zip(quantities, baseline)), D(0)
        ),
        "changes": changes,
        "days": daily,
        "constraint_audit": residuals,
        "proposed_meals": proposal,
        "note": "Continuous gram quantities in recorded raw/cooked states; not rounded for cooking. Illustrative user targets, not dietary advice. Baseline untouched.",
    }
