from decimal import Decimal

from meal_plan_calc.planning import allocation_fractions, eating_meals
from meal_plan_calc.validation import nonnegative_decimal

NUTRIENTS = (
    "calories",
    "fat",
    "saturates",
    "carbs",
    "sugars",
    "fibre",
    "protein",
    "salt",
)


def empty_nutrition_totals() -> dict[str, Decimal]:
    """Return zero-valued totals for every tracked nutrient."""
    return {nutrient: Decimal("0") for nutrient in NUTRIENTS}


def calculate_meal_nutrition(
    meal: dict,
    foods: dict,
    category_fractions: dict[str, Decimal] | None = None,
) -> dict[str, Decimal]:
    """Sum meal nutrients, optionally applying per-category allocation fractions."""
    totals = empty_nutrition_totals()
    for ingredient, quantity in meal.items():
        food = foods[ingredient]
        fraction = (
            nonnegative_decimal(
                category_fractions.get(food["category"], 1),
                "category fraction",
                maximum=1,
            )
            if category_fractions is not None
            else Decimal("1")
        )
        quantity = nonnegative_decimal(quantity, f"{ingredient} quantity")
        for nutrient in NUTRIENTS:
            value_per_100g = nonnegative_decimal(
                food[nutrient], f"{ingredient}.{nutrient}"
            )
            totals[nutrient] += value_per_100g * quantity * fraction / Decimal("100")
    return totals


def calculate_cooking_nutrition(
    day: str,
    foods: dict,
    meals: dict,
    categories_split: dict[str, Decimal],
    meal_part: str,
) -> dict[str, Decimal]:
    """Return the lunch or dinner share of a day's cooked batch."""
    fractions = allocation_fractions(meals[day], foods, categories_split, meal_part)
    return calculate_meal_nutrition(
        meals[day],
        foods,
        category_fractions=fractions,
    )


def calculate_meal_type_nutrition(
    meal_type: str,
    foods: dict,
    meals: dict,
) -> dict[str, Decimal]:
    """Return nutrient totals for the selected meal type."""
    return calculate_meal_nutrition(meals[meal_type], foods)


def calculate_day_eating_nutrition(
    day: str,
    foods: dict,
    meals: dict,
    days: list[str],
    exercise_split: dict[str, str],
    categories_split: dict[str, Decimal],
) -> dict[str, Decimal]:
    """Return nutrients eaten on a day, including portions from earlier batches."""
    totals = empty_nutrition_totals()
    for meal, fractions in eating_meals(
        day, foods, meals, days, exercise_split, categories_split
    ):
        meal_totals = calculate_meal_nutrition(meal, foods, fractions)
        for nutrient in NUTRIENTS:
            totals[nutrient] += meal_totals[nutrient]
    return totals
