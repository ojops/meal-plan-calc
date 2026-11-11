"""Reproduce illustrative baseline, tighter-target and infeasible scenarios."""

import json
from copy import deepcopy

from meal_plan_calc.main import DATA_DIR
from meal_plan_calc.optimisation import optimise
from meal_plan_calc.planning import CATEGORIES_SPLIT, DAYS, EXERCISE_SPLIT
from meal_plan_calc.validation import load_json

foods = load_json(DATA_DIR / "foods.json")
meals = load_json(DATA_DIR / "meals.json")
profile = load_json(DATA_DIR / "profile.example.json")
preferences = load_json(DATA_DIR / "optimisation.example.json")
schedule = {
    "days": DAYS,
    "exercise_split": EXERCISE_SPLIT,
    "categories_split": CATEGORIES_SPLIT,
}
results = {}
for label in ("illustrative", "tighter_energy_range", "impossible_fruit_minimum"):
    personal, constraints = deepcopy(profile), deepcopy(preferences)
    if label == "tighter_energy_range":
        personal["default"]["calories"]["tolerance"] = "100"
        for values in personal["exercise"].values():
            values["calories"]["tolerance"] = "100"
    if label == "impossible_fruit_minimum":
        constraints["minimums"].append({"group": "fruit", "grams": "10000"})
    report = optimise(foods, meals, schedule, personal, constraints)
    results[label] = {
        k: report[k]
        for k in ("status", "objective_value", "changes", "message")
        if k in report
    }
print(json.dumps(results, indent=2, default=str))
