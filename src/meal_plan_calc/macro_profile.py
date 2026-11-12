"""Explicit calorie budgets and editable macro assumptions, not prescriptions."""

from decimal import Decimal as D

from meal_plan_calc.nutrition import NUTRIENTS
from meal_plan_calc.targets import Target
from meal_plan_calc.validation import checked_object
from meal_plan_calc.validation import nonnegative_decimal as number

MACROS = {"protein", "fat", "carbs"}
CORE = MACROS | {"calories"}


def resolve_macros(profile, days, exercise):
    checked_object(
        profile,
        {
            "schema_version",
            "weight_kg",
            "default",
            "exercise",
            "hard_targets",
            "hard_limits",
        },
        {"schema_version", "weight_kg", "default", "exercise"},
    )
    if type(profile["schema_version"]) is not int or profile["schema_version"] != 2:
        raise ValueError("Macro profile schema_version must be 2")
    weight = number(profile["weight_kg"], "weight_kg")
    if not weight:
        raise ValueError("weight_kg must be positive")
    settings = {
        "protein_g_per_kg",
        "fat_fraction",
        "tolerance_fraction",
        "macro_overrides",
    }
    defaults = checked_object(
        profile["default"],
        settings,
        {"protein_g_per_kg", "fat_fraction", "tolerance_fraction"},
    )
    kinds = set(exercise.values())
    overrides = checked_object(profile["exercise"], kinds, kinds)
    hard = profile.get("hard_targets", [])
    if (
        not isinstance(hard, list)
        or any(not isinstance(k, str) or k not in CORE for k in hard)
        or len(set(hard)) != len(hard)
    ):
        raise ValueError("hard_targets must list distinct calorie/macro names")
    limits = checked_object(profile.get("hard_limits", {}), {"default", "exercise"})
    default_limits = checked_object(limits.get("default", {}), set(NUTRIENTS) - CORE)
    exercise_limits = checked_object(limits.get("exercise", {}), kinds)
    resolved, assumptions = {}, {}
    for kind in sorted(kinds):
        spec = checked_object(overrides[kind], settings | {"calories"}, {"calories"})
        merged = {**defaults, **spec}
        calories = number(spec["calories"], f"{kind}.calories")
        if not calories:
            raise ValueError("Daily calorie budgets must be positive")
        coefficient = number(merged["protein_g_per_kg"], "protein_g_per_kg")
        fraction = number(merged["fat_fraction"], "fat_fraction", maximum=1)
        tolerance = number(
            merged["tolerance_fraction"], "tolerance_fraction", maximum=1
        )
        explicit = {
            **checked_object(defaults.get("macro_overrides", {}), MACROS),
            **checked_object(spec.get("macro_overrides", {}), MACROS),
        }
        explicit = {k: number(v, f"{kind}.{k} override") for k, v in explicit.items()}
        protein = explicit.get("protein", weight * coefficient)
        fat = explicit.get("fat", calories * fraction / 9)
        remainder = calories - 4 * protein - 9 * fat
        if remainder < 0:
            raise ValueError(
                f"{kind}: protein/fat consume more than the calorie budget"
            )
        carbs = explicit.get("carbs", remainder / 4)
        discrepancy = 4 * protein + 9 * fat + 4 * carbs - calories
        if abs(discrepancy) > max(D("0.00000001"), calories * tolerance):
            raise ValueError(
                f"{kind}: explicit macros conflict with the calorie budget/tolerance"
            )
        centres = {"calories": calories, "protein": protein, "fat": fat, "carbs": carbs}
        targets = {k: Target(v, "aim", v * tolerance) for k, v in centres.items()}
        for nutrient, limit in {
            **default_limits,
            **checked_object(exercise_limits.get(kind, {}), set(NUTRIENTS) - CORE),
        }.items():
            checked_object(limit, {"value", "mode", "tolerance"}, {"value", "mode"})
            if limit["mode"] not in ("minimum", "maximum"):
                raise ValueError("hard_limits require minimum or maximum mode")
            targets[nutrient] = Target(**limit)
        resolved[kind] = targets
        assumptions[kind] = {
            "weight_kg": weight,
            "calories_include_exercise": True,
            "protein_g_per_kg": coefficient,
            "fat_fraction": fraction,
            "tolerance_fraction": tolerance,
            "macro_overrides_g": explicit,
            "macro_energy_minus_budget_kcal": discrepancy,
        }
    daily = {day: resolved[exercise[day]] for day in days}
    hard_daily = {day: set(hard) | (set(daily[day]) - CORE) for day in days}
    return daily, hard_daily, assumptions
