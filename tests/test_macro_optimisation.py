"""Macro precedence, practical portions and lexicographic optimization behaviour."""

from copy import deepcopy
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from meal_plan_calc.macro_profile import resolve_macros


def profile():
    return {
        "schema_version": 2,
        "weight_kg": "50",
        "default": {
            "protein_g_per_kg": "0.5",
            "fat_fraction": "0.225",
            "tolerance_fraction": "0.05",
        },
        "exercise": {"rest": {"calories": "400"}},
    }


def test_macro_derivation_and_explicit_precedence():
    p = profile()
    p["default"]["macro_overrides"] = {"protein": "20"}
    p["exercise"]["rest"].update(
        protein_g_per_kg="9", macro_overrides={"protein": "30", "fat": "8"}
    )
    targets, hard, assumptions = resolve_macros(p, ["a"], {"a": "rest"})
    assert targets["a"]["protein"].value == 30
    assert targets["a"]["fat"].value == 8
    assert targets["a"]["carbs"].value == 52
    assert targets["a"]["calories"].value == 400
    assert targets["a"]["calories"].tolerance == 20
    assert not hard["a"]
    assert assumptions["rest"]["calories_include_exercise"] is True


def test_exercise_types_have_distinct_budgets_and_assumptions():
    p = profile()
    p["exercise"]["run"] = {
        "calories": "800",
        "protein_g_per_kg": "1",
        "fat_fraction": "0.25",
    }
    targets, _, _ = resolve_macros(p, ["a", "b"], {"a": "rest", "b": "run"})
    assert targets["a"]["protein"].value == 25
    assert targets["b"]["protein"].value == 50
    assert targets["b"]["carbs"].value == 100


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.update(weight_kg="0"),
        lambda p: p["exercise"]["rest"].update(calories="-1"),
        lambda p: p["default"].update(fat_fraction="1.1"),
        lambda p: p["default"].update(protein_g_per_kg="10"),
        lambda p: p["default"].update(macro_overrides={"carbs": "1000"}),
        lambda p: p["default"].update(tolerance_fraction="NaN"),
        lambda p: p.update(duration_hours={"a": "1"}),
        lambda p: p.update(
            hard_limits={"default": {"iron": {"value": "8", "mode": "minimum"}}}
        ),
    ],
)
def test_bad_profiles_rejected(change):
    p = profile()
    change(p)
    with pytest.raises(ValueError):
        resolve_macros(p, ["a"], {"a": "rest"})


@pytest.fixture
def problem():
    pytest.importorskip("scipy")
    from meal_plan_calc.nutrition import NUTRIENTS

    food = {k: "0" for k in NUTRIENTS}
    food.update(category="carb", calories="400", protein="25", fat="10", carbs="52.5")
    foods = {"rice": food}
    meals = {
        "a": {"rice": "25"},
        "b": {"rice": "25"},
        "snack": {},
        "breakfast": {},
        "supplements": {},
        "rest": {},
    }
    schedule = {
        "days": ["a", "b"],
        "exercise_split": {"a": "rest", "b": "rest"},
        "categories_split": {"carb": "0.5"},
    }
    rules = {"adjustable": {"rice": {"min_g": "10", "max_g": "200", "step_g": "10"}}}
    return foods, meals, schedule, profile(), rules


def test_fit_has_priority_over_baseline_and_increments_are_exact(problem):
    from meal_plan_calc.optimisation import optimise

    before = deepcopy(problem)
    result = optimise(*problem)
    assert problem == before
    assert result["status"] == "optimal"
    assert result["primary_objective_value"] <= D("0.0000011")
    assert result["objective_value"] == pytest.approx(D("2.8"))
    for day in ("a", "b"):
        assert result["proposed_meals"][day]["rice"] % 10 == 0
        assert result["days"][day]["proposed"]["calories"] == 380
    assert result["shopping"]["prepared"]["rice"]["delta_g"] == 140
    assert sum(x["consumed_change_g"] for x in result["batch_effects"]["a"]) == 70


def test_optional_food_can_be_zero_but_never_tiny(problem):
    from meal_plan_calc.optimisation import optimise

    problem[4]["adjustable"]["rice"].update(required=False, min_g="150")
    result = optimise(*problem)
    assert result["status"] == "optimal"
    portions = [result["proposed_meals"][day]["rice"] for day in ("a", "b")]
    assert 0 in portions
    assert all(x == 0 or 150 <= x <= 200 for x in portions)


def test_required_food_cannot_disappear_and_impossible_grid_is_infeasible(problem):
    from meal_plan_calc.optimisation import optimise

    problem[4]["adjustable"]["rice"].update(min_g="5", max_g="9", step_g="10")
    result = optimise(*problem)
    assert result["status"] == "infeasible"
    assert result["proposed_meals"] is None


def test_whole_units_and_explicit_exclusion(problem):
    from meal_plan_calc.optimisation import optimise

    spec = problem[4]["adjustable"]["rice"]
    spec.pop("step_g")
    spec.update(unit_g="70", unit_label="test unit")
    result = optimise(*problem)
    assert all(result["proposed_meals"][day]["rice"] % 70 == 0 for day in ("a", "b"))
    problem[4].clear()
    problem[4].update(adjustable={}, excluded=["rice"])
    result = optimise(*problem)
    assert result["status"] == "optimal"
    assert result["primary_objective_value"] > 0
    assert all(result["proposed_meals"][day]["rice"] == 0 for day in ("a", "b"))


def test_food_group_minimum_survives_soft_targets(problem):
    from meal_plan_calc.optimisation import optimise

    problem[4].update(
        groups={"grains": ["rice"]},
        minimums=[{"group": "grains", "grams": "180", "days": ["a"]}],
    )
    result = optimise(*problem)
    assert result["days"]["a"]["proposed"]["calories"] >= 720
    assert result["primary_objective_value"] > 0


def test_user_hard_macro_or_limit_cannot_be_relaxed(problem):
    from meal_plan_calc.optimisation import optimise

    problem[4]["adjustable"]["rice"]["max_g"] = "20"
    problem[3]["hard_targets"] = ["protein"]
    assert optimise(*problem)["status"] == "infeasible"
    problem[3]["hard_targets"] = []
    problem[3]["hard_limits"] = {
        "default": {"fibre": {"value": "5", "mode": "minimum"}}
    }
    assert optimise(*problem)["status"] == "infeasible"


def test_missing_nutrient_data_is_not_assumed_zero(problem):
    from meal_plan_calc.optimisation import optimise

    del problem[0]["rice"]["fibre"]
    with pytest.raises(ValueError, match="missing nutrient fibre"):
        optimise(*problem)


def test_optional_electrolytes_remain_selected_and_fixed(problem):
    from meal_plan_calc.optimisation import optimise

    problem[0]["powder"] = dict(problem[0]["rice"])
    problem[1]["extra_electrolytes"] = {"powder": "6"}
    problem[2]["electrolytes_days"] = ["a"]
    result = optimise(*problem)
    assert result["proposed_meals"]["extra_electrolytes"] == {"powder": "6"}
    assert result["shopping"]["prepared"]["powder"]["after_g"] == 6
    assert (
        result["days"]["a"]["proposed"]["calories"]
        - result["days"]["b"]["proposed"]["calories"]
        == 24
    )


def test_limit_does_not_export_incumbent(problem, monkeypatch):
    from meal_plan_calc.optimisation import optimise

    monkeypatch.setattr(
        "scipy.optimize.milp",
        lambda *a, **kw: SimpleNamespace(
            status=1,
            message="Time limit",
            fun=0.5,
            x=[0],
            mip_gap=0.2,
            mip_dual_bound=0.4,
        ),
    )
    result = optimise(*problem, time_limit=1)
    assert result["status"] == "limit_reached"
    assert result["proposed_meals"] is None
    assert result["solver_stages"]["target_fit"]["mip_gap"] == 0.2


def test_final_quantity_audit_rejects_false_solver_success(problem, monkeypatch):
    import scipy.optimize

    from meal_plan_calc.optimisation import optimise

    original = scipy.optimize.milp
    calls = []

    def bad_second(*a, **kw):
        result = original(*a, **kw)
        calls.append(1)
        if len(calls) == 2:
            result.x[0] += 0.3
        return result

    monkeypatch.setattr(scipy.optimize, "milp", bad_second)
    with pytest.raises(ValueError, match="nonintegral"):
        optimise(*problem)


def test_exclusion_cannot_override_a_hard_food_minimum(problem):
    from meal_plan_calc.optimisation import optimise

    problem[4].clear()
    problem[4].update(
        adjustable={}, excluded=["rice"], minimums=[{"food": "rice", "grams": "10"}]
    )
    result = optimise(*problem)
    assert result["status"] == "infeasible"
    assert result["proposed_meals"] is None


def test_macro_cli_uses_alias_exports_safely_and_preserves_every_input(
    problem, tmp_path
):
    import json

    from meal_plan_calc.optimise import main

    args = []
    for name, data in zip(
        ("foods", "meals", "schedule", "profile", "portion-rules"), problem
    ):
        path = tmp_path / (name + ".json")
        path.write_text(json.dumps(data))
        args.extend(["--" + name, str(path)])
    snapshots = {p: p.read_bytes() for p in tmp_path.iterdir()}
    report, export = tmp_path / "report.json", tmp_path / "proposed.json"
    assert main(args + ["--output", str(report), "--export-meals", str(export)]) == 0
    assert all(p.read_bytes() == original for p, original in snapshots.items())
    saved = report.read_bytes(), export.read_bytes()
    for destination in snapshots:
        with pytest.raises(SystemExit):
            main(args + ["--output", str(destination)])
    with pytest.raises(SystemExit):
        main(
            args
            + ["--output", str(tmp_path / "unused.json"), "--export-meals", str(export)]
        )
    assert not (tmp_path / "unused.json").exists()
    assert (report.read_bytes(), export.read_bytes()) == saved


def test_infeasible_cli_writes_diagnostic_but_no_meals(problem, tmp_path):
    import json

    from meal_plan_calc.optimise import main

    problem[3]["hard_targets"] = ["calories"]
    problem[4]["adjustable"]["rice"]["max_g"] = "20"
    args = []
    for name, data in zip(
        ("foods", "meals", "schedule", "profile", "portion-rules"), problem
    ):
        path = tmp_path / (name + ".json")
        path.write_text(json.dumps(data))
        args.extend(["--" + name, str(path)])
    report, export = tmp_path / "diagnostic.json", tmp_path / "not-written.json"
    assert main(args + ["--output", str(report), "--export-meals", str(export)]) == 1
    assert json.loads(report.read_text())["status"] == "infeasible"
    assert not export.exists()


def test_excluding_an_absent_known_food_is_harmless(problem):
    from meal_plan_calc.optimisation import optimise

    problem[0]["absent"] = dict(problem[0]["rice"])
    problem[4]["excluded"] = ["absent"]
    assert optimise(*problem)["status"] == "optimal"
    problem[4]["adjustable"] = {}
    result = optimise(*problem)
    assert result["status"] == "optimal"
    assert result["changes"] == []
    assert (
        result["primary_objective_value"] == result["baseline_primary_objective_value"]
    )
