# Meal Plan Calculator

A Python command-line project for calculating daily nutrition and shopping quantities from a configurable, repeating meal plan.

[![Eight-second preview of calculated daily nutrition](docs/media/preview.gif)](https://raw.githubusercontent.com/ojops/meal-plan-calc/45d36fb767beec954759e319df599bb409524fab/docs/media/demo.mp4)

*Preview: historical meal-plan snapshot, including the formerly automatic electrolyte powder. [Watch the full 36-second demonstration (MP4)](https://raw.githubusercontent.com/ojops/meal-plan-calc/45d36fb767beec954759e319df599bb409524fab/docs/media/demo.mp4) · [How the video is made](docs/DEMO.md).*

## Overview

Use a repeating meal plan to calculate daily nutrients and shopping quantities. JSON files define foods, meals, and exercise schedules. Batch allocation accounts for food prepared on one day and eaten later.

Optional targets compare intake with exercise-specific goals. Contribution reports show which ingredients supply each nutrient.

## Features

- Calculate calories, fat, saturates, carbohydrates, sugars, fibre, protein, and salt
- Configure foods, meals, and exercise schedules using JSON
- Include additional electrolyte powder only on explicitly selected days
- Distribute cooked batches across subsequent lunches and dinners
- Report shopping quantities for arbitrary periods, based on food **prepared** or **eaten**
- Evaluate energy and nutrient aims, minimums, and maximums by exercise type
- Show absolute and percentage deviations, plus the largest consumed ingredient contributions
- Validate inputs and retain precision using Python `Decimal`

Targets are user-defined objectives, not universal dietary requirements. The optional
[profile-driven optimiser](docs/OPTIMISATION.md) now derives macro ranges from body
weight and exercise-specific **total daily calorie budgets**, fits those ranges
first, then minimises changes to the existing plan. No exercise calories are added
a second time. Hard nutritional limits, exclusions and practical portions remain
mandatory; optional foods can be zero or a useful minimum, with gram increments or
explicit whole-unit conversions.

```bash
uv sync --locked --extra optimise
cp -n data/profile.macros.example.json profile.local.json
cp -n data/portion-rules.example.json portions.local.json
# Edit the local files before running the optimiser.
uv run --extra optimise python -m meal_plan_calc.optimise --profile profile.local.json --portion-rules portions.local.json --output proposals/report.json --export-meals proposals/meals.json
```

Edit the local copies: supplied body data, coefficients and unit conversions are
illustrative, not personalised recommendations. Existing inputs and output files
are never overwritten. Reports show remaining target deviations, batch effects,
shopping changes and solver outcomes; a mathematical optimum does not certify
nutritional adequacy. Existing profiles and `--preferences` commands still work.
SciPy/HiGHS remains an optional pinned dependency; ordinary calculation is unchanged.
See the [formulation, examples, compatibility and limitations](docs/OPTIMISATION.md).

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

Edit `data/foods.json` and `data/meals.json`, or use `--foods`, `--meals`, and `--schedule` for custom files. See `uv run meal-plan-calc --help` for all options.

### Optional electrolyte powder

The supplied plan excludes additional electrolyte powder by default. Select the
days when you want the 6 g portion included:

```bash
uv run meal-plan-calc --sweaty tuesday --sweaty thursday
uv run meal-plan-calc --days 14 --report shopping --sweaty tuesday
```

Each selected day gets one portion per occurrence, including across repeated weeks.
The selection applies to nutrition, targets, contributions, and both shopping bases.
The run-day tablet remains in the normal run meal.

For a saved preference, add `"electrolytes_days": ["tuesday", "thursday"]` to your
schedule JSON. CLI day selections replace that list. `--no-extra-electrolytes`
disables it for a report. Adjust the portion in `extra_electrolytes` in
`data/meals.json`. See [selection rules](docs/CALCULATIONS.md#optional-electrolyte-powder)
for custom files and migration from the old default.

### Nutritional targets and contributions

```bash
uv run meal-plan-calc --targets data/targets.example.json --report targets
uv run meal-plan-calc --targets data/targets.example.json --report nutrition --days 1 --contributors protein
```

The example targets illustrate the format and are **not nutritional recommendations**. Supply your own goals in kcal for calories and grams for other nutrients. Defaults can be overridden by exercise type.

Reports show actual intake, signed and absolute deviations, percentage deviation, and goal status. A zero target has an undefined percentage (`n/a`). Only configured nutrients are assessed. See [target configuration and formulas](docs/CALCULATIONS.md#nutritional-targets) for modes, tolerances, and overrides.

`--contributors nutrient` works with or without targets and shows up to five ingredients, their consumed quantities, meal sources, and recorded states. Use `nutrition`, `targets`, or `both` reports for these features. Shopping uses the same plan and optional powder selection.

## Calculation Method and Limitations

Lunch uses the previous day's batch, and dinner uses the batch from two days earlier. Category fractions divide each batch. Nutrients are listed per 100 g, with quantities in the food's recorded **raw or cooked state**. No cooking-yield or purchase-pack conversion is performed. Supplement units still need checking.

Quinoa and grains quantities refer to **cooked** product weights. See the [input audit notes](docs/CALCULATIONS.md#specific-uncertainties-in-the-supplied-example) before relying on the example data.

See [calculation notes](docs/CALCULATIONS.md) for formulas, schedule rules, and data limitations.

## Development Roadmap

Development is focused on moving from calculating what a meal plan provides to evaluating it against useful nutritional objectives, while preserving reliable shopping calculations.

### Planned

- **Validate inputs:** audit nutrient sources, raw versus cooked weights, and supplement units before interpreting target comparisons as a dietary assessment.
- **Compare proposed adjustments:** build on the implemented targets and contribution reports to compare explicit portion scenarios, including their shopping effects, without mutating the baseline.
- **Constrain future optimisation:** define portion bounds, preferences, and treatment of competing goals before introducing an optimiser.
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
├── tests/                    # Nutrition, targets, shopping, and validation tests
├── docs/                     # Calculation and demo documentation
│   └── media/                # Preview GIF, MP4, and recorded data
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

When changing dependencies, commit both `pyproject.toml` and `uv.lock`. GitHub Actions runs tests and formatting checks. See [coding conventions](docs/STYLE.md).

## License

[MIT licensed](LICENSE).
