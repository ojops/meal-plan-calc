import argparse
from decimal import Decimal
from pathlib import Path

from meal_plan_calc import nutrition, shopping
from meal_plan_calc.evaluation import day_contributions
from meal_plan_calc.planning import CATEGORIES_SPLIT, DAYS, EXERCISE_SPLIT
from meal_plan_calc.targets import Target, compare, load_targets
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


def print_targets(totals: dict[str, Decimal], targets: dict[str, Target]) -> None:
    """Display signed and absolute differences separately from goal satisfaction."""
    print("User targets (kcal for calories, g otherwise; not dietary advice)")
    print(
        "nutrient | actual | target (mode; tolerance) | deviation | absolute | % | status"
    )
    for nutrient in nutrition.NUTRIENTS:
        if nutrient not in targets:
            continue
        target = targets[nutrient]
        result = compare(totals[nutrient], target)
        percent = (
            f"{result.percentage_deviation:+.2f}%"
            if result.percentage_deviation is not None
            else "n/a (zero target)"
        )
        print(
            f"{nutrient} | {result.actual:.2f} | {target.value:.2f} "
            f"({target.mode}; {target.tolerance:.2f}) | {result.deviation:+.2f} | "
            f"{result.absolute_deviation:.2f} | {percent} | {result.status}"
        )


def print_contributors(entries: list[dict], nutrient: str, total: Decimal) -> None:
    """Show the five largest consumed contributions, including batch provenance."""
    unit = "kcal" if nutrient == "calories" else "g"
    print(f"Largest {nutrient} contributions (up to 5; consumed portions)")
    for entry in sorted(
        entries, key=lambda row: row["nutrients"][nutrient], reverse=True
    )[:5]:
        value = entry["nutrients"][nutrient]
        share = f"{value / total * 100:.2f}%" if total else "n/a"
        print(
            f"  {entry['meal']} [{entry['source']}] / {entry['ingredient']}: "
            f"{value:.2f} {unit} ({share} of day); "
            f"{entry['quantity']:.2f} g, state={entry['state']}"
        )


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
    electrolytes = parser.add_mutually_exclusive_group()
    electrolytes.add_argument(
        "--electrolytes-day",
        action="append",
        metavar="DAY",
        help="Include extra_electrolytes on this schedule day; repeat for more days. "
        "Replaces schedule electrolytes_days when supplied.",
    )
    electrolytes.add_argument(
        "--no-extra-electrolytes",
        action="store_true",
        help="Disable scheduled extra electrolytes for this report",
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Number of consecutive days"
    )
    parser.add_argument(
        "--report", choices=("both", "nutrition", "shopping", "targets"), default="both"
    )
    parser.add_argument(
        "--shopping-basis", choices=("prepared", "eaten"), default="prepared"
    )
    parser.add_argument(
        "--targets", type=Path, help="Optional JSON nutrient goals by exercise type"
    )
    parser.add_argument(
        "--contributors",
        choices=nutrition.NUTRIENTS,
        help="Show the largest consumed ingredient contributions",
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
        electrolytes_days = schedule.get("electrolytes_days", [])
        if args.no_extra_electrolytes:
            electrolytes_days = []
        elif args.electrolytes_day is not None:
            electrolytes_days = args.electrolytes_day
        if not isinstance(electrolytes_days, list) or any(
            not isinstance(day, str) or day not in days for day in electrolytes_days
        ):
            raise ValueError("electrolytes_days must be a list of schedule day names")
        if electrolytes_days and "extra_electrolytes" not in meals:
            raise ValueError(
                "Selected electrolytes days require an extra_electrolytes meal"
            )
        if args.report == "targets" and args.targets is None:
            raise ValueError("--report targets requires --targets")
        if args.report == "shopping" and (args.targets or args.contributors):
            raise ValueError(
                "Use --report nutrition, targets or both for target/contributor reports"
            )
        targets = (
            load_targets(args.targets, {exercise[day] for day in days})
            if args.targets
            else None
        )
        if args.report in ("both", "nutrition", "targets"):
            for day in selected:
                print(day.upper())
                totals = nutrition.calculate_day_eating_nutrition(
                    day, foods, meals, days, exercise, fractions, electrolytes_days
                )
                if args.report != "targets":
                    print_nutrition(totals)
                if targets is not None:
                    print(f"Exercise type: {exercise[day]}")
                    print_targets(totals, targets[exercise[day]])
                if args.contributors:
                    print_contributors(
                        day_contributions(
                            day,
                            foods,
                            meals,
                            days,
                            exercise,
                            fractions,
                            electrolytes_days,
                        ),
                        args.contributors,
                        totals[args.contributors],
                    )
                print("---")
        if args.report in ("both", "shopping"):
            quantities = (
                shopping.calculate_shopping_quantities(
                    selected, meals, exercise, electrolytes_days
                )
                if args.shopping_basis == "prepared"
                else shopping.calculate_eating_quantities(
                    selected, foods, meals, days, exercise, fractions, electrolytes_days
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
