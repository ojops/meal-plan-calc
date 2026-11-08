# Meal Plan Calculator

A Python command-line project for calculating daily nutrition and shopping quantities from a configurable, repeating meal plan.

[![Eight-second preview of calculated daily nutrition](docs/media/preview.gif)](https://raw.githubusercontent.com/ojops/meal-plan-calc/45d36fb767beec954759e319df599bb409524fab/docs/media/demo.mp4)

*Preview: historical meal-plan snapshot, including the formerly automatic electrolyte powder. [Watch the full 36-second demonstration (MP4)](https://raw.githubusercontent.com/ojops/meal-plan-calc/45d36fb767beec954759e319df599bb409524fab/docs/media/demo.mp4) · [How the video is made](docs/DEMO.md).*

## Overview

This project turns a structured meal plan into practical reports: what nutrients are consumed each day and which ingredients are needed over a chosen period. Its JSON-based food, meal and exercise schedules can be adjusted as a plan changes, while batch-cooking rules account for food prepared on one day and eaten later.

Optional nutritional targets turn those totals into daily comparisons, with exercise-specific goals, tolerances and signed/absolute deviations. Ingredient contribution reports help explain the current intake before proposing changes.

## Features

- Calculate calories, fat, saturates, carbohydrates, sugars, fibre, protein and salt
- Configure foods, meals and exercise schedules using JSON
- Include additional electrolyte powder only on explicitly selected days
- Distribute cooked batches across subsequent lunches and dinners
- Report shopping quantities for arbitrary periods, based on food **prepared** or **eaten**
- Evaluate optional energy and nutrient aims, minimums and maximums by exercise type
- Show absolute and percentage deviations, plus the largest consumed ingredient contributions
- Validate inputs and retain precision using Python `Decimal`

Targets are user-defined objectives, not universal dietary requirements. Ingredient optimisation is not implemented.

## Requirements and Installation

Requires Python 3.10 and [uv](https://docs.astral.sh/uv/). These commands target Ubuntu or WSL:

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

By default, the program reports daily nutrition and a week of **prepared** shopping. Add `--shopping-basis eaten` to count ingredients consumed, including portions cooked on earlier days.

Edit `data/foods.json` and `data/meals.json`, or specify alternative files with `--foods`, `--meals` and `--schedule`. See `uv run meal-plan-calc --help` for more options.

### Optional electrolyte powder

The supplied plan excludes additional electrolyte powder by default. Select the
days when you want the 6 g portion included:

```bash
uv run meal-plan-calc --electrolytes-day tuesday --electrolytes-day thursday
uv run meal-plan-calc --days 14 --report shopping --electrolytes-day tuesday
```

Each selected day gets one portion on every occurrence in the reporting period,
including across repeated weeks. Selection works on any schedule day and affects
nutrition, targets, contributions and both shopping bases together. The run-day
tablet remains part of the normal run meal.

For a saved preference, add `"electrolytes_days": ["tuesday", "thursday"]` to your
schedule JSON. CLI day selections replace that list; `--no-extra-electrolytes`
disables it for a report. Adjust the portion in `extra_electrolytes` in
`data/meals.json`. See [selection rules](docs/CALCULATIONS.md#optional-electrolyte-powder)
for custom files and migration from the old default.

### Nutritional targets and contributions

```bash
uv run meal-plan-calc --targets data/targets.example.json --report targets
uv run meal-plan-calc --targets data/targets.example.json --report nutrition --days 1 --contributors protein
```

The example numbers illustrate the file format; they are **not nutritional recommendations**. Supply your own targets. `default` goals apply to all exercise types; `exercise` overrides selected nutrients for types such as `run`. Each goal has a `value`, optional `mode` (`aim`, `minimum`, `maximum`) and absolute `tolerance`. Calories use kcal; other nutrients use grams.

Reports show actual intake, signed and absolute deviations, percentage deviation and whether the directional goal is met. Zero targets have an undefined percentage (`n/a`). Only configured nutrients are assessed. `--contributors nutrient` also works without targets and lists up to five consumed ingredient contributions, their meal, batch source and recorded state. See [target configuration and formulas](docs/CALCULATIONS.md#nutritional-targets) for details.

Existing commands work without a targets file. Targets and contributions are available with `nutrition`, `targets` or `both` reports; shopping calculations use the same plan and optional powder selection.

## Calculation Method and Limitations

Lunch uses the previous day's batch; dinner uses the batch from two days earlier. Category fractions determine how much of each batch goes to each meal. Nutrients are listed per 100 g, and ingredient quantities retain each food's recorded **raw or cooked state**. No cooking-yield or purchase-pack conversion is performed; supplement units still need checking.

Quinoa and grains are recorded as **cooked**: their quantities refer to the supplied cooked products. This label correction does not change per-100-g nutrient values or perform a weight conversion.

The main calculations are in `src/meal_plan_calc/nutrition.py`, `planning.py` and `shopping.py`. See [calculation notes](docs/CALCULATIONS.md) for formulas and schedule rules.

## Development Roadmap

Development is focused on moving from calculating what a meal plan provides to evaluating it against useful nutritional objectives, while preserving reliable shopping calculations.

### Planned

- **Validate inputs:** audit nutrient sources, raw versus cooked weights and supplement units before interpreting target comparisons as a dietary assessment.
- **Compare proposed adjustments:** build on the implemented targets and contribution reports to compare explicit portion scenarios, including their shopping effects, without mutating the baseline.
- **Constrain future optimisation:** define user-selected portion bounds, preferences and treatment of competing goals before introducing an optimiser.
- **Improve shopping accuracy:** add optional cooking-yield and purchase-pack conversions while keeping prepared and eaten quantities distinct.

## Project Structure

```text
meal-plan-calc/
├── data/
│   ├── foods.json            # Ingredient nutrient records
│   ├── meals.json            # Meals and quantities
│   └── targets.example.json  # Illustrative user targets, optional
├── src/meal_plan_calc/
│   ├── nutrition.py          # Nutrient calculations
│   ├── planning.py           # Repeating schedule and allocations
│   ├── targets.py            # Target configuration and comparisons
│   ├── evaluation.py         # Consumed ingredient contributions
│   ├── shopping.py           # Prepared and eaten shopping quantities
│   ├── validation.py         # JSON and data validation
│   └── main.py               # Command-line reporting
├── scripts/                  # Portfolio video rendering
├── tests/                    # Nutrition, shopping and validation tests
├── docs/                     # Calculation and demo documentation
│   └── media/                # Preview GIF, MP4 and recorded data
├── pyproject.toml            # Project metadata and dependencies
├── uv.lock                   # Locked dependencies
└── README.md
```

## Development

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Dependencies are managed with `uv`; when changing them, commit both `pyproject.toml` and `uv.lock`. GitHub Actions runs tests and formatting checks. See [coding conventions](docs/STYLE.md).

## License

[MIT licensed](LICENSE).
