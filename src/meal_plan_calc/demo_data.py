"""Build presentation data by calling the existing Decimal-based calculator."""

import hashlib
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

from meal_plan_calc.nutrition import (
    calculate_day_eating_nutrition,
    calculate_meal_nutrition,
)
from meal_plan_calc.planning import CATEGORIES_SPLIT, DAYS, EXERCISE_SPLIT
from meal_plan_calc.shopping import (
    calculate_eating_quantities,
    calculate_shopping_quantities,
)
from meal_plan_calc.validation import load_json, validate_data


def build_demo(data_dir: Path) -> dict:
    """Calculate the supplied week and an isolated 75 g to 100 g oats scenario.

    Preserve Decimal values until JSON serialization; never edit the source plan.
    Shopping quantities retain each food's recorded raw/cooked state.
    """
    foods = load_json(data_dir / "foods.json")
    meals = load_json(data_dir / "meals.json")
    validate_data(foods, meals)

    def week(plan):
        return {
            day: calculate_day_eating_nutrition(
                day, foods, plan, DAYS, EXERCISE_SPLIT, CATEGORIES_SPLIT
            )
            for day in DAYS
        }

    altered = deepcopy(meals)
    altered["breakfast"]["oats"] = Decimal("100")
    validate_data(foods, altered)
    baseline, scenario = week(meals), week(altered)
    shopping = {}
    for length in (3, 7, 14):
        selected = [DAYS[i % len(DAYS)] for i in range(length)]
        shopping[str(length)] = {
            "prepared": calculate_shopping_quantities(selected, meals, EXERCISE_SPLIT),
            "eaten": calculate_eating_quantities(
                selected, foods, meals, DAYS, EXERCISE_SPLIT, CATEGORIES_SPLIT
            ),
        }

    rice = {"rice": meals["monday"]["rice"]}
    return {
        "input_sha256": {
            name: hashlib.sha256((data_dir / name).read_bytes()).hexdigest()
            for name in ("foods.json", "meals.json")
        },
        "days": DAYS,
        "daily": baseline,
        "scenario": {
            "ingredient": "oats",
            "before_g": Decimal(str(meals["breakfast"]["oats"])),
            "after_g": Decimal("100"),
            "daily": scenario,
            "monday_delta": {
                key: scenario["monday"][key] - value
                for key, value in baseline["monday"].items()
            },
        },
        "oats": {
            "per_100g": foods["oats"],
            "breakfast_contribution": calculate_meal_nutrition(
                {"oats": meals["breakfast"]["oats"]}, foods
            ),
        },
        "rice_allocation": {
            "prepared_g": Decimal(str(rice["rice"])),
            "lunch_fraction": CATEGORIES_SPLIT["carb"],
            "lunch_g": Decimal(str(rice["rice"])) * CATEGORIES_SPLIT["carb"],
            "dinner_g": Decimal(str(rice["rice"])) * (1 - CATEGORIES_SPLIT["carb"]),
            "lunch": calculate_meal_nutrition(
                rice, foods, {"carb": CATEGORIES_SPLIT["carb"]}
            ),
            "dinner": calculate_meal_nutrition(
                rice, foods, {"carb": 1 - CATEGORIES_SPLIT["carb"]}
            ),
        },
        "shopping": shopping,
        "units": {name: foods[name].get("state", "unspecified") for name in foods},
        "note": "Recorded food data; supplement units unverified; no yield or pack conversion.",
    }
