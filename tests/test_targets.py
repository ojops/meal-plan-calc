"""Target semantics and contribution arithmetic independent of display rounding."""

import json
from decimal import Decimal

import pytest

from meal_plan_calc.evaluation import day_contributions
from meal_plan_calc.main import DATA_DIR, main
from meal_plan_calc.nutrition import NUTRIENTS, calculate_day_eating_nutrition
from meal_plan_calc.planning import CATEGORIES_SPLIT, DAYS, EXERCISE_SPLIT
from meal_plan_calc.targets import Target, compare, load_targets
from meal_plan_calc.validation import load_json


@pytest.mark.parametrize(
    "actual,mode,tolerance,status",
    [
        ("90", "aim", "10", "within range"),
        ("110", "aim", "10", "within range"),
        ("89.999", "aim", "10", "below range"),
        ("110.001", "aim", "10", "above range"),
        ("120", "minimum", "0", "met"),
        ("90", "minimum", "10", "met"),
        ("89", "minimum", "10", "below minimum"),
        ("80", "maximum", "0", "met"),
        ("111", "maximum", "10", "above maximum"),
    ],
)
def test_direction_and_inclusive_tolerance(actual, mode, tolerance, status):
    result = compare(Decimal(actual), Target(Decimal(100), mode, Decimal(tolerance)))
    assert result.status == status
    assert result.deviation == Decimal(actual) - 100
    assert result.absolute_deviation == abs(Decimal(actual) - 100)
    assert result.percentage_deviation == Decimal(actual) - 100


def test_percentage_uses_target_and_zero_target_is_explicit():
    result = compare(Decimal("0.3"), Target(Decimal("0.2")))
    assert result.deviation == Decimal("0.1")
    assert result.percentage_deviation == Decimal(50)
    zero = compare(Decimal(1), Target(Decimal(0), "maximum"))
    assert zero.percentage_deviation is None and zero.status == "above maximum"
    assert compare(Decimal(0), Target(Decimal(0))).status == "within range"


def test_exercise_overrides_replace_one_nutrient_and_preserve_defaults(tmp_path):
    path = tmp_path / "targets.json"
    path.write_text(
        json.dumps(
            {
                "default": {
                    "calories": {"value": "2000", "tolerance": "100"},
                    "protein": {"value": "100", "mode": "minimum"},
                },
                "exercise": {"run": {"calories": {"value": "2400"}}},
            }
        )
    )
    goals = load_targets(path, {"run", "rest"})
    assert goals["run"]["calories"] == Target(Decimal(2400))
    assert goals["rest"]["calories"].tolerance == 100
    assert goals["run"]["protein"] == goals["rest"]["protein"]
    assert "salt" not in goals["run"]


@pytest.mark.parametrize(
    "config",
    [
        {},
        {"defalt": {}},
        {"default": {"protien": {"value": 1}}},
        {"default": {"protein": {"value": True}}},
        {"default": {"protein": {"value": "NaN"}}},
        {"default": {"protein": {"value": -1}}},
        {"default": {"protein": {"value": 1, "tolerance": -1}}},
        {"default": {"protein": {"value": 1, "mode": "optimal"}}},
        {"default": {"protein": {"value": 1, "tolerence": 1}}},
        {"default": {"protein": 1}},
        {"exercise": {"run": {"protein": {"value": 1}}}},
        {"exercise": {"rest": {"protein": {"value": 1}}}},
    ],
)
def test_invalid_or_uncovered_targets_rejected(tmp_path, config):
    path = tmp_path / "targets.json"
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError):
        load_targets(path, {"rest"} if "run" in config.get("exercise", {}) else {"run"})


def test_contributors_use_consumed_batches_and_preserve_raw_cooked_states():
    foods = {
        "rice": {"category": "carb", "state": "cooked", **{n: "10" for n in NUTRIENTS}},
        "beans": {
            "category": "protein",
            "state": "raw",
            **{n: "20" for n in NUTRIENTS},
        },
    }
    meals = {
        "a": {"rice": 200, "beans": 100},
        "b": {"rice": 400, "beans": 200},
        "breakfast": {"rice": 50},
        "snack": {},
        "supplements": {},
        "rest": {},
    }
    kwargs = dict(
        day="a",
        foods=foods,
        meals=meals,
        days=["a", "b"],
        exercise_split={"a": "rest", "b": "rest"},
        categories_split={"carb": Decimal("0.75"), "protein": Decimal("0.5")},
    )
    entries = day_contributions(**kwargs)
    lunch_rice = next(
        row for row in entries if row["meal"] == "lunch" and row["ingredient"] == "rice"
    )
    assert lunch_rice["quantity"] == 300 and lunch_rice["source"] == "b"
    assert lunch_rice["nutrients"]["protein"] == 30
    assert lunch_rice["state"] == "cooked"
    assert all(row["state"] == "raw" for row in entries if row["ingredient"] == "beans")
    # 50 g breakfast rice + 300 g lunch rice + 50 g dinner rice = 40 g protein;
    # 100 g lunch beans + 50 g dinner beans = 30 g protein.
    assert sum(row["nutrients"]["protein"] for row in entries) == 70
    assert calculate_day_eating_nutrition(**kwargs)["protein"] == 70
    assert meals["b"]["rice"] == 400


def test_contributions_reconcile_every_supplied_day_and_nutrient():
    foods, meals = (
        load_json(DATA_DIR / "foods.json"),
        load_json(DATA_DIR / "meals.json"),
    )
    for day in DAYS:
        args = (day, foods, meals, DAYS, EXERCISE_SPLIT, CATEGORIES_SPLIT)
        entries = day_contributions(*args)
        totals = calculate_day_eating_nutrition(*args)
        for nutrient, total in totals.items():
            assert abs(
                sum(row["nutrients"][nutrient] for row in entries) - total
            ) < Decimal("1e-20")


def test_target_cli_repeats_schedule_and_shows_sources(capsys):
    assert (
        main(
            [
                "--report",
                "targets",
                "--targets",
                str(DATA_DIR / "targets.example.json"),
                "--start-day",
                "sunday",
                "--days",
                "8",
                "--contributors",
                "protein",
            ]
        )
        == 0
    )
    text = capsys.readouterr().out
    assert text.count("SUNDAY") == 2
    assert "2600.00 (aim; 100.00)" in text and "2400.00 (aim; 100.00)" in text
    assert "absolute" in text and "below minimum" not in text
    assert "lunch [sunday] / salmon" in text
    assert "Shopping List" not in text


def test_target_report_requires_configuration(capsys):
    with pytest.raises(SystemExit) as error:
        main(["--report", "targets"])
    assert error.value.code == 2
    assert "requires --targets" in capsys.readouterr().err
