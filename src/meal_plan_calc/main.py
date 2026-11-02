import argparse
from decimal import Decimal
from pathlib import Path

from meal_plan_calc import nutrition, shopping
from meal_plan_calc.planning import CATEGORIES_SPLIT, DAYS, EXERCISE_SPLIT
from meal_plan_calc.validation import load_json, nonnegative_decimal, validate_data

PACKAGE_DATA = Path(__file__).with_name("data")
DATA_DIR = (
    PACKAGE_DATA
    if PACKAGE_DATA.is_dir()
    else Path(__file__).resolve().parents[2] / "data"
)


def print_nutrition(totals: dict[str, Decimal]) -> None:
    for nutrient, value in totals.items():
        print(f"{nutrient}: {value:.2f}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--foods", type=Path, default=DATA_DIR / "foods.json")
    parser.add_argument("--meals", type=Path, default=DATA_DIR / "meals.json")
    parser.add_argument(
        "--schedule",
        type=Path,
        help="JSON with days, exercise_split and categories_split",
    )
    parser.add_argument(
        "--start-day", help="Default: first day of the repeating schedule"
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Number of consecutive days"
    )
    parser.add_argument(
        "--report", choices=("both", "nutrition", "shopping"), default="both"
    )
    parser.add_argument(
        "--shopping-basis", choices=("prepared", "eaten"), default="prepared"
    )
    args = parser.parse_args(argv)
    try:
        foods, meals = load_json(args.foods), load_json(args.meals)
        validate_data(foods, meals)
        schedule = (
            load_json(args.schedule)
            if args.schedule
            else {
                "days": DAYS,
                "exercise_split": EXERCISE_SPLIT,
                "categories_split": CATEGORIES_SPLIT,
            }
        )
        days = schedule["days"]
        exercise = schedule["exercise_split"]
        fractions = schedule["categories_split"]
        if (
            not isinstance(days, list)
            or not days
            or any(not isinstance(d, str) for d in days)
            or len(set(days)) != len(days)
        ):
            raise ValueError("Schedule days must be a non empty list of distinct names")
        if not isinstance(exercise, dict) or not isinstance(fractions, dict):
            raise ValueError(
                "Schedule exercise_split and categories_split must be objects"
            )
        fractions = {
            k: nonnegative_decimal(v, f"{k} fraction", maximum=1)
            for k, v in fractions.items()
        }
        for day in days:
            if day not in meals or day not in exercise or exercise[day] not in meals:
                raise ValueError(f"Missing cooking or exercise meal for {day}")
        for name in ("breakfast", "snack", "supplements"):
            if name not in meals:
                raise ValueError(f"Missing meal {name}")
        if args.days <= 0:
            raise ValueError("--days must be positive")
        start = days.index(args.start_day or days[0])
        selected = [days[(start + i) % len(days)] for i in range(args.days)]
        if args.report in ("both", "nutrition"):
            for day in selected:
                print(day.upper())
                print_nutrition(
                    nutrition.calculate_day_eating_nutrition(
                        day, foods, meals, days, exercise, fractions
                    )
                )
                print("---")
        if args.report in ("both", "shopping"):
            quantities = (
                shopping.calculate_shopping_quantities(selected, meals, exercise)
                if args.shopping_basis == "prepared"
                else shopping.calculate_eating_quantities(
                    selected, foods, meals, days, exercise, fractions
                )
            )
            print(f"Shopping List ({args.days} days, {args.shopping_basis} basis)")
            print(
                "Grams in each food's recorded raw/cooked state; no yield conversion."
            )
            grouped = {}
            for ingredient, quantity in quantities.items():
                grouped.setdefault(foods[ingredient]["category"], []).append(
                    (ingredient, quantity)
                )
            for category, entries in sorted(grouped.items()):
                print(f"\n{category.title()}")
                for ingredient, quantity in sorted(entries):
                    amount = f"{quantity:.2f}".rstrip("0").rstrip(".")
                    print(f"   {ingredient}: {amount} g")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
