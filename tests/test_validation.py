import json
from decimal import Decimal

import pytest

from meal_plan_calc import nutrition, shopping
from meal_plan_calc.main import DATA_DIR, main
from meal_plan_calc.planning import CATEGORIES_SPLIT, DAYS, EXERCISE_SPLIT
from meal_plan_calc.validation import load_json, validate_data


def test_unspecified_category_is_not_double_counted():
    foods = {"rice": {"category": "carb", **{k: "100" for k in nutrition.NUTRIENTS}}}
    meals = {"monday": {"rice": "100"}}
    lunch = nutrition.calculate_cooking_nutrition("monday", foods, meals, {}, "lunch")
    dinner = nutrition.calculate_cooking_nutrition("monday", foods, meals, {}, "dinner")
    assert lunch["calories"] + dinner["calories"] == Decimal(100)


@pytest.mark.parametrize("value", ["-1", "NaN", "Infinity", True, "not a number"])
def test_invalid_quantities_are_rejected(value):
    food = {"rice": {"category": "carb", **{k: "0" for k in nutrition.NUTRIENTS}}}
    with pytest.raises(ValueError):
        nutrition.calculate_meal_nutrition({"rice": value}, food)


@pytest.mark.parametrize("fraction", ["-0.1", "1.1", "NaN"])
def test_invalid_allocations_rejected(fraction):
    foods = {"rice": {"category": "carb", **{k: "0" for k in nutrition.NUTRIENTS}}}
    with pytest.raises(ValueError):
        nutrition.calculate_cooking_nutrition(
            "monday", foods, {"monday": {"rice": 1}}, {"carb": fraction}, "lunch"
        )


def test_duplicate_keys_and_missing_nutrients_are_not_silent(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"rice": 1, "rice": 2}')
    with pytest.raises(ValueError, match="Duplicate"):
        load_json(path)
    with pytest.raises(ValueError, match="missing nutrient"):
        validate_data({"rice": {"category": "carb"}}, {})


def test_weekly_mass_and_nutrient_conservation():
    foods, meals = (
        load_json(DATA_DIR / "foods.json"),
        load_json(DATA_DIR / "meals.json"),
    )
    validate_data(foods, meals)
    prepared = shopping.calculate_shopping_quantities(DAYS, meals, EXERCISE_SPLIT)
    eaten = shopping.calculate_eating_quantities(
        DAYS, foods, meals, DAYS, EXERCISE_SPLIT, CATEGORIES_SPLIT
    )
    assert prepared.keys() == eaten.keys()
    for ingredient in prepared:
        assert abs(prepared[ingredient] - eaten[ingredient]) < Decimal("1e-20")
    total = nutrition.empty_nutrition_totals()
    for day in DAYS:
        daily = nutrition.calculate_day_eating_nutrition(
            day, foods, meals, DAYS, EXERCISE_SPLIT, CATEGORIES_SPLIT
        )
        for nutrient in total:
            total[nutrient] += daily[nutrient]
    expected = nutrition.calculate_meal_nutrition(prepared, foods)
    for nutrient in total:
        assert abs(total[nutrient] - expected[nutrient]) < Decimal("1e-20")


def test_partial_period_has_distinct_prepared_and_eaten_quantities():
    foods, meals = (
        load_json(DATA_DIR / "foods.json"),
        load_json(DATA_DIR / "meals.json"),
    )
    prepared = shopping.calculate_shopping_quantities([DAYS[0]], meals, EXERCISE_SPLIT)
    eaten = shopping.calculate_eating_quantities(
        [DAYS[0]], foods, meals, DAYS, EXERCISE_SPLIT, CATEGORIES_SPLIT
    )
    assert prepared != eaten  # Monday consumption includes Saturday/Sunday batches.


def test_fortnight_cli_and_custom_schedule(tmp_path, capsys):
    schedule = tmp_path / "schedule.json"
    schedule.write_text(
        json.dumps(
            {
                "days": DAYS,
                "exercise_split": EXERCISE_SPLIT,
                "categories_split": {"carb": "0.5"},
            }
        )
    )
    assert (
        main(
            [
                "--days",
                "14",
                "--start-day",
                "sunday",
                "--report",
                "shopping",
                "--schedule",
                str(schedule),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "14 days, prepared" in output and "oats: 1050 g" in output
