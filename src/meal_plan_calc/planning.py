from decimal import Decimal

from meal_plan_calc.validation import nonnegative_decimal

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
EXERCISE_SPLIT = dict(
    zip(DAYS, ("strength", "run", "strength", "run", "mobility", "run", "run"))
)


CATEGORIES_SPLIT = {
    category: Decimal(2) / Decimal(3)
    for category in ("protein", "veg", "extra", "fruit", "dairy", "nut")
}


CATEGORIES_SPLIT["carb"] = Decimal(3) / Decimal(4)


def allocation_fractions(meal, foods, categories_split, meal_part):
    if meal_part not in ("lunch", "dinner"):
        raise ValueError("meal_part must be 'lunch' or 'dinner'")
    result = {}
    for ingredient in meal:
        category = foods[ingredient]["category"]
        fraction = nonnegative_decimal(
            categories_split.get(category, 1), f"{category} fraction", maximum=1
        )
        result[category] = fraction if meal_part == "lunch" else 1 - fraction
    return result


def immediate_meal_names(day, exercise_split, electrolytes_days=()):
    """Meals consumed on this day without batch allocation."""
    names = ["snack", "supplements", exercise_split[day], "breakfast"]
    if day in electrolytes_days:
        names.append("extra_electrolytes")
    return names


def eating_meals(
    day, foods, meals, days, exercise_split, categories_split, electrolytes_days=()
):
    """Yield meals and fractions eaten today, including periodic carry over"""
    for _, _, meal, fractions in eating_meal_entries(
        day, foods, meals, days, exercise_split, categories_split, electrolytes_days
    ):
        yield meal, fractions


def eating_meal_entries(
    day, foods, meals, days, exercise_split, categories_split, electrolytes_days=()
):
    """Yield meal name, source key, quantities and fractions, with batch provenance."""
    if not days or len(set(days)) != len(days):
        raise ValueError("The repeating schedule must contain distinct days")
    index = days.index(day)
    for meal_type in immediate_meal_names(day, exercise_split, electrolytes_days):
        yield meal_type, meal_type, meals[meal_type], None
    for offset, part in ((1, "lunch"), (2, "dinner")):
        source = days[(index - offset) % len(days)]
        meal = meals[source]
        yield (
            part,
            source,
            meal,
            allocation_fractions(meal, foods, categories_split, part),
        )
