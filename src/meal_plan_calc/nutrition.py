from decimal import Decimal

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
    """Produce dictionary with all nutrients as 0"""
    return {nutrient: Decimal("0") for nutrient in NUTRIENTS}


def calculate_meal_nutrition(
    meal: dict,
    foods: dict,
    category_fractions: dict[str, Decimal] | None = None,
) -> dict[str, Decimal]:
    """ Calculate nutrition for individual meal, optionally applying category fraction"""
    totals = empty_nutrition_totals()

    for ingredient, quantity in meal.items():
        food = foods[ingredient]
        fraction = (
            category_fractions.get(food["category"], Decimal("1"))
            if category_fractions is not None
            else Decimal("1")
        )

        quantity = Decimal(str(quantity))

        for nutrient in NUTRIENTS:
            value_per_100g = Decimal(str(food[nutrient]))
            totals[nutrient] += (
                value_per_100g * quantity * fraction / Decimal("100")
            )

    return totals


def calculate_cooking_nutrition(
    day: str,
    foods: dict,
    meals: dict,
    categories_split: dict[str, Decimal],
    meal_part: str,
) -> dict[str, Decimal]:
    """Calculate nutrition total for lunch or dinner cooked on given day"""
    if meal_part == "lunch":
        fractions = categories_split
    elif meal_part == "dinner":
        fractions = {
            category: Decimal("1") - fraction
            for category, fraction in categories_split.items()
        }
    else:
        raise ValueError("meal_part must be 'lunch' or 'dinner'")

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
    """Calculate nutrition totals for specific meal type"""
    return calculate_meal_nutrition(meals[meal_type], foods)


def calculate_day_eating_nutrition(
    day: str,
    foods: dict,
    meals: dict,
    days: list[str],
    exercise_split: dict[str, str],
    categories_split: dict[str, Decimal],
) -> dict[str, Decimal]:
    """Calculates total nutrition for day ate food on"""
    totals = empty_nutrition_totals()
    day_index = days.index(day)

    meal_types = [
        "snack",
        "supplements",
        exercise_split[day],
        "breakfast",
    ]

    for meal_type in meal_types:
        meal_totals = calculate_meal_type_nutrition(
            meal_type, foods, meals
        )
        for nutrient in NUTRIENTS:
            totals[nutrient] += meal_totals[nutrient]

    # Lunch is prepared from the previous day's cooking
    # Dinner is prepared from the cooking two days earlier
    previous_day = days[(day_index - 1) % len(days)]
    two_days_previous = days[(day_index - 2) % len(days)]

    for cooking_day, meal_part in (
        (previous_day, "lunch"),
        (two_days_previous, "dinner"),
    ):
        meal_totals = calculate_cooking_nutrition(
            cooking_day, foods, meals, categories_split, meal_part
        )
        for nutrient in NUTRIENTS:
            totals[nutrient] += meal_totals[nutrient]

    return totals