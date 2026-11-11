# Profile-driven, minimum-change meal planning

This optional feature proposes a new repeating schedule. It does not edit the
current meal plan, food database, profile or existing output files. All example
body data and target coefficients are illustrative, not dietary recommendations.
The calculator covers only the nutrients in its food database; it cannot establish
complete nutritional adequacy or infer individual requirements from weight alone.

## Run it

```bash
uv sync --locked --extra optimise
cp data/profile.example.json profile.local.json
cp data/optimisation.example.json preferences.local.json
# Edit both local files for your chosen targets and portion limits.
uv run --extra optimise python -m meal_plan_calc.optimise \
  --profile profile.local.json --preferences preferences.local.json \
  --output proposals/report.json --export-meals proposals/meals.json
uv run meal-plan-calc --meals proposals/meals.json --report nutrition
uv run meal-plan-calc --meals proposals/meals.json --report shopping --shopping-basis eaten
uv run meal-plan-calc --meals proposals/meals.json --report shopping --shopping-basis prepared
```

Use a new output name for every run. `--export-meals` is optional and only writes
on a successful, audited solution. An infeasible run writes a diagnostic report,
returns exit code 1, and exports no meal plan. Existing reports and baseline files
are never overwritten, even if passed as output paths. Personal `*.local.json`
files and `proposals/` are Git-ignored.

`--foods`, `--meals` and `--schedule` accept the existing repository formats.
Use the same custom schedule for subsequent reporting. Optional electrolyte
selection is read from its `electrolytes_days`; it is not automatically enabled.
No supplement or other unlisted food is adjustable by default.

## Separate personal profile

Each nutrient target is:

`base + per_kg × weight_kg + per_hour × duration_hours[day]`

Calories use kcal; other nutrients use grams, so their coefficients have matching
units. `default` defines the common formula. An `exercise` entry replaces the
complete formula for that nutrient on days of that exercise type. Exercise types
come from the schedule, not a separate conflicting calendar. A duration must be
supplied for every day using a nonzero `per_hour` coefficient, including explicit
zero duration where appropriate. Weight must be positive and numbers finite.

For example, the fictitious 75 kg example uses a run calorie aim of
`30 × 75 + 300 × hours`. A 1.5-hour run day therefore has an aim of 2,700 kcal.
These coefficients are editable assumptions, not a validated physiological model.
Age/sex/height are not collected merely to imply greater accuracy; this version
uses user-selected target coefficients rather than estimating a metabolic rate.

Targets retain the existing modes:

- `aim`: intake must lie between value minus tolerance and value plus tolerance.
- `minimum`: intake must be at least value minus tolerance (floored at zero).
- `maximum`: intake must be at most value plus tolerance.

Unspecified nutrients are reported but not constrained. Constraints are hard;
contradictory targets are not silently relaxed.

## Portion limits, food minimums and groups

`adjustable` lists foods the solver may change, with explicit `min_g` and `max_g`.
Those bounds apply separately to each existing meal/source entry containing that
food: a cooked batch entry means the full prepared batch, not a daily intake.
All other entries are fixed. The optimiser does not invent new foods or recipes.

`minimums` constrain grams actually **eaten** on a day, after batch allocation:

```json
{
  "adjustable": {"oats": {"min_g": "40", "max_g": "150"}},
  "groups": {"fruit": ["apple", "orange", "banana", "kiwi", "blueberries"]},
  "minimums": [
    {"food": "oats", "grams": "50"},
    {"group": "fruit", "grams": "250", "days": ["tuesday", "saturday"]}
  ]
}
```

Omitting `days` applies a minimum to every schedule day. A group is an explicit
list of distinct known foods, independent of the database's allocation categories.
A group minimum counts their combined consumed grams, not a minimum of every
member. Bounds and minimums use each food's recorded raw/cooked weight; mixed
states are not converted into equivalent raw weights. Check the meaning of a
mixed-state group before using its summed grams as a target.

## Mathematical formulation

One decision variable `x_i` represents grams in an existing `(meal source, food)`
entry. Shared breakfast/snack entries and cooked batches therefore have one
consistent quantity across the repeating schedule. The existing allocation
functions map those variables to daily consumed grams and nutrient totals.

The linear programme minimises:

`sum_i |x_i - original_i| / max(original_i, 50 g)`

Auxiliary nonnegative variables represent absolute deviations. Scaling avoids
letting large portions dominate solely because they contain more grams; the
50 g floor prevents tiny original portions receiving extreme weights. This is a
transparent modelling choice, not a nutrition score. There is no food-price
objective because the current food database has no validated price data.

Constraints enforce every day's nutrient ranges, chosen food/group minimums and
portion bounds. SciPy's HiGHS solver works with floating-point coefficients;
inputs, original food arithmetic and the independent post-solve audit use Decimal.
The audit permits numerical constraint residuals up to `1e-6 × max(1, |bound|)`
in each assembled row, and `1e-6 g` at portion bounds. This numerical allowance
is separate from the user's nutritional target tolerance. Values are not rounded
before checking. Whole eggs/pack sizes and integer portions are not modelled.
Multiple equally good solutions may exist; exact quantities can vary by solver
version even when the objective and constraints agree.

The output records baseline/proposed daily nutrition, derived targets, changed
quantities, constraint residuals, input hashes, schedule and solver version.
`proposed_meals` preserves the existing meals schema and can be exported directly.
The independent audit rejects a materially invalid solver result.

## Reproduced examples

```bash
uv run --extra optimise python scripts/optimisation_example.py
```

[Recorded scenario results](examples/optimisation-scenarios.json) use the shipped
illustrative profile and food data, not the author's personal requirements:

| Scenario | Outcome |
|---|---|
| Energy tolerance ±250 kcal | One change: Friday batch rice 105 → approximately 110.38 g; normalized change objective 0.05124. |
| Energy tolerance ±100 kcal | Five source entries change; objective 1.26519. |
| Require 10,000 g fruit/day while fruit remains fixed | Infeasible; no proposed plan. |

The Friday batch contributes to Saturday lunch and Sunday dinner. Its small
increase raises Saturday from approximately 2,434.87 to 2,450 kcal, the lower
edge of that day's illustrative range. Sunday remains within its own range.
The simpler solution is retained because every additional change would increase
the objective. These results show constraint sensitivity, not health benefits.

## Application discussion

Be ready to explain the objective, shared batch variables, hard versus soft
targets, continuous versus integer quantities and infeasibility. Understand and
reproduce the implementation before presenting it as evidence in an interview.
