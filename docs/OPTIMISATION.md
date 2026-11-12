# Macro targets and practical portions

The optional optimiser proposes a separate plan for the existing repeating
schedule. It does not edit meals, food data, profiles or previous outputs.
Calories/macros are planning assumptions, not personalised medical advice or a
guarantee of nutritional completeness. The example profiles are fictitious.

## Quick start

```bash
uv sync --locked --extra optimise
cp -n data/profile.macros.example.json profile.local.json
cp -n data/portion-rules.example.json portions.local.json
# Edit both files before treating the proposal as your own plan.
uv run --extra optimise python -m meal_plan_calc.optimise \
  --profile profile.local.json --portion-rules portions.local.json \
  --output proposals/report.json --export-meals proposals/meals.json
uv run meal-plan-calc --meals proposals/meals.json --report nutrition
uv run meal-plan-calc --meals proposals/meals.json --report shopping --shopping-basis eaten
uv run meal-plan-calc --meals proposals/meals.json --report shopping --shopping-basis prepared
```

Every output must be a **new** path. Existing files are refused, including profile,
food and baseline meal files. `--export-meals` is optional; no meal file is exported
on infeasibility, a solver limit, or a failed numerical audit. The diagnostic report
still records solver outcomes when a solve stops without an accepted plan.
Personal `*.local.json` files and `proposals/` are Git-ignored. The copy commands
also preserve existing local files; choose a fresh filename if yours uses the
older profile format.

`--foods`, `--meals` and `--schedule` use the existing formats. Use the same custom
schedule for subsequent reporting. `electrolytes_days` remains the explicit
selection for extra powder; optimisation never switches it on automatically.
`--preferences` remains an alias of `--portion-rules` for older commands.

## Macro profile (schema version 2)

The profile has a positive `weight_kg`, common `default` assumptions, and an
`exercise` entry for **every exercise type used by the schedule**. Each type must
specify its total daily `calories`, already including exercise. No exercise
expenditure is added again, and this schema does not accept duration adjustments.

```json
{
  "schema_version": 2,
  "weight_kg": "75",
  "default": {
    "protein_g_per_kg": "1.6",
    "fat_fraction": "0.30",
    "tolerance_fraction": "0.05"
  },
  "exercise": {
    "strength": {"calories": "2400"},
    "run": {"calories": "2700", "protein_g_per_kg": "1.8"},
    "mobility": {"calories": "2250", "macro_overrides": {"protein": "120"}}
  },
  "hard_targets": [],
  "hard_limits": {
    "default": {
      "fibre": {"value": "25", "mode": "minimum"},
      "salt": {"value": "6", "mode": "maximum"},
      "saturates": {"value": "25", "mode": "maximum"}
    }
  }
}
```

These example numbers are **user-choice demonstrations, not sourced dietary
reference values**. No physiological adequacy claim is made for them.

Target centres follow:

1. Protein = body weight × `protein_g_per_kg`.
2. Fat = calorie budget × `fat_fraction` ÷ 9.
3. Carbohydrate = (calorie budget − 4 × protein − 9 × fat) ÷ 4.

Precedence is explicit: exercise-specific assumptions replace defaults;
`macro_overrides` in grams replace derived protein/fat/carbohydrate values;
exercise-specific overrides replace default overrides **per nutrient**. Derived
carbohydrate is calculated after applying protein/fat overrides. A default explicit
override remains active unless replaced by the exercise entry. Each target range
is centre ± `tolerance_fraction × centre` for that exercise type.

For a 75 kg example with a 2,700 kcal budget, 1.6 g/kg protein and 30% fat:
protein is 120 g, fat 90 g and carbohydrate 352.5 g, before any overrides.
Negative remaining calories are rejected. Explicit carbohydrate overrides must
keep 4/4/9 macro energy within the calorie target tolerance (with a tiny decimal
roundoff allowance). Unknown keys, uncovered exercise types and nonfinite values
are errors. No silent substitution of guessed inputs occurs.

The 4/4/9 relationship is approximate. Food-label calories can differ because of
fibre, labelling conventions and rounding. Actual nutrition uses the existing food
database's separate calorie and macro fields. A remaining mismatch is reported,
not hidden by replacing labelled calories or claiming every target is met.

Calories, protein, fat and carbohydrate are **soft target ranges** by default.
To make selected ranges mandatory, list their names in `hard_targets`.
`hard_limits.default` accepts other supported nutrients with `minimum` or
`maximum` mode, optional absolute `tolerance`, and `value` in grams.
`hard_limits.exercise` can replace a nutrient's complete specification for a
particular exercise type. These limits are always hard constraints.

## Portion rules

One editable file contains `adjustable`, optional `excluded`, `groups` and
`minimums`. A food's adjustable rule applies separately to every existing source
entry containing that food. A batch entry means **prepared batch grams**, not the
amount eaten on one day. Shared breakfast/snack/exercise entries remain shared.

```json
{
  "adjustable": {
    "oats": {"min_g": "40", "max_g": "150", "required": true, "step_g": "5"},
    "extra_virgin_olive_oil": {"min_g": "5", "max_g": "25", "required": false, "step_g": "5"},
    "egg": {"min_g": "70", "max_g": "140", "unit_g": "70", "unit_label": "illustrative edible egg portion"}
  },
  "excluded": [],
  "groups": {"fruit": ["apple", "orange", "banana", "kiwi", "blueberries"]},
  "minimums": [{"group": "fruit", "grams": "250", "days": ["tuesday", "saturday"]}]
}
```

- `required: true` (default): quantity lies between its minimum and maximum.
- `required: false`: quantity is zero **or** at least its positive minimum, up to
  its maximum. This prevents tiny positive optional portions.
- `step_g`: quantity is an integer multiple of this increment from zero.
- `unit_g`: alternative to `step_g` for whole units, using an explicitly supplied
  grams-per-unit conversion. Measure/verify the edible weight in the food's recorded
  state; the example 70 g conversion is illustrative, not inferred or validated.
- Omitting both increment fields allows continuous grams for that food.
- `excluded`: known foods forced to zero wherever consumed, even if previously
  fixed. Excluded foods cannot also appear in `adjustable`. An exclusion of a known
  food absent from the plan is harmless. No replacement food is introduced.

All unlisted foods, including supplements, retain their baseline quantities.
Supplements are not automatically selected as optimisation variables. Small
quantities remain appropriate for some spices; minimums are deliberately specific
to foods. A required portion range with no valid increment is infeasible.

Food/group `minimums` apply to grams **eaten after allocation**. Specify `food` or
`group`, `grams`, and optionally `days`; omission means all schedule days. A group
minimum is the sum across members, not a minimum for each member. Groups must list
distinct known foods. Raw/cooked states are retained without yield conversion;
check whether adding differently prepared foods' gram weights is meaningful for
your intended group minimum.

## Two-stage mixed-integer formulation

SciPy's existing pinned HiGHS backend solves the model; no new dependency is added.
Each variable represents a food quantity in an existing meal or prepared batch.
The solver matrix stores only nonzero coefficients to avoid allocating large
arrays of zeros as the schedule grows. Increment variables are integer counts. Optional foods use a binary active/inactive variable linked
to their lower and upper bounds. Existing batch allocation functions map those
variables into each day's food quantities and nutrients.

Stage 1 minimises the sum, over days and soft targets, of:

`distance outside target range / max(target centre, 1 native unit)`

Each soft target contributes equally in proportional terms; a target already in
range has zero penalty. Hard targets, nutritional limits, portion constraints,
exclusions and food/group minimums never receive violation slack.

Stage 2 preserves stage 1's optimum within **1e-6 of the summed normalised
objective**, then minimises:

`sum(abs(proposed source grams − baseline source grams) / max(baseline, 50 g))`

This ordered approach is called lexicographic optimisation: target fit has
priority over keeping quantities close to the baseline. The 50 g floor avoids
extreme penalties on tiny baseline portions. Neither objective measures health or food cost. Multiple equally optimal
plans can exist, particularly with shared batch allocations.

`--time-limit` defaults to 60 seconds **per stage**. Both stages request zero relative
MIP gap. A time limit or solver failure produces no accepted meal plan, even if
a candidate solution exists. This avoids reporting an unproven result as optimal. Reports retain
status, message, objective, time limit, MIP gap and dual bound where HiGHS supplies
them. Gap fields can be null for continuous solves.

The solver uses floats. Inputs, nutrition calculations and final auditing use
Decimal. Integer counts must be within 1e-5 of an integer before exact increment
reconstruction. Final portion bounds permit 1e-7 g numerical error; hard assembled
rows permit `1e-7 × max(1, |bound|)`. The reconstructed primary objective must remain
within the 1e-6 preservation allowance plus 1e-7 audit tolerance. Nutrition is then
recomputed through the existing calculation engine and checked again. This is not
rounding a continuous proposal to convenient portions after solving.

## Reports and nutrition coverage

Reports contain resolved assumptions, targets and their hard/soft status,
baseline and proposed nutrition, signed deviations, and remaining range violations,
baseline/proposed target-fit objectives, quantity changes, daily batch effects,
prepared/eaten shopping differences, solver stages and constraint audits.
CLI reports include input checksums, schedule and SciPy version.

`optimal` describes the mathematical model, **not universal satisfaction of soft
targets or a healthy diet**. Infeasibility guidance identifies categories to inspect
but does not claim an exact conflicting constraint set. Missing nutrient fields
are rejected instead of filled with zero. Unsupported micronutrients cannot be
configured as though they were assessed. Food variety, micronutrient adequacy,
medical conditions, absorption and personal suitability are outside this model.
Review nutritional data quality and appropriate targets independently.

## Reproducible examples and checks

```bash
uv run --extra optimise python scripts/macro_optimisation_example.py
uv run --extra optimise pytest
uv run ruff check .
uv run ruff format --check .
```

[Recorded synthetic scenarios](examples/macro-scenarios.json) isolate the maths;
they are not meal recommendations. The baseline target-range objective is 5.60.
The feasible increment-constrained example reduces it to zero, then chooses the
minimum baseline change (2.8). With a 150 g optional minimum, one batch can be zero
and another 190 g, retaining the target fit. An incompatible hard calorie target
and maximum portion is infeasible and exports nothing. Equivalent batch splits
may differ with solver versions while retaining the same objectives.

The shipped realistic profile/portion examples also solve, but some soft ranges
remain unmet because not all foods can change and the schedule shares quantities.
Inspect those residuals before deciding whether to revise assumptions or bounds.
Never relax hard limits automatically to make a result look better.

## Compatibility and implementation map

Existing `profile.example.json` and `optimisation.example.json` were preserved.
Profiles without `schema_version` retain the original base/per-kg/per-hour target
formulas and all-hard goal semantics. They use the same two-stage engine, with an
identically zero primary objective. `scripts/optimisation_example.py` remains the
legacy example; its recorded results describe the earlier continuous model.
No migration rewrites a user's existing profile.

- `macro_profile.py`: target derivation, precedence and profile validation.
- `optimisation.py`: schedule/portion validation, daily constraints and reporting.
- `portion_solver.py`: integer/optional portions, two solves and final audit.
- `optimise.py`: input/output handling and overwrite protection.

Be ready to explain this formulation and its limitations before presenting it in
applications: particularly soft versus hard constraints, lexicographic objectives,
shared batch variables, integer portions, and why an optimum is not a health claim.
