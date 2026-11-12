"""Small, fully synthetic examples of fit priority and infeasibility; no file writes."""

import json
from copy import deepcopy

from meal_plan_calc.nutrition import NUTRIENTS
from meal_plan_calc.optimisation import optimise


def main():
    # A synthetic food isolates the mathematics; this is not a proposed diet.
    food = dict.fromkeys(NUTRIENTS, "0")
    food.update(category="carb", calories="400", protein="25", fat="10", carbs="52.5")
    foods = {"example_food": food}
    meals = {
        "a": {"example_food": "25"},
        "b": {"example_food": "25"},
        "snack": {},
        "breakfast": {},
        "rest": {},
        "supplements": {},
    }
    schedule = {
        "days": ["a", "b"],
        "exercise_split": {"a": "rest", "b": "rest"},
        "categories_split": {"carb": "0.5"},
    }
    profile = {
        "schema_version": 2,
        "weight_kg": "50",
        "default": {
            "protein_g_per_kg": "0.5",
            "fat_fraction": "0.225",
            "tolerance_fraction": "0.05",
        },
        "exercise": {"rest": {"calories": "400"}},
    }
    rules = {
        "adjustable": {"example_food": {"min_g": "10", "max_g": "200", "step_g": "10"}}
    }
    summary = {}
    for name in (
        "fit_before_baseline",
        "optional_useful_portion",
        "infeasible_hard_target",
    ):
        p, r = deepcopy(profile), deepcopy(rules)
        if name == "optional_useful_portion":
            r["adjustable"]["example_food"].update(required=False, min_g="150")
        if name == "infeasible_hard_target":
            p["hard_targets"] = ["calories"]
            r["adjustable"]["example_food"]["max_g"] = "20"
        result = optimise(foods, meals, schedule, p, r)
        summary[name] = {
            k: result[k]
            for k in (
                "status",
                "baseline_primary_objective_value",
                "primary_objective_value",
                "objective_value",
                "changes",
                "message",
            )
            if k in result
        }
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
