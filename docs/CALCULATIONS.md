# Calculation notes

This document explains how nutrient totals and shopping quantities are derived. See the [README](../README.md) for commands and installation.

## Nutrition and precision

For each ingredient and nutrient:

```text
contribution = nutrient_per_100g × quantity × allocation_fraction / 100
```

Meal and day totals sum those contributions. Saturated fat is included in total fat, sugars are included in carbohydrates, and fibre is tracked separately.

Calculations use `Decimal`, accepting JSON numbers and numeric strings. Output is rounded to two decimal places using round-half-even. Evaluation uses unrounded values, subject to finite `Decimal` precision for repeating fractions such as 2/3.

## Repeating schedule

Lunch consumes the previous day's cooking and dinner consumes cooking from two days earlier, with wraparound at the end of the schedule. For each food category, the configured fraction goes to lunch and the remainder to dinner. Categories without a configured fraction default to **100% lunch**.

Shopping reports use two different bases:

- **Prepared:** cooking batches and directly consumed meals scheduled during the selected days, including selected electrolyte extras.
- **Eaten:** food consumed during those days, including portions prepared before the selected period.

Prepared and eaten quantities agree over a complete repeating cycle. Shorter periods can differ because cooking and consumption fall on different days.

## Input validation and units

Food records must contain a category and all eight nutrients. Validation rejects unknown ingredients, duplicate JSON keys, missing nutrient values, invalid or negative numbers, invalid allocation fractions, sugars greater than carbohydrates, and saturates greater than total fat. The `comments` entry in `data/meals.json` is metadata, not a meal.

Quantities are grams in the food record's stated **raw or cooked state**. Quinoa and grains refer to cooked product weights. No cooking-yield conversion, stock tracking, or package rounding is performed. Check food sources, state labels, and supplement units before using shopping totals as purchasing instructions.

### Specific uncertainties in the supplied example

These observations come from the repository's records, not verified current
product labels. The example is not an audited dietary assessment:

- `vitamin_d3_and_k2`, `zinc`, `omega_3`, and `magnesium_glycinate` each have a
  quantity of `1` and zero for all eight tracked nutrients. The program interprets
  each quantity as **1 g**, not one tablet/capsule. Their recorded zero contribution
  is not evidence that the products contain no energy, fat, or other nutrients.
  Check the oil product's label in particular. Vitamin/mineral content
  is outside the eight tracked nutrients.

Before relying on target statuses or shopping weights, audit the exact products,
serving masses, nutrient label basis, and raw/cooked states. No values or portions
have been guessed to resolve these uncertainties.

## Optional electrolyte powder

The supplied `run` meal includes the tablet but no powder. The optional
`extra_electrolytes` meal contains `electrolytes_powder: "6"` (grams).
Its nutrient values remain estimates. One portion contributes 0.78 g of recorded
salt, or 1.6056 g together with the run-day tablet.

Use `--sweaty tuesday`, repeating the option for additional days, or
save an `electrolytes_days` list in a schedule file. Omission means no extra
powder. CLI selections replace the saved list. `--no-extra-electrolytes` overrides
it with no selected days. These two CLI options cannot be combined.

Day names must belong to the repeating schedule. Each selected day receives one
portion per occurrence in the report, even across multiple cycles. Duplicate
names do not add extra portions. Days outside the reporting window add nothing.
Selection is allowed on non-run days too, without changing the day's exercise
type or its target overrides. To select a single occurrence, report that date's
schedule day with `--days 1` (this calculator does not model calendar dates).

The extra meal is consumed directly that day, without lunch/dinner allocation.
Nutrition, target comparisons, contribution records, and prepared/eaten shopping
all include the same portion. Library callers can pass `electrolytes_days` to
the daily nutrition, contribution, and shopping functions (it defaults to empty).

With custom meal files, define `extra_electrolytes` only if you select extra days.
Its quantity can be changed to your actual serving. When migrating older files,
**move** the powder out of `run` into `extra_electrolytes`: powder left in any
ordinary meal is still counted as normal intake, and selecting an extra portion
adds to it. Day selection implements the condition. Comments alone do not.

## Custom schedule

Use `--schedule schedule.json` with, for example:

```json
{
  "days": ["monday", "tuesday"],
  "exercise_split": {"monday": "strength", "tuesday": "run"},
  "categories_split": {"carb": "0.75", "protein": "0.5"},
  "electrolytes_days": ["tuesday"]
}
```

These are illustrative fractions. Schedule days must be distinct and have matching cooking and exercise meals. `breakfast`, `snack`, and `supplements` are also required (and may be empty). `--start-day` must belong to the schedule, and `--days` must be positive.

## Nutritional targets

Pass `--targets path/to/targets.json`. This is optional and does not alter foods, portions, allocation fractions, or shopping quantities. The [example file](../data/targets.example.json) contains **illustrative numbers only**, not health recommendations.

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

Nutrient names are `calories`, `fat`, `saturates`, `carbs`, `sugars`, `fibre`, `protein`, and `salt`. Calories use kcal, and all others use grams. Targets refer to daily **consumed nutrition**, not ingredient weights. Numbers and decimal strings use `Decimal` without rounding before comparison.

`default` and `exercise` are optional objects. Every scheduled exercise type must resolve to at least one target. An override replaces that nutrient's complete specification while retaining other defaults. Unlisted nutrients are unassessed. Validation rejects unknown names or fields, invalid modes, duplicate keys, and negative or nonfinite values.

A target requires `value`, `mode` defaults to `aim`, and `tolerance` to zero. Tolerance is an absolute amount in the target's unit:

| Mode | Satisfied when |
| --- | --- |
| `aim` | `value - tolerance <= actual <= value + tolerance` |
| `minimum` | `actual >= value - tolerance` |
| `maximum` | `actual <= value + tolerance` |

Boundaries are inclusive. Minimum 100 with tolerance 10 accepts 90, and maximum 100 with tolerance 10 accepts 110.

For every mode:

- `deviation = actual - value`
- `absolute_deviation = abs(deviation)`
- `percentage_deviation = 100 * deviation / value`, undefined for a zero target even when actual is zero

Deviations measure distance from the nominal target, not a tolerance boundary. A positive minimum deviation or negative maximum deviation can still be `met`. Display rounding can make an out-of-range value appear equal to the boundary.

## Explaining intake

Use `--contributors protein` (or another nutrient) with nutrition or target reports. `day_contributions()` returns consumed quantities, nutrients, meal names, and source keys. Lunch and dinner identify their cooking day. The CLI shows the five largest contributions and their shares of the full daily total. Repeated ingredients in different meals remain separate.

Contributions reuse the daily meal and allocation calculations. Finite precision can cause negligible summation-order differences. These records explain intake rather than prescribe which foods to increase. The input-data limitations above apply to target assessments too.
