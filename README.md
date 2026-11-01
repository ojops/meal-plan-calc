# Meal Plan Calculator

Python 3.10 nutrition totals and shopping quantities from local JSON food data
and a repeating meal-preparation schedule. Decimal arithmetic is used throughout;
no optimiser or external nutrition service is implemented.

```bash
uv sync --locked
uv run pytest
uv run meal-plan-calc
uv run meal-plan-calc --start-day friday --days 14 --report shopping
uv run meal-plan-calc --start-day monday --days 3 --shopping-basis eaten
uv run python -m meal_plan_calc --report nutrition
```

Use `--foods` and `--meals` for alternate JSON files. Example data are included in
built wheels, so the default CLI also works away from the checkout.
`--report` accepts `both`, `nutrition`, or `shopping`.

## Units, preparation and periods

Nutrients are **per 100 g**: calories are kcal and the other tracked nutrients
are grams. Ingredient quantities are grams **in the state of the corresponding
food record** (`raw` or `cooked`). There is no raw/cooked yield conversion, pack
rounding or inventory management. In particular, shopping quantities for cooked
foods are not automatically purchase weights. Tablet/capsule quantities in the
example data require manual unit/source review before treating them as grams.
No food values have been corrected from guesses about supplier products.

Lunch uses the previous day's cooking batch and dinner uses the batch from two
days earlier, wrapping around the repeating schedule. Category fractions specify
the lunch share; dinner receives its complement. An unspecified category goes
entirely to lunch, rather than being counted twice.

- `--shopping-basis prepared` (default) buys ingredients for batches prepared on
  the selected days plus those days' breakfast/snack/supplement/exercise meals.
- `--shopping-basis eaten` totals ingredients actually consumed on those days,
  including carry-over from earlier cooking days.

These bases agree over complete repeating cycles (up to Decimal rounding), but
can differ over short periods. An eaten-basis report describes ingredient demand,
not a purchase recommendation accounting for leftovers already in the fridge.

## Configurable schedule

`--schedule schedule.json` accepts:

```json
{
  "days": ["monday", "tuesday"],
  "exercise_split": {"monday": "strength", "tuesday": "run"},
  "categories_split": {"carb": "0.75", "protein": "0.6666666666666666666666666667"}
}
```

Day names must be distinct and refer to cooking meals in the meals file. Exercise
names must also refer to meals. Common `breakfast`, `snack` and `supplements` meals
are required, but may be empty. Any positive report length is allowed, including
multiple cycles. Choose `--start-day` from that schedule.

Food records require a category and all eight tracked nutrients. Missing nutrients
are errors, not assumed zeros. Unknown ingredients, invalid numbers, negative
quantities, impossible component totals and duplicate JSON keys are rejected.
Fractions must lie in [0,1]. The optional top-level meals `comments` object is
metadata and is not interpreted as instructions or conditional inclusion.

Output rounds once to two places using Decimal's default half-even rounding.
It is an estimate conditional on the input data. Decimal precision does not
establish nutritional accuracy, and supplier/database sources should be checked.

See [calculation notes](docs/CALCULATIONS.md) and [coding standard](docs/STYLE.md).
Next: verify data provenance and units, then consider targets and comparisons
before an optimisation algorithm. MIT licensed; see [LICENSE](LICENSE).
