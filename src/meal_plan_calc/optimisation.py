"""Propose a bounded, minimum-change schedule without mutating baseline data."""

from copy import deepcopy
from decimal import Decimal

from meal_plan_calc.evaluation import day_contributions
from meal_plan_calc.macro_profile import resolve_macros
from meal_plan_calc.nutrition import NUTRIENTS
from meal_plan_calc.planning import eating_meal_entries
from meal_plan_calc.portion_solver import solve_portions
from meal_plan_calc.shopping import (
    calculate_eating_quantities,
    calculate_shopping_quantities,
)
from meal_plan_calc.targets import Target
from meal_plan_calc.validation import checked_object, nonnegative_decimal, validate_data

D = Decimal


def profile_targets(profile, days, exercise):
    """Resolve base + per_kg * weight + per_hour * day duration, in native units."""
    if "schema_version" in profile:
        return resolve_macros(profile, days, exercise)[0]
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


def optimise(foods, meals, schedule, profile, preferences, *, time_limit=60.0):
    """Fit targets, then minimise plan changes using audited mixed-integer portions.

    Only explicitly adjustable food entries can change. Batch source quantities
    are variables shared by every consuming day. Unlisted foods remain fixed.
    """
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
    if "schema_version" in profile:
        goals, hard_goals, assumptions = resolve_macros(profile, days, exercise)
    else:
        goals = profile_targets(profile, days, exercise)
        hard_goals = {day: set(goals[day]) for day in days}
        assumptions = {
            "legacy_profile": "All configured goals remain hard; original formula semantics preserved"
        }
    checked_object(
        preferences, {"adjustable", "groups", "minimums", "excluded"}, {"adjustable"}
    )
    adjustable = checked_object(preferences["adjustable"], foods)
    excluded = preferences.get("excluded", [])
    if (
        not isinstance(excluded, list)
        or any(not isinstance(f, str) or f not in foods for f in excluded)
        or len(set(excluded)) != len(excluded)
    ):
        raise ValueError("excluded must list distinct known foods")
    if set(excluded) & set(adjustable):
        raise ValueError("Excluded foods must not also have adjustable portion rules")
    if not adjustable and not excluded:
        raise ValueError("Select at least one adjustable or excluded food")
    bounds_by_food, portion_rules = {}, {}
    for food, spec in adjustable.items():
        checked_object(
            spec,
            {"min_g", "max_g", "required", "step_g", "unit_g", "unit_label"},
            {"min_g", "max_g"},
        )
        low, high = (
            nonnegative_decimal(spec[k], f"{food}.{k}") for k in ("min_g", "max_g")
        )
        if low > high:
            raise ValueError(f"{food}: min_g exceeds max_g")
        required = spec.get("required", True)
        if type(required) is not bool:
            raise ValueError("required must be true or false")
        if not required and low == 0:
            raise ValueError("Optional foods need a positive minimum useful portion")
        if "step_g" in spec and "unit_g" in spec:
            raise ValueError("Specify step_g or unit_g, not both")
        if "unit_label" in spec and (
            "unit_g" not in spec
            or not isinstance(spec["unit_label"], str)
            or not spec["unit_label"].strip()
        ):
            raise ValueError("unit_label requires unit_g and a nonempty label")
        step = None
        if "step_g" in spec or "unit_g" in spec:
            step = nonnegative_decimal(
                spec.get("step_g", spec.get("unit_g")), "portion increment"
            )
            if step == 0:
                raise ValueError("Portion increment must be positive")
        bounds_by_food[food] = (low, high)
        portion_rules[food] = {"required": required, "step": step}
    for food in excluded:
        bounds_by_food[food] = (D(0), D(0))
        portion_rules[food] = {"required": True, "step": None}
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
    variables = sorted(key for key in used if key[1] in bounds_by_food)
    index = {key: i for i, key in enumerate(variables)}
    baseline = [D(str(meals[source][food])) for source, food in variables]
    n = len(variables)
    rows = []

    def add_constraint(label, coefficients, upper, penalty=None):
        vector = [D(0)] * n
        fixed = D(0)
        for key, coefficient in coefficients.items():
            if key in index:
                vector[index[key]] += coefficient
            else:
                fixed += coefficient * D(str(meals[key[0]][key[1]]))
        rows.append((label, vector, upper - fixed, penalty))

    for day in days:
        for nutrient, target in goals[day].items():
            penalty = (
                None if nutrient in hard_goals[day] else D(1) / max(target.value, D(1))
            )
            coeff = {
                key: fraction * D(str(foods[key[1]][nutrient])) / 100
                for key, fraction in consumption[day].items()
            }
            if target.mode != "minimum":
                add_constraint(
                    f"{day}.{nutrient}.maximum",
                    coeff,
                    target.value + target.tolerance,
                    penalty,
                )
            if target.mode != "maximum":
                add_constraint(
                    f"{day}.{nutrient}.minimum",
                    {k: -v for k, v in coeff.items()},
                    -max(D(0), target.value - target.tolerance),
                    penalty,
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
    quantities, solver = solve_portions(
        baseline,
        bounds,
        [portion_rules[food] for _, food in variables],
        rows,
        time_limit,
    )
    if quantities is None:
        stage = solver.get("baseline_change", solver["target_fit"])
        return {
            "status": "infeasible"
            if stage["status"] == 2
            else "limit_reached"
            if stage["status"] == 1
            else "solver_failure",
            "message": stage["message"],
            "solver_stages": solver,
            "proposed_meals": None,
            "guidance": "No plan exported. Check hard targets, portion rules, exclusions and food/group minimums together. No exact conflict set has been identified; hard constraints were not relaxed.",
        }
    residuals = solver.pop("constraint_audit")
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
                k: {
                    "value": t.value,
                    "mode": t.mode,
                    "tolerance": t.tolerance,
                    "hard": k in hard_goals[day],
                }
                for k, t in goals[day].items()
            },
            "baseline": totals(meals),
            "proposed": totals(proposal),
        }
    # Independently recompute target gaps through the existing nutrition engine.
    actual_primary, baseline_primary = D(0), D(0)
    for day, values in daily.items():
        values["target_deviations"] = {}
        for nutrient, target in goals[day].items():
            actual = values["proposed"][nutrient]
            below = (
                max(D(0), target.value - target.tolerance - actual)
                if target.mode != "maximum"
                else D(0)
            )
            above = (
                max(D(0), actual - target.value - target.tolerance)
                if target.mode != "minimum"
                else D(0)
            )
            gap = below + above
            original = values["baseline"][nutrient]
            baseline_gap = (
                max(D(0), target.value - target.tolerance - original)
                if target.mode != "maximum"
                else D(0)
            ) + (
                max(D(0), original - target.value - target.tolerance)
                if target.mode != "minimum"
                else D(0)
            )
            if nutrient in hard_goals[day] and gap > D("0.000001") * max(
                D(1), target.value
            ):
                raise ValueError(f"Final nutrition audit failed: {day}.{nutrient}")
            if nutrient not in hard_goals[day]:
                actual_primary += gap / max(target.value, D(1))
                baseline_primary += baseline_gap / max(target.value, D(1))
            values["target_deviations"][nutrient] = {
                "baseline_signed_from_centre": original - target.value,
                "baseline_outside_range": baseline_gap,
                "signed_from_centre": actual - target.value,
                "outside_range": gap,
            }
    if abs(actual_primary - solver["primary_actual"]) > D("0.0000001"):
        raise ValueError(
            "Independent nutrition calculation disagrees with solver model"
        )
    shopping = {}
    for basis in ("prepared", "eaten"):

        def quantities_for(plan):
            return (
                calculate_shopping_quantities(days, plan, exercise, extras)
                if basis == "prepared"
                else calculate_eating_quantities(
                    days, foods, plan, days, exercise, fractions, extras
                )
            )

        before, after = quantities_for(meals), quantities_for(proposal)
        shopping[basis] = {
            food: {
                "before_g": before.get(food, D(0)),
                "after_g": after.get(food, D(0)),
                "delta_g": after.get(food, D(0)) - before.get(food, D(0)),
                "state": foods[food].get("state", "unspecified"),
            }
            for food in sorted(before.keys() | after.keys())
        }
    return {
        "status": "optimal",
        "objective": "First minimise normalized target-range deviations; then normalized absolute changes from baseline",
        "primary_objective_value": actual_primary,
        "baseline_primary_objective_value": baseline_primary,
        "solver_stages": solver,
        "profile_assumptions": assumptions,
        "portion_rules": preferences,
        "shopping": shopping,
        "batch_effects": {
            day: [
                {
                    "source": source,
                    "food": food,
                    "consumed_change_g": fraction
                    * (D(str(proposal[source][food])) - D(str(meals[source][food]))),
                }
                for (source, food), fraction in consumption[day].items()
                if D(str(proposal[source][food])) != D(str(meals[source][food]))
            ]
            for day in days
        },
        "objective_value": sum(
            (abs(x - y) / max(y, D(50)) for x, y in zip(quantities, baseline)), D(0)
        ),
        "changes": changes,
        "days": daily,
        "constraint_audit": residuals,
        "proposed_meals": proposal,
        "note": "Portion increments reconstructed and audited before export; quantities retain raw/cooked states. Soft target ranges may remain unmet. User planning assumptions are not dietary advice or proof of nutritional completeness. Baseline untouched.",
    }
