from decimal import Decimal

def calculate_shopping_quantities(
    days: list[str],
    meals: dict,
    exercise_split: dict[str, str],
) -> dict[str, Decimal]:
    """Calculate the total quantity of each ingredient needed for a given set of days"""
    shopping_quantities: dict[str, Decimal] = {}

    for day in days:
        meal_types = [
            day,
            "breakfast",
            "snack",
            "supplements",
            exercise_split[day],
        ]

        for meal_type in meal_types:
            for ingredient, quantity in meals[meal_type].items():
                quantity = Decimal(str(quantity))

                shopping_quantities[ingredient] = (
                    shopping_quantities.get(ingredient, Decimal("0"))
                    + quantity
                )

    return shopping_quantities
