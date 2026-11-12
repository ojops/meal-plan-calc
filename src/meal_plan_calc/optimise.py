"""Create a separate proposed plan; never update an existing file."""

import argparse
import hashlib
import json
from pathlib import Path

from meal_plan_calc.main import DATA_DIR
from meal_plan_calc.optimisation import optimise
from meal_plan_calc.planning import CATEGORIES_SPLIT, DAYS, EXERCISE_SPLIT
from meal_plan_calc.validation import load_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--foods", type=Path, default=DATA_DIR / "foods.json")
    parser.add_argument("--meals", type=Path, default=DATA_DIR / "meals.json")
    parser.add_argument("--schedule", type=Path)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument(
        "--portion-rules",
        "--preferences",
        dest="preferences",
        type=Path,
        required=True,
        help="Editable portion bounds, increments, exclusions and daily food/group minimums",
    )
    parser.add_argument(
        "--time-limit",
        type=float,
        default=60.0,
        help="Maximum solver seconds per stage; no incumbent exported on a limit",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--export-meals",
        type=Path,
        help="Optional new meals JSON for existing reporting commands",
    )
    args = parser.parse_args(argv)
    try:
        outputs = [p for p in (args.output, args.export_meals) if p is not None]
        if len({p.resolve() for p in outputs}) != len(outputs) or any(
            p.exists() for p in outputs
        ):
            raise ValueError(
                "Output paths must be distinct new files; existing files are never overwritten"
            )
        schedule = (
            load_json(args.schedule)
            if args.schedule
            else {
                "days": DAYS,
                "exercise_split": EXERCISE_SPLIT,
                "categories_split": CATEGORIES_SPLIT,
            }
        )
        report = optimise(
            load_json(args.foods),
            load_json(args.meals),
            schedule,
            load_json(args.profile),
            load_json(args.preferences),
            time_limit=args.time_limit,
        )
        report["input_sha256"] = {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in (
                ("foods", args.foods),
                ("meals", args.meals),
                ("profile", args.profile),
                ("preferences", args.preferences),
                ("schedule", args.schedule),
            )
            if path is not None
        }
        report["schedule"] = schedule
        import scipy

        report["solver"] = {
            "name": "scipy.optimize.milp/HiGHS",
            "scipy_version": scipy.__version__,
        }
        for path, value in [(args.output, report)] + (
            [(args.export_meals, report["proposed_meals"])]
            if args.export_meals and report["status"] == "optimal"
            else []
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as handle:
                json.dump(value, handle, indent=2, default=str, allow_nan=False)
                handle.write("\n")
        print(f"{report['status']}: {args.output}")
        if report["status"] == "optimal":
            print(
                f"Target-range deviation: {report['primary_objective_value']}; baseline change: {report['objective_value']}"
            )
            if report["primary_objective_value"] > 0.000001:
                print("Some soft target ranges remain unmet; inspect the report.")
        return 0 if report["status"] == "optimal" else 1
    except ImportError:
        parser.error(
            "Install the optional optimiser with: uv sync --locked --extra optimise"
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
