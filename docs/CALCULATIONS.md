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

### Specific uncertainties in the supplied example

These observations come from the repository's records, not verified current
product labels. The example is not an audited dietary assessment:

- `vitamin_d3_and_k2`, `zinc`, `omega_3` and `magnesium_glycinate` each have a
  quantity of `1` and zero for all eight tracked nutrients. The program interprets
  each quantity as **1 g**, not one tablet/capsule. Their recorded zero contribution
  is not evidence that the products contain no energy, fat or other nutrients;
  the oil product in particular needs its label checked. Vitamin/mineral content
  is outside the eight tracked nutrients.
- `quinoa` and `grains` are now labelled `state: cooked`, matching the intended
  “Simply Cooked” products. Quantities refer to cooked product weights. Their
  nutrient values and portion quantities are unchanged; this corrects the state
  metadata, without performing a cooking-yield conversion or verifying labels.
- The `run` meal includes 4.3 g of `electrolytes_tablet`, contributing **0.8256 g
  salt**. Additional powder is now optional (see below). Its 6 g portion adds
  **0.7800 g salt**, making **1.6056 g** from tablet plus powder on a selected run
  day. The powder's nutrition remains explicitly marked as an estimate.

Before relying on target statuses or shopping weights, audit the exact products,
serving masses, nutrient-label basis and raw/cooked states. No values or portions
have been guessed to resolve these uncertainties.

## Optional electrolyte powder

The supplied `run` meal no longer includes powder. The separate
`extra_electrolytes` meal contains `electrolytes_powder: "6"` (grams) and is
included only on selected days. The tablet remains in the run meal.

Use `--electrolytes-day tuesday`, repeating the option for additional days, or
save an `electrolytes_days` list in a schedule file. Omission means no extra
powder. CLI selections replace the saved list; `--no-extra-electrolytes` overrides
it with no selected days. These two CLI options cannot be combined.

Day names must belong to the repeating schedule. Each selected day receives one
portion per occurrence in the report, even across multiple cycles; duplicate
names do not add extra portions. Days outside the reporting window add nothing.
Selection is allowed on non-run days too, without changing the day's exercise
type or its target overrides. To select a single occurrence, report that date's
schedule day with `--days 1`; this calculator does not model calendar dates.

The extra meal is consumed directly that day, without lunch/dinner allocation.
Nutrition, target comparisons, contribution records and prepared/eaten shopping
all include the same portion. Library callers can pass `electrolytes_days` to
the daily nutrition, contribution and shopping functions; it defaults to empty.

With custom meal files, define `extra_electrolytes` only if you select extra days.
Its quantity can be changed to your actual serving. When migrating older files,
**move** the powder out of `run` into `extra_electrolytes`: powder left in any
ordinary meal is still counted as normal intake, and selecting an extra portion
adds to it. Comments are descriptive; the day selection implements the condition.

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
