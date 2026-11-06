"""Build reproducible presentation data from the current validated meal plan."""

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
    """Recalculate an isolated +25 g breakfast scenario using current inputs."""
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

    ingredient = "oats" if "oats" in meals["breakfast"] else next(
        iter(meals["breakfast"]), None
    )
    if ingredient is None:
        raise ValueError("The demonstration requires a nonempty breakfast")
    before = Decimal(str(meals["breakfast"][ingredient]))
    after = before + Decimal("25")
    altered = deepcopy(meals)
    altered["breakfast"][ingredient] = after
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

    day = "monday"
    if "rice" in meals[day]:
        batch_ingredient = "rice"
    else:
        candidates = [
            (candidate_day, name)
            for candidate_day in DAYS
            for name in meals[candidate_day]
            if foods[name]["category"] == "carb"
        ]
        if not candidates:
            raise ValueError("The demonstration needs a prepared carbohydrate")
        day, batch_ingredient = candidates[0]
    category = foods[batch_ingredient]["category"]
    fraction = CATEGORIES_SPLIT.get(category, Decimal(1))
    quantity = Decimal(str(meals[day][batch_ingredient]))
    batch = {batch_ingredient: quantity}
    day_index = DAYS.index(day)
    prepared_week = shopping["7"]["prepared"]
    preferred = ("oats", "rice", "chicken", "broccoli")
    displayed = [name for name in preferred if name in prepared_week]
    displayed.extend(name for name in prepared_week if name not in displayed)

    return {
        "input_sha256": {
            name: hashlib.sha256((data_dir / name).read_bytes()).hexdigest()
            for name in ("foods.json", "meals.json")
        },
        "days": DAYS,
        "daily": baseline,
        "scenario": {
            "ingredient": ingredient,
            "before_g": before,
            "after_g": after,
            "daily": scenario,
            "monday_delta": {
                key: scenario["monday"][key] - value
                for key, value in baseline["monday"].items()
            },
        },
        "example": {
            "per_100g": foods[ingredient],
            "breakfast_contribution": calculate_meal_nutrition(
                {ingredient: before}, foods
            ),
        },
        "batch_allocation": {
            "ingredient": batch_ingredient,
            "prepared_day": day,
            "lunch_day": DAYS[(day_index + 1) % len(DAYS)],
            "dinner_day": DAYS[(day_index + 2) % len(DAYS)],
            "prepared_g": quantity,
            "lunch_fraction": fraction,
            "lunch_g": quantity * fraction,
            "dinner_g": quantity * (1 - fraction),
            "lunch": calculate_meal_nutrition(batch, foods, {category: fraction}),
            "dinner": calculate_meal_nutrition(
                batch, foods, {category: 1 - fraction}
            ),
        },
        "shopping": shopping,
        "display_ingredients": displayed[:4],
        "units": {name: foods[name].get("state", "unspecified") for name in foods},
        "note": "Current records; supplement units unverified; no yield or pack conversion.",
    }
