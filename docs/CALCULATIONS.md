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

## Nutritional targets

Pass `--targets path/to/targets.json`. This is optional and does not alter foods, portions, allocation fractions or shopping quantities. The [example file](../data/targets.example.json) contains **illustrative numbers only**, not health recommendations.

```json
{
  "default": {
    "calories": {"value": "2400", "mode": "aim", "tolerance": "100"},
    "protein": {"value": "120", "mode": "minimum"},
    "salt": {"value": "6", "mode": "maximum"}
  },
  "exercise": {
    "run": {"calories": {"value": "2600", "mode": "aim", "tolerance": "100"}}
  }
}
```

Nutrient names are the existing eight keys (`calories`, `fat`, `saturates`, `carbs`, `sugars`, `fibre`, `protein`, `salt`). `calories` uses kcal and all others use grams. Targets refer to a day's **consumed nutrition**, not grams of an ingredient. Numeric JSON values and decimal strings use `Decimal`; no rounding occurs before comparison.

`default` and `exercise` are optional objects, but every exercise type actually used in the schedule must resolve to at least one target. An exercise override replaces that nutrient's complete specification; other default nutrients remain. Unlisted nutrients are unassessed, not zero targets. Unknown nutrients, exercise types, fields, modes, duplicate keys, negative or nonfinite values are rejected.

A target requires `value`; `mode` defaults to `aim` and `tolerance` to zero. Tolerance is an absolute amount in the target's unit:

| Mode | Satisfied when |
| --- | --- |
| `aim` | `value - tolerance <= actual <= value + tolerance` |
| `minimum` | `actual >= value - tolerance` |
| `maximum` | `actual <= value + tolerance` |

Boundaries are inclusive. For every mode, `deviation = actual - value`, `absolute_deviation = abs(deviation)` and `percentage_deviation = 100 * deviation / value`. Percentage deviation is undefined for a zero target, even when actual is also zero. Signed and absolute deviations describe distance from the nominal value; they are **not** the amount needed to meet a tolerance boundary. A positive difference from a minimum can still be `met`; a negative difference from a maximum is also `met`. Display rounding can make a boundary appear equal even when the unrounded comparison is outside it.

## Explaining intake

Use `--contributors protein` (or another nutrient) with nutrition or target reports. `day_contributions()` returns per-consumed-ingredient quantities, nutrition, meal names and source keys. Lunch and dinner identify their earlier cooking day. The CLI sorts by nutrient amount and shows up to five entries and each entry's share of the full daily total; repeated ingredients in different meals remain separate.

The report calls the same meal calculator and schedule allocation functions as daily totals. It does not convert raw/cooked states or silently move food between preparation and eating dates. Finite `Decimal` precision can produce negligible summation-order differences; only display values are rounded. Contributors describe where nutrition comes from, not which food is responsible for a shortfall or should be increased. Unverified supplement units and source data still limit the usefulness of any target assessment.
