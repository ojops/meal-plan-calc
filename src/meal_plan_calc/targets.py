"""Optional user-defined nutrient goals, never dietary recommendations."""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from meal_plan_calc.nutrition import NUTRIENTS
from meal_plan_calc.validation import load_json, nonnegative_decimal


@dataclass(frozen=True)
class Target:
    """Represent an aim, minimum or maximum in kcal or nutrient grams."""

    value: Decimal
    mode: str = "aim"
    tolerance: Decimal = Decimal(0)

    def __post_init__(self):
        object.__setattr__(self, "value", nonnegative_decimal(self.value, "target"))
        object.__setattr__(
            self, "tolerance", nonnegative_decimal(self.tolerance, "tolerance")
        )
        if self.mode not in ("aim", "minimum", "maximum"):
            raise ValueError("Target mode must be aim, minimum or maximum")


@dataclass(frozen=True)
class Comparison:
    actual: Decimal
    target: Target
    deviation: Decimal
    absolute_deviation: Decimal
    percentage_deviation: Decimal | None
    status: str


def compare(actual: Decimal, target: Target) -> Comparison:
    """Compare without rounding; percentage deviation is undefined at target zero."""
    actual = nonnegative_decimal(actual, "actual nutrition")
    deviation = actual - target.value
    below = actual < target.value - target.tolerance
    above = actual > target.value + target.tolerance
    if target.mode == "minimum":
        status = "below minimum" if below else "met"
    elif target.mode == "maximum":
        status = "above maximum" if above else "met"
    else:
        status = "below range" if below else "above range" if above else "within range"
    return Comparison(
        actual,
        target,
        deviation,
        abs(deviation),
        deviation / target.value * 100 if target.value else None,
        status,
    )


def load_targets(path: Path, exercise_types: set[str]) -> dict[str, dict[str, Target]]:
    """Resolve defaults and nutrient-level exercise overrides for every day type.

    Overrides replace a complete nutrient specification. Omitted nutrients are
    unassessed, not zero targets. Unknown keys and uncovered day types are errors.
    """
    data = load_json(path)
    if set(data) - {"default", "exercise"} or not data:
        raise ValueError("Targets file accepts only default and exercise objects")

    def parse(values, label):
        if not isinstance(values, dict):
            raise ValueError(f"{label} must be an object")
        result = {}
        for nutrient, spec in values.items():
            if nutrient not in NUTRIENTS:
                raise ValueError(f"Unknown target nutrient: {nutrient}")
            if (
                not isinstance(spec, dict)
                or "value" not in spec
                or set(spec) - {"value", "mode", "tolerance"}
            ):
                raise ValueError(
                    f"{label}.{nutrient}: expected value, optional mode and tolerance"
                )
            result[nutrient] = Target(**spec)
        return result

    defaults = parse(data.get("default", {}), "default")
    overrides = data.get("exercise", {})
    if not isinstance(overrides, dict) or set(overrides) - exercise_types:
        raise ValueError(
            "Target exercise keys must match exercise types in the schedule"
        )
    resolved = {}
    for kind in sorted(exercise_types):
        resolved[kind] = {
            **defaults,
            **parse(overrides.get(kind, {}), f"exercise.{kind}"),
        }
        if not resolved[kind]:
            raise ValueError(
                f"No nutritional targets configured for exercise type {kind}"
            )
    return resolved
