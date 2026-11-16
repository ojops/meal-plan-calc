"""Summaries preserve units, residual gaps, and failure outcomes."""

import json
from copy import deepcopy
from decimal import Decimal as D

import pytest

from meal_plan_calc.proposal_summary import proposal_summary


def test_summary_retains_small_gaps_and_ranks_different_units_proportionally():
    targets = {
        "calories": {
            "value": D(2000),
            "tolerance": D(100),
            "mode": "aim",
            "hard": False,
        },
        "protein": {
            "value": D(100),
            "tolerance": D(0),
            "mode": "minimum",
            "hard": False,
        },
        "fat": {"value": D(80), "tolerance": D(0), "mode": "maximum", "hard": False},
        "salt": {"value": D(6), "tolerance": D(0), "mode": "maximum", "hard": True},
    }
    report = {
        "status": "optimal",
        "baseline_primary_objective_value": D(1),
        "primary_objective_value": D("0.2"),
        "changes": [
            {
                "source": "batch",
                "food": "rice",
                "before_g": D(100),
                "after_g": D(120),
                "delta_g": D(20),
            },
            {
                "source": "snack",
                "food": "oats",
                "before_g": D(100),
                "after_g": D(50),
                "delta_g": D(-50),
            },
        ],
        "days": {
            "monday": {
                "targets": targets,
                "proposed": {
                    "calories": D(2150),
                    "protein": D(90),
                    "fat": D("80.0001"),
                    "salt": D(6),
                },
                "target_deviations": {
                    name: {"outside_range": value}
                    for name, value in [
                        ("calories", D(50)),
                        ("protein", D(10)),
                        ("fat", D("0.0001")),
                        ("salt", D(0)),
                    ]
                },
            }
        },
        "shopping": {
            basis: {
                "rice": {
                    "before_g": D(100),
                    "after_g": D(120),
                    "delta_g": D(20),
                    "state": "cooked",
                }
            }
            for basis in ("prepared", "eaten")
        },
    }
    original = deepcopy(report)
    text = proposal_summary(report)
    assert text.index("snack / oats") < text.index("batch / rice")
    assert text.index("monday / protein") < text.index("monday / calories")
    assert "outside by 1.00E-4 g" in text
    assert "target at least 100.00 g" in text
    assert "target at most 80.00 g" in text
    assert "target 1900.00 to 2100.00 kcal" in text
    assert "Remaining soft target gaps: 3" in text
    assert (
        "rice [cooked]" in text
        and "prepared, full cycle" in text
        and "eaten, full cycle" in text
    )
    assert report == original
    assert proposal_summary(json.loads(json.dumps(report, default=str))) == text
    assert "... 2 more in the JSON report" in proposal_summary(report, limit=1)


@pytest.mark.parametrize("status", ["infeasible", "limit_reached", "solver_failure"])
def test_failed_solve_never_displays_proposed_portions(status):
    text = proposal_summary(
        {"status": status, "message": "Stopped", "guidance": "Check inputs."}
    )
    assert "No accepted meal plan" in text
    assert "Stopped" in text and "Check inputs." in text
    assert "portion changes" not in text
