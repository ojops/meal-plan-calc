from decimal import Decimal
import json
from pathlib import Path

from meal_plan_calc import nutrition, optimiser

# saturates are always included in fat total
# sugars are always included in carbs total
# fibre is not included in carbs total
# meals.json just using meal plan values, maybe not clear what "state", cooked/raw

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

DAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

EXERCISE_SPLIT = {
    "monday": "strength",
    "tuesday": "run",
    "wednesday": "strength",
    "thursday": "run",
    "friday": "mobility",
    "saturday": "run",
    "sunday": "run",
}

CATEGORIES_SPLIT = {
    "protein": Decimal("2") / Decimal("3"),
    "carb": Decimal("3") / Decimal("4"),
    "veg": Decimal("2") / Decimal("3"),
    "extra": Decimal("2") / Decimal("3"),
    "fruit": Decimal("2") / Decimal("3"),
    "dairy": Decimal("2") / Decimal("3"),
    "nut": Decimal("2") / Decimal("3"),
}


def print_nutrition(totals: dict[str, Decimal]) -> None:
    for nutrient, value in totals.items():
        print(f"{nutrient}: {value.quantize(Decimal('0.01'))}")


def main() -> None:
    with (
        open(DATA_DIR / "foods.json", encoding="utf-8") as foods_file,
        open(DATA_DIR / "meals.json", encoding="utf-8") as meals_file,
    ):
        foods = json.load(foods_file)
        meals = json.load(meals_file)

    for day in DAYS:
        print(day.upper())

        totals = nutrition.calculate_day_eating_nutrition(
            day,
            foods,
            meals,
            DAYS,
            EXERCISE_SPLIT,
            CATEGORIES_SPLIT,
        )

        print_nutrition(totals)
        print("---")


if __name__ == "__main__":
    main()