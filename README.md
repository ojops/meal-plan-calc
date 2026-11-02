# Meal Plan Calculator

A Python project for calculating daily nutritional intake and shopping quantities
from a meal plan, with the longer-term aim of adjusting food quantities to meet
nutrition targets with minimal excess.

## Overview

The calculator uses food composition data and meal quantities stored in JSON.
It accounts for a repeating cooking schedule and the allocation of prepared food
between lunch and dinner. Development is progressing from nutritional
calculations towards target comparisons and practical optimisation.

## Features

- Nutritional totals for individual meals and daily intake
- Tracking of calories, fat, saturates, carbohydrates, sugars, fibre, protein and salt
- Configurable food data, meal quantities and exercise schedule
- Shopping quantities for weekly, twice-weekly or fortnightly periods
- Separate reports for ingredients prepared or eaten during a period
- Input validation and automated calculation tests

Optimisation and nutrition targets are planned; neither is implemented yet.

## Requirements

- Python 3.10
- [uv](https://docs.astral.sh/uv/)

The following instructions assume Ubuntu or WSL running Ubuntu.

## Installation

Clone the repository and install its dependencies:

```bash
git clone https://github.com/ojops/meal-plan-calc.git
cd meal-plan-calc
uv sync --locked
```

## Usage

Run the calculator from the repository root:

```bash
uv run meal-plan-calc
```

By default, it prints daily nutrition and a shopping list for one week.
The module command also works: `uv run python -m meal_plan_calc`.

Choose a report and period without editing the source:

```bash
# Daily nutrition only
uv run meal-plan-calc --report nutrition

# A fortnight's shopping
uv run meal-plan-calc --days 14 --report shopping

# Two shopping periods: Monday–Wednesday and Thursday–Sunday
uv run meal-plan-calc --start-day monday --days 3 --report shopping
uv run meal-plan-calc --start-day thursday --days 4 --report shopping
```

Shopping defaults to ingredients prepared during the selected days. Use
`--shopping-basis eaten` for quantities consumed instead, including food from
earlier cooking days. Neither report accounts for existing stock or pack sizes.

Edit `data/foods.json` and `data/meals.json` to change the supplied plan.
Use `--foods`, `--meals` or `--schedule` to select alternate JSON files;
`uv run meal-plan-calc --help` lists all options.

## Calculation assumptions

Lunch uses the previous day's cooking and dinner uses cooking from two days
earlier, wrapping around the schedule. Category fractions define the lunch share;
dinner receives the remainder.

Nutrients are recorded per 100 g. Quantities use the food record's raw or cooked
state, with no conversion to purchase weights. Some supplement quantities appear
to be tablet or capsule counts but are displayed as grams; these units still need
to be resolved. Results depend on the accuracy of the supplied food data.

See [calculation notes](docs/CALCULATIONS.md) for allocation, units and custom
schedule details.

## Development Roadmap

- **Data and units:** Verify food sources and distinguish grams, tablet counts and purchase weights.
- **Nutrition targets:** Define daily targets and acceptable tolerances.
- **Comparisons:** Show how the current meal plan differs from those targets.
- **Optimisation:** Adjust ingredient quantities to reduce target deviations and unnecessary excess.
- **Constraints:** Support portion limits, food preferences and practical meal preparation.
- **Evaluation:** Compare proposed plans with the existing plan for accuracy and practicality.

## Project Structure

| Path | Purpose |
| --- | --- |
| `data/` | Food composition data and meal quantities |
| `src/meal_plan_calc/main.py` | Terminal arguments and report output |
| `src/meal_plan_calc/planning.py` | Schedule defaults and meal allocation |
| `src/meal_plan_calc/nutrition.py` | Nutritional calculations |
| `src/meal_plan_calc/shopping.py` | Prepared and eaten ingredient quantities |
| `src/meal_plan_calc/validation.py` | JSON loading and input checks |
| `tests/` | Automated tests |
| `docs/` | Calculation notes and coding conventions |
| `pyproject.toml`, `uv.lock` | Project configuration and locked dependencies |

## Development

Run the tests and code checks:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Add dependencies with `uv add package-name` and commit both `pyproject.toml`
and `uv.lock` when they change. GitHub Actions runs the checks on pushes and
pull requests. See [coding conventions](docs/STYLE.md).

## License

MIT licensed. See [LICENSE](LICENSE).
