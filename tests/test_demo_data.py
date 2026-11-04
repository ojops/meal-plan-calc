"""Verify scenario isolation and the accounting represented in the film."""

from decimal import Decimal
from pathlib import Path

from meal_plan_calc.demo_data import build_demo
from meal_plan_calc.main import main

DATA = Path(__file__).resolve().parents[1] / "data"


def test_demo_scenario_isolated_and_has_expected_nutrient_deltas():
    source = (DATA / "meals.json").read_bytes()
    report = build_demo(DATA)
    assert (DATA / "meals.json").read_bytes() == source
    for day, original in report["daily"].items():
        changed = report["scenario"]["daily"][day]
        assert abs(
            changed["calories"] - original["calories"] - Decimal("93.5")
        ) < Decimal("1e-20")
        assert abs(
            changed["protein"] - original["protein"] - Decimal("2.75")
        ) < Decimal("1e-20")
    allocation = report["rice_allocation"]
    assert allocation["lunch_g"] + allocation["dinner_g"] == allocation["prepared_g"]
    assert allocation["lunch"]["calories"] == Decimal("452.8125")


def test_shopping_recording_conserves_full_cycles_and_scales_period():
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
