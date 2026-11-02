# Calculation notes

## Nutrients and precision

An ingredient contributes `nutrient_per_100g × quantity × allocated_fraction / 100`.
Meal totals sum these contributions. Saturates are included in fat, sugars in carbohydrates, and fibre is separate.

Calculations use `Decimal`. JSON decimal numbers are loaded directly as decimals,
numeric strings are also accepted. Fractions such as 2/3 have finite precision.
Only output is rounded, to two decimal places using half even rounding.

## Meal allocation and shopping

The schedule repeats: lunch uses the previous day's batch and dinner uses the
batch from two days earlier. Category fractions specify the lunch share, with
the remainder assigned to dinner. A category missing from the split currently
goes entirely to lunch.

- **Prepared:** Batches cooked on the selected days plus those days' breakfast,
  snack, supplement, and exercise meals.
- **Eaten:** Ingredients consumed on those days, including earlier batches.

Both totals agree over a complete schedule cycle, allowing Decimal rounding.
Tests check this for quantities and nutrients (they do not verify food labels).

## Data and units

Food records require a category and all eight nutrients. Validation rejects
unknown ingredients, missing nutrients, duplicate JSON keys, non finite or
negative numbers, fractions outside [0, 1], sugars above carbohydrates and
saturates above fat. The datas meals `comments` entry is metadata, it does
not control whether an ingredient is included.

Quantities are treated as grams in each food's recorded raw/cooked state.
There is no yield conversion, stock tracking or pack rounding. Food sources,
state labels and tablet/capsule units still need verification before shopping
totals can be treated as purchase quantities.

## Custom schedules

Pass `--schedule schedule.json` with this structure:

```json
{
  "days": ["monday", "tuesday"],
  "exercise_split": {"monday": "strength", "tuesday": "run"},
  "categories_split": {"carb": "0.75", "protein": "0.5"}
}
```

These fractions are examples. Day names must be distinct and match cooking
entries in the meals file, exercise names must also match meal entries.
`breakfast`, `snack`, and `supplements` are required but may be empty.
`--start-day` must belong to the schedule, and `--days` must be positive.
