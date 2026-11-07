# Calculation notes

This document explains how nutrient totals and shopping quantities are derived. See the [README](../README.md) for commands and installation.

## Nutrition and precision

For each ingredient and nutrient:

```text
contribution = nutrient_per_100g × quantity × allocation_fraction / 100
```

Meal and day totals sum those contributions. Saturated fat is included in total fat; sugars are included in carbohydrates; fibre is tracked separately.

All calculations use `Decimal`. JSON decimal values and numeric strings are accepted; output alone is rounded to two decimal places using round-half-even. Repeating fractions (such as 2/3) use `Decimal` precision.

## Repeating schedule

Lunch consumes the previous day's cooking and dinner consumes cooking from two days earlier, with wraparound at the end of the schedule. For each food category, the configured fraction goes to lunch and the remainder to dinner. Categories without a configured fraction default to **100% lunch**.

Shopping reports use two different bases:

- **Prepared:** cooking batches and the breakfast, snack, supplement and exercise meals scheduled during the selected days.
- **Eaten:** food consumed during those days, including portions prepared before the selected period.

Over a complete repeating cycle, prepared and eaten quantities agree. Shorter periods can differ because cooking and consumption fall on different days.

## Input validation and units

Food records must contain a category and all eight nutrients. Validation rejects unknown ingredients, duplicate JSON keys, missing nutrient values, invalid or negative numbers, invalid allocation fractions, sugars greater than carbohydrates, and saturates greater than total fat. The `comments` entry in `data/meals.json` is metadata, not a meal.

Quantities are treated as grams in the food record's stated **raw or cooked state**. The calculator does **not** convert cooking yields, track stock or round to package sizes. Check food sources, state labels and supplement tablet/capsule units before using the shopping totals as purchasing instructions.

## Custom schedule

Use `--schedule schedule.json` with, for example:

```json
{
  "days": ["monday", "tuesday"],
  "exercise_split": {"monday": "strength", "tuesday": "run"},
  "categories_split": {"carb": "0.75", "protein": "0.5"}
}
```

These are illustrative fractions. Schedule days must be distinct and have matching cooking and exercise meals. `breakfast`, `snack` and `supplements` are also required (and may be empty). `--start-day` must belong to the schedule, and `--days` must be positive.
