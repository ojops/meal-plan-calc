# Meal Plan Calculator

Calculate daily nutrition and shopping quantities from a configurable, repeating meal plan.

[![Eight-second preview of calculated daily nutrition](docs/media/preview.gif)](https://raw.githubusercontent.com/ojops/meal-plan-calc/45d36fb767beec954759e319df599bb409524fab/docs/media/demo.mp4)

*Preview: nutrition calculated from the supplied data. [Watch the full 36-second demonstration (MP4)](https://raw.githubusercontent.com/ojops/meal-plan-calc/45d36fb767beec954759e319df599bb409524fab/docs/media/demo.mp4) · [How the video is made](docs/DEMO.md).*

## Features

- Calculate calories, fat, saturates, carbohydrates, sugars, fibre, protein and salt
- Configure foods, meals and exercise schedules using JSON
- Distribute cooked batches across subsequent lunches and dinners
- Report shopping quantities for arbitrary periods, based on food **prepared** or **eaten**
- Validate inputs and retain precision using Python `Decimal`

Nutrition targets and ingredient optimisation are **planned, not implemented**.

## Install

Requires Python 3.10 and [uv](https://docs.astral.sh/uv/). These commands target Ubuntu or WSL:

```bash
git clone https://github.com/ojops/meal-plan-calc.git
cd meal-plan-calc
uv sync --locked
```

## Run

```bash
uv run meal-plan-calc
uv run meal-plan-calc --report nutrition
uv run meal-plan-calc --days 14 --report shopping
uv run meal-plan-calc --start-day monday --days 3 --report shopping
uv run meal-plan-calc --start-day thursday --days 4 --report shopping
```

By default, the program reports daily nutrition and a week of **prepared** shopping. Add `--shopping-basis eaten` to count ingredients consumed, including portions cooked on earlier days.

Edit `data/foods.json` and `data/meals.json`, or specify alternative files with `--foods`, `--meals` and `--schedule`. See `uv run meal-plan-calc --help` for more options.

## Calculation assumptions

Lunch uses the previous day's batch; dinner uses the batch from two days earlier. Category fractions determine how much of each batch goes to each meal. Nutrients are listed per 100 g, and ingredient quantities retain each food's recorded **raw or cooked state**. No cooking-yield or purchase-pack conversion is performed; supplement units still need checking.

The main calculations are in `src/meal_plan_calc/nutrition.py`, `planning.py` and `shopping.py`. See [calculation notes](docs/CALCULATIONS.md) for formulas and schedule rules.

## Next steps

Verify input units and sources, introduce nutrition targets and deviations, then develop constrained ingredient optimisation.

## Development

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

GitHub Actions runs tests and formatting checks. See [coding conventions](docs/STYLE.md). [MIT licensed](LICENSE).
