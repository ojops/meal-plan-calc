"""Optional intake must reconcile across every report and repeating cycle."""

import json
from copy import deepcopy
from decimal import Decimal

import pytest

from meal_plan_calc.evaluation import day_contributions
from meal_plan_calc.main import DATA_DIR, main
from meal_plan_calc.nutrition import NUTRIENTS, calculate_day_eating_nutrition
from meal_plan_calc.planning import CATEGORIES_SPLIT, DAYS, EXERCISE_SPLIT
from meal_plan_calc.shopping import (
    calculate_eating_quantities,
    calculate_shopping_quantities,
)
from meal_plan_calc.validation import load_json


def test_selected_intake_and_shopping_reconcile_without_mutation():
    foods = load_json(DATA_DIR / "foods.json")
    meals = load_json(DATA_DIR / "meals.json")
    original = deepcopy(meals)
    assert foods["quinoa"]["state"] == foods["grains"]["state"] == "cooked"
    assert "electrolytes_powder" not in meals["run"]
    chosen = ["tuesday", "friday", "tuesday"]
    for day in DAYS:
        args = (day, foods, meals, DAYS, EXERCISE_SPLIT, CATEGORIES_SPLIT)
        baseline = calculate_day_eating_nutrition(*args)
        changed = calculate_day_eating_nutrition(*args, chosen)
        entries = day_contributions(*args, chosen)
        for nutrient in NUTRIENTS:
            expected = (
                Decimal(foods["electrolytes_powder"][nutrient]) * Decimal("0.06")
                if day in chosen
                else Decimal(0)
            )
            assert abs(changed[nutrient] - baseline[nutrient] - expected) < Decimal(
                "1e-20"
            )
            assert abs(
                sum(row["nutrients"][nutrient] for row in entries) - changed[nutrient]
            ) < Decimal("1e-20")
        powder = [row for row in entries if row["ingredient"] == "electrolytes_powder"]
        assert len(powder) == (1 if day in chosen else 0)
        if powder:
            assert powder[0]["quantity"] == 6
            assert powder[0]["nutrients"]["salt"] == Decimal("0.78")
            assert powder[0]["source"] == "extra_electrolytes"
    selected = DAYS[5:] + DAYS + DAYS[:5]  # two cycles, starting Saturday
    prepared = calculate_shopping_quantities(selected, meals, EXERCISE_SPLIT, chosen)
    eaten = calculate_eating_quantities(
        selected, foods, meals, DAYS, EXERCISE_SPLIT, CATEGORIES_SPLIT, chosen
    )
    assert prepared["electrolytes_powder"] == eaten["electrolytes_powder"] == 24
    assert "electrolytes_powder" not in calculate_shopping_quantities(
        selected, meals, EXERCISE_SPLIT
    )
    for ingredient in prepared:
        assert abs(prepared[ingredient] - eaten[ingredient]) < Decimal("1e-20")
    assert meals == original


@pytest.mark.parametrize("basis", ["prepared", "eaten"])
def test_cli_optional_powder_shopping(basis, capsys):
    args = ["--days", "14", "--report", "shopping", "--shopping-basis", basis]
    assert main(args) == 0
    assert "electrolytes_powder:" not in capsys.readouterr().out
    assert main(args + ["--electrolytes-day", "tuesday"]) == 0
    assert "electrolytes_powder: 12 g" in capsys.readouterr().out


def test_cli_targets_and_contributors_include_extra(capsys):
    args = [
        "--start-day",
        "tuesday",
        "--days",
        "1",
        "--report",
        "targets",
        "--targets",
        str(DATA_DIR / "targets.example.json"),
        "--contributors",
        "salt",
    ]
    assert main(args) == 0
    baseline = capsys.readouterr().out
    assert main(args + ["--electrolytes-day", "tuesday"]) == 0
    changed = capsys.readouterr().out
    before = next(line for line in baseline.splitlines() if line.startswith("salt |"))
    after = next(line for line in changed.splitlines() if line.startswith("salt |"))
    assert Decimal(after.split("|")[1].strip()) - Decimal(
        before.split("|")[1].strip()
    ) == Decimal("0.78")
    assert (
        "extra_electrolytes [extra_electrolytes] / electrolytes_powder: 0.78 g"
        in changed
    )
    assert "Exercise type: run" in changed


def test_custom_schedule_selection_and_cli_override(tmp_path, capsys):
    schedule = tmp_path / "schedule.json"
    schedule.write_text(
        json.dumps(
            {
                "days": ["monday", "tuesday"],
                "exercise_split": {"monday": "strength", "tuesday": "run"},
                "categories_split": {},
                "electrolytes_days": ["monday"],
            }
        )
    )
    args = [
        "--schedule",
        str(schedule),
        "--start-day",
        "tuesday",
        "--days",
        "3",
        "--report",
        "shopping",
    ]
    for extra, expected in [
        ([], "6 g"),
        (["--electrolytes-day", "tuesday"], "12 g"),
        (["--no-extra-electrolytes"], None),
    ]:
        assert main(args + extra) == 0
        output = capsys.readouterr().out
        if expected is None:
            assert "electrolytes_powder:" not in output
        else:
            assert f"electrolytes_powder: {expected}" in output


@pytest.mark.parametrize("selection", ["tuesday", ["typo"], [1], None])
def test_invalid_schedule_selection(selection, tmp_path, capsys):
    schedule = tmp_path / "schedule.json"
    schedule.write_text(
        json.dumps(
            {
                "days": DAYS,
                "exercise_split": EXERCISE_SPLIT,
                "categories_split": {},
                "electrolytes_days": selection,
            }
        )
    )
    with pytest.raises(SystemExit) as error:
        main(["--schedule", str(schedule)])
    assert error.value.code == 2
    assert (
        "electrolytes_days must be a list of schedule day names"
        in capsys.readouterr().err
    )


def test_missing_optional_meal_only_required_when_selected(tmp_path, capsys):
    meals = load_json(DATA_DIR / "meals.json")
    del meals["extra_electrolytes"]
    path = tmp_path / "meals.json"
    path.write_text(json.dumps(meals))
    assert main(["--meals", str(path), "--days", "1"]) == 0
    capsys.readouterr()
    with pytest.raises(SystemExit) as error:
        main(["--meals", str(path), "--electrolytes-day", "tuesday"])
    assert error.value.code == 2
    assert "require an extra_electrolytes meal" in capsys.readouterr().err
