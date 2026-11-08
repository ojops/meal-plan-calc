"""Explain daily nutrition using the existing batch allocation calculations."""

from decimal import Decimal

from meal_plan_calc.nutrition import calculate_meal_nutrition
from meal_plan_calc.planning import eating_meal_entries
from meal_plan_calc.validation import nonnegative_decimal


def day_contributions(
    day: str,
    foods: dict,
    meals: dict,
    days: list[str],
    exercise_split: dict[str, str],
    categories_split: dict[str, Decimal],
    electrolytes_days=(),
) -> list[dict]:
    """Return each consumed ingredient's quantity, state, source and nutrients.

    Contributions explain intake; they do not attribute a shortfall to a food
    or imply that increasing a contributor is nutritionally appropriate.
    """
    result = []
    for name, source, meal, fractions in eating_meal_entries(
        day, foods, meals, days, exercise_split, categories_split, electrolytes_days
    ):
        for ingredient, quantity in meal.items():
            fraction = (
                fractions[foods[ingredient]["category"]]
                if fractions is not None
                else Decimal(1)
            )
            result.append(
                {
                    "meal": name,
                    "source": source,
                    "ingredient": ingredient,
                    "quantity": nonnegative_decimal(quantity, ingredient) * fraction,
                    "state": foods[ingredient].get("state", "unspecified"),
                    "nutrients": calculate_meal_nutrition(
                        {ingredient: quantity}, foods, fractions
                    ),
                }
            )
    return result
