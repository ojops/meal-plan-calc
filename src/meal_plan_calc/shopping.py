from decimal import Decimal

from meal_plan_calc.planning import eating_meals, immediate_meal_names
from meal_plan_calc.validation import nonnegative_decimal


def calculate_shopping_quantities(
    days: list[str],
    meals: dict,
    exercise_split: dict[str, str],
    electrolytes_days=(),
) -> dict[str, Decimal]:
    """Calculate the total quantity of each ingredient needed for a given set of days"""
    shopping_quantities: dict[str, Decimal] = {}
    for day in days:
        meal_types = [
            day,
            *immediate_meal_names(day, exercise_split, electrolytes_days),
        ]
        for meal_type in meal_types:
            for ingredient, quantity in meals[meal_type].items():
                quantity = nonnegative_decimal(quantity, f"{ingredient} quantity")
                shopping_quantities[ingredient] = (
                    shopping_quantities.get(ingredient, Decimal("0")) + quantity
                )
    return shopping_quantities


def calculate_eating_quantities(
    days, foods, meals, schedule, exercise_split, categories_split, electrolytes_days=()
):
    """Quantities consumed on selected days, rather than batches prepared then"""
    totals = {}
    for day in days:
        for meal, fractions in eating_meals(
            day,
            foods,
            meals,
            schedule,
            exercise_split,
            categories_split,
            electrolytes_days,
        ):
            for ingredient, quantity in meal.items():
                fraction = (
                    fractions[foods[ingredient]["category"]]
                    if fractions is not None
                    else Decimal(1)
                )
                amount = (
                    nonnegative_decimal(quantity, f"{ingredient} quantity") * fraction
                )
                totals[ingredient] = totals.get(ingredient, Decimal(0)) + amount
    return totals
