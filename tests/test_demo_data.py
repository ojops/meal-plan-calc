"""Verify dynamic scenarios, shopping invariants, and CLI agreement."""

import json
from decimal import Decimal
from pathlib import Path

from meal_plan_calc.demo_data import build_demo
from meal_plan_calc.main import main
from meal_plan_calc.validation import load_json

DATA = Path(__file__).resolve().parents[1] / "data"


def assert_scenario_consistent(report):
    scenario = report["scenario"]
    amount = scenario["after_g"] - scenario["before_g"]
    assert amount == Decimal("25")
    for day, original in report["daily"].items():
        changed = scenario["daily"][day]
        for nutrient in original:
            expected = (
                amount * Decimal(str(report["example"]["per_100g"][nutrient])) / 100
            )
            assert abs(changed[nutrient] - original[nutrient] - expected) < Decimal(
                "1e-20"
            )
    batch = report["batch_allocation"]
    assert batch["lunch_g"] + batch["dinner_g"] == batch["prepared_g"]


def test_demo_uses_current_values_without_modifying_inputs():
    original = (DATA / "meals.json").read_bytes()
    report = build_demo(DATA)
    assert (DATA / "meals.json").read_bytes() == original
    assert_scenario_consistent(report)
    meals = load_json(DATA / "meals.json")
    ingredient = report["scenario"]["ingredient"]
    assert report["scenario"]["before_g"] == Decimal(
        str(meals["breakfast"][ingredient])
    )


def test_changed_food_and_meal_values_update_demo(tmp_path):
    foods = load_json(DATA / "foods.json")
    meals = load_json(DATA / "meals.json")
    meals["breakfast"]["oats"] = "82"
    meals["monday"]["rice"] = "195"
    foods["oats"]["calories"] = "390"
    foods["oats"]["protein"] = "12"
    for name, value in (("foods.json", foods), ("meals.json", meals)):
        (tmp_path / name).write_text(json.dumps(value, default=str))
    report = build_demo(tmp_path)
    assert_scenario_consistent(report)
    assert report["scenario"]["before_g"] == Decimal("82")
    assert report["scenario"]["after_g"] == Decimal("107")
    assert report["scenario"]["monday_delta"]["calories"] == Decimal("97.5")
    assert report["scenario"]["monday_delta"]["protein"] == Decimal("3")
    assert report["batch_allocation"]["prepared_g"] == Decimal("195")
    assert report["batch_allocation"]["lunch_g"] == Decimal("146.25")


def test_other_ingredients_are_supported(tmp_path):
    foods = load_json(DATA / "foods.json")
    meals = load_json(DATA / "meals.json")
    meals["breakfast"].pop("oats")
    meals["monday"].pop("rice")
    for name, value in (("foods.json", foods), ("meals.json", meals)):
        (tmp_path / name).write_text(json.dumps(value, default=str))
    report = build_demo(tmp_path)
    assert report["scenario"]["ingredient"] != "oats"
    assert report["batch_allocation"]["prepared_day"] != "monday" or (
        report["batch_allocation"]["ingredient"] != "rice"
    )
    assert_scenario_consistent(report)


def test_shopping_conserves_full_cycles_and_scales():
    report = build_demo(DATA)
    for length in ("7", "14"):
        totals = report["shopping"][length]
        for ingredient, prepared in totals["prepared"].items():
            assert abs(prepared - totals["eaten"][ingredient]) < Decimal("1e-20")
    for ingredient, amount in report["shopping"]["7"]["prepared"].items():
        assert report["shopping"]["14"]["prepared"][ingredient] == amount * 2


def test_daily_recording_matches_displayed_cli(capsys):
    report = build_demo(DATA)
    assert main(["--days", "1", "--report", "nutrition"]) == 0
    output = capsys.readouterr().out
    for nutrient, value in report["daily"]["monday"].items():
        assert f"{nutrient}: {value:.2f}\n" in output
