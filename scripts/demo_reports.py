"""Record the walkthrough from the example inputs and production report functions."""

import hashlib
from dataclasses import asdict
from pathlib import Path

import scipy

from meal_plan_calc.demo_data import build_demo
from meal_plan_calc.evaluation import day_contributions
from meal_plan_calc.nutrition import calculate_day_eating_nutrition
from meal_plan_calc.optimisation import optimise
from meal_plan_calc.planning import CATEGORIES_SPLIT, DAYS, EXERCISE_SPLIT
from meal_plan_calc.proposal_summary import proposal_summary
from meal_plan_calc.targets import compare, load_targets
from meal_plan_calc.validation import load_json


def record_walkthrough(data_dir: Path) -> dict:
    data = build_demo(data_dir)
    foods = load_json(data_dir / "foods.json")
    meals = load_json(data_dir / "meals.json")
    targets_file = data_dir / "targets.example.json"
    profile_file = data_dir / "profile.macros.example.json"
    rules_file = data_dir / "portion-rules.example.json"
    for path in (targets_file, profile_file, rules_file):
        data["input_sha256"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()

    schedule = dict(
        days=DAYS, exercise_split=EXERCISE_SPLIT, categories_split=CATEGORIES_SPLIT
    )
    targets = load_targets(targets_file, set(EXERCISE_SPLIT.values()))
    data["monday_targets"] = {
        name: asdict(compare(data["daily"]["monday"][name], target))
        for name, target in targets[EXERCISE_SPLIT["monday"]].items()
    }
    entries = day_contributions("monday", foods, meals, **schedule)
    data["protein_contributors"] = sorted(
        entries, key=lambda e: e["nutrients"]["protein"], reverse=True
    )[:5]
    data["tuesday_powder"] = {
        "portion": meals["extra_electrolytes"],
        "default": data["daily"]["tuesday"],
        "selected": calculate_day_eating_nutrition(
            "tuesday", foods, meals, **schedule, electrolytes_days=["tuesday"]
        ),
    }

    profile, rules = load_json(profile_file), load_json(rules_file)
    proposal = optimise(foods, meals, schedule, profile, rules)
    if proposal["status"] != "optimal":
        raise RuntimeError(f"The example proposal ended with {proposal['status']}.")
    data["profile"] = profile
    data["rules"] = rules
    data["proposal"] = proposal
    data["proposal_summary"] = proposal_summary(proposal)
    data["solver_version"] = scipy.__version__
    return data
