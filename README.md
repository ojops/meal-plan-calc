# Meal Plan Calculator

A Python project for calculating daily nutritional intake and optimising food quantities to meet nutrition targets with minimal excess.

## Overview

This project aims to develop a meal planning tool that calculates nutritional intake from food composition data and meal plans, then optimises ingredient quantities to bring daily nutrition as close as possible to specified targets.

The project is being developed incrementally, starting with nutritional calculations and progressing towards an optimisation algorithm that balances target accuracy, food quantities, and practical meal planning constraints.

## Features

- Nutritional calculations for individual meals and daily food intake
- Food composition data and configurable meal plans stored in JSON
- Nutrient tracking for calories, macronutrients, fibre, and salt
- Allocation of prepared food between meals
- Planned optimisation of food quantities against daily nutrition targets
- Planned minimisation of excess nutrition and unnecessary food quantities

## Requirements

- Python 3.10
- [uv](https://docs.astral.sh/uv/)

The setup instructions below assume Ubuntu or WSL running Ubuntu.

## Installation

Clone the repository:

```bash
git clone https://github.com/ojops/meal-plan-calc.git
cd meal-plan-calc
```

Install the project dependencies:

```bash
uv sync --locked
```

## Usage

Run the meal plan calculator from the repository root:

```bash
uv run python -m meal_plan_calc.main
```

The calculator loads food composition data and meal quantities from JSON files, calculates daily nutritional totals, and prints the results.

## Development Roadmap

The project is being developed incrementally, with an emphasis on accurate nutritional calculations, reliable data handling, and effective optimisation.

### Planned

- **Testing:** Add automated tests for nutritional calculations, meal allocation, and edge cases.
- **Data validation:** Validate food composition data, ingredient quantities, and meal plan configurations.
- **Nutrition targets:** Define configurable daily nutritional targets and acceptable tolerances.
- **Optimisation:** Develop an algorithm to adjust food quantities to minimise deviations from nutritional targets.
- **Excess minimisation:** Penalise unnecessary excess while prioritising important nutritional targets.
- **Constraints:** Support practical restrictions on ingredient quantities, food choices, and minimum or maximum serving sizes.
- **Evaluation:** Compare optimisation results against the existing meal plan and assess nutritional accuracy and practicality.

## Project Structure

```text
meal-plan-calc/
├── data/                  # Food composition data and meal plans
├── src/
│   └── meal_plan_calc/
│       ├── __init__.py
│       ├── main.py        # Application entry point
│       ├── nutrition.py   # Nutritional calculation functions
│       └── optimiser.py   # Planned optimisation logic
├── tests/                 # Automated tests
├── pyproject.toml         # Project metadata and dependencies
├── uv.lock                # Locked dependency versions
├── .gitignore
├── LICENSE
└── README.md
```

## Development

Dependencies are managed using `uv`. Add a dependency with:

```bash
uv add package-name
```

Commit changes to both `pyproject.toml` and `uv.lock` when dependencies change.

Run automated tests with:

```bash
uv run pytest
```

## License

See [LICENSE](LICENSE) for details.