import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


def nonnegative_decimal(value, label: str, *, maximum=None) -> Decimal:
    try:
        if isinstance(value, bool):
            raise ValueError
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{label} must be a finite non negative number") from None
    if (
        not number.is_finite()
        or number < 0
        or (maximum is not None and number > maximum)
    ):
        raise ValueError(
            f"{label} must be finite and between 0 and {maximum or 'infinity'}"
        )
    return number


def load_json(path: Path) -> dict:
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError(f"Non finite JSON number: {value}")

    with path.open(encoding="utf-8") as handle:
        result = json.load(
            handle,
            parse_float=Decimal,
            object_pairs_hook=unique_object,
            parse_constant=invalid_constant,
        )
    if not isinstance(result, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return result


def validate_data(foods: dict, meals: dict) -> None:
    from meal_plan_calc.nutrition import NUTRIENTS

    for name, food in foods.items():
        if not isinstance(food, dict) or not isinstance(food.get("category"), str):
            raise ValueError(f"{name}: expected food object with a category")
        if not food["category"]:
            raise ValueError(f"{name}: empty category")
        for nutrient in NUTRIENTS:
            if nutrient not in food:
                raise ValueError(f"{name}: missing nutrient {nutrient}")
            nonnegative_decimal(
                food[nutrient],
                f"{name}.{nutrient}",
                maximum=None if nutrient == "calories" else 100,
            )
        for component, total in (("sugars", "carbs"), ("saturates", "fat")):
            if Decimal(str(food[component])) > Decimal(str(food[total])):
                raise ValueError(f"{name}: {component} exceeds {total}")
        if "state" in food and food["state"] not in ("raw", "cooked"):
            raise ValueError(f"{name}: state must be raw or cooked")
    for name, meal in meals.items():
        if name == "comments":
            continue
        if not isinstance(meal, dict):
            raise ValueError(f"{name}: expected ingredient quantities")
        for ingredient, quantity in meal.items():
            if ingredient not in foods:
                raise ValueError(f"{name}: unknown ingredient {ingredient}")
            nonnegative_decimal(quantity, f"{name}.{ingredient}")


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
