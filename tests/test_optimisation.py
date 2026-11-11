"""Analytic LP examples, shared-batch consistency and non-destructive output."""

import copy
import json
from decimal import Decimal as D

import pytest

pytest.importorskip("scipy")

from meal_plan_calc.nutrition import NUTRIENTS
from meal_plan_calc.optimisation import optimise, profile_targets
from meal_plan_calc.optimise import main


@pytest.fixture
def problem():
    food = {k: "0" for k in NUTRIENTS}
    food.update(category="carb", calories="100", protein="10")
    foods = {"rice": food}
    meals = {
        "a": {"rice": "100"},
        "b": {"rice": "100"},
        "breakfast": {},
        "snack": {},
        "supplements": {},
        "rest": {},
    }
    schedule = {
        "days": ["a", "b"],
        "exercise_split": {"a": "rest", "b": "rest"},
        "categories_split": {"carb": "0.5"},
    }
    profile = {"weight_kg": "50", "default": {"calories": {"per_kg": "4"}}}
    preferences = {"adjustable": {"rice": {"min_g": "0", "max_g": "400"}}}
    return foods, meals, schedule, profile, preferences


def test_exact_target_with_shared_batches_and_no_mutation(problem):
    before = copy.deepcopy(problem)
    report = optimise(*problem)
    assert problem == before
    assert report["status"] == "optimal"
    assert report["objective_value"] == pytest.approx(D(2))
    for day in ("a", "b"):
        assert report["days"][day]["proposed"]["calories"] == pytest.approx(D(200))
    # Only sum of batch sizes is identified here: do not demand an arbitrary LP tie-break.
    assert sum(
        report["proposed_meals"][day]["rice"] for day in ("a", "b")
    ) == pytest.approx(D(400))


def test_feasible_baseline_is_unchanged(problem):
    problem[3]["default"]["calories"] = {"base": "100"}
    report = optimise(*problem)
    assert report["changes"] == []
    assert report["objective_value"] == 0


def test_group_minimum_and_food_minimum_are_consumed_not_prepared(problem):
    problem[3]["default"]["calories"] = {"base": "500", "mode": "maximum"}
    problem[4].update(
        groups={"grains": ["rice"]},
        minimums=[
            {"group": "grains", "grams": "150", "days": ["a"]},
            {"food": "rice", "grams": "160", "days": ["b"]},
        ],
    )
    report = optimise(*problem)
    for day in ("a", "b"):
        assert report["days"][day]["proposed"]["calories"] >= D("159.99999")


def test_infeasible_constraints_do_not_return_a_plan(problem):
    problem[4]["adjustable"]["rice"]["max_g"] = "150"
    assert optimise(*problem)["proposed_meals"] is None
    assert optimise(*problem)["status"] == "infeasible"


def test_unlisted_foods_are_fixed(problem):
    problem[0]["fixed"] = dict(problem[0]["rice"])
    problem[1]["breakfast"]["fixed"] = "10"
    assert optimise(*problem)["proposed_meals"]["breakfast"]["fixed"] == "10"


def test_exercise_and_duration_formula():
    profile = {
        "weight_kg": "70",
        "duration_hours": {"a": "1.5"},
        "default": {"protein": {"per_kg": "1.6", "mode": "minimum"}},
        "exercise": {
            "run": {"calories": {"base": "1000", "per_kg": "10", "per_hour": "300"}}
        },
    }
    targets = profile_targets(profile, ["a"], {"a": "run"})
    assert targets["a"]["calories"].value == 2150
    assert targets["a"]["protein"].value == 112
    profile["duration_hours"] = {}
    with pytest.raises(ValueError, match="duration_hours"):
        profile_targets(profile, ["a"], {"a": "run"})


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p[4].update(groups={"bad": ["rice", "rice"]}),
        lambda p: p[4]["adjustable"]["rice"].update(min_g="500"),
        lambda p: p[3].update(weight_kg="NaN"),
        lambda p: p[4].update(minimums=[{"food": "unknown", "grams": "1"}]),
    ],
)
def test_invalid_configuration_is_rejected(problem, change):
    change(problem)
    with pytest.raises(ValueError):
        optimise(*problem)


def test_cli_exports_separately_and_refuses_overwrite(problem, tmp_path):
    args = []
    for name, data in zip(
        ("foods", "meals", "schedule", "profile", "preferences"), problem
    ):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(data))
        args += ["--" + name, str(path)]
    inputs = {p: p.read_bytes() for p in tmp_path.iterdir()}
    output, exported = tmp_path / "report.json", tmp_path / "proposed.json"
    assert main(args + ["--output", str(output), "--export-meals", str(exported)]) == 0
    assert exported.exists()
    assert all(p.read_bytes() == content for p, content in inputs.items())
    saved = output.read_bytes()
    with pytest.raises(SystemExit):
        main(args + ["--output", str(output)])
    assert output.read_bytes() == saved
    with pytest.raises(SystemExit):
        main(args + ["--output", str(tmp_path / "meals.json")])
    assert all(p.read_bytes() == content for p, content in inputs.items())
