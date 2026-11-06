# Meal Plan Calculator

A Python project for nutritional calculations and shopping quantities from a configurable, repeating meal plan.

[![Eight-second looping preview of calculated weekly nutrition](docs/media/preview.gif)](https://raw.githubusercontent.com/ojops/meal-plan-calc/45d36fb767beec954759e319df599bb409524fab/docs/media/demo.mp4)

*Eight-second preview. [Watch the full 36-second demonstration (MP4)](https://raw.githubusercontent.com/ojops/meal-plan-calc/45d36fb767beec954759e319df599bb409524fab/docs/media/demo.mp4) · [Regenerate with current data](docs/DEMO.md).*

## Features

- Calculate calories, fat, saturates, carbohydrates, sugars, fibre, protein and salt
- Configure food data, daily meals and exercise schedules in JSON
- Allocate prepared meals between subsequent lunches and dinners
- Generate 3-, 7- and 14-day ingredient totals on a **prepared** or **eaten** basis
- Validate inputs and calculate with Python `Decimal` arithmetic

Nutritional targets and meal-plan **optimisation are planned, not implemented**.

## Requirements and installation

Python 3.10 and [uv](https://docs.astral.sh/uv/); commands below target Ubuntu/WSL.

```bash
git clone https://github.com/ojops/meal-plan-calc.git
cd meal-plan-calc
uv sync --locked
```

## Usage

```bash
uv run meal-plan-calc
uv run meal-plan-calc --report nutrition
uv run meal-plan-calc --days 14 --report shopping
uv run meal-plan-calc --start-day monday --days 3 --report shopping
uv run meal-plan-calc --start-day thursday --days 4 --report shopping
```

The default reports a week of nutrition and prepared shopping. Use `--shopping-basis eaten` to count consumption, including earlier batches. Edit `data/foods.json` and `data/meals.json`, or supply alternatives with `--foods`, `--meals` and `--schedule`. See `uv run meal-plan-calc --help`.

## Calculation assumptions

Lunch uses yesterday's batch; dinner uses the batch from two days earlier. Category-specific fractions determine the split. Nutrients are specified per 100 g in the recorded **raw or cooked state**, without yield or purchase-pack conversion. Supplement tablet/capsule units need verification.

The core calculation lives in `src/meal_plan_calc/nutrition.py`, `planning.py` and `shopping.py`. See [calculation notes](docs/CALCULATIONS.md) for formulas and limitations.

## Roadmap

Verify ingredient units and sources, introduce nutritional targets and deviations, then implement constrained optimisation.

## Development

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

GitHub Actions runs automated checks. See [coding conventions](docs/STYLE.md). Licensed under [MIT](LICENSE).
