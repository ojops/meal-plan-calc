# Portfolio video: reproduction and verification

The eight-second README preview shows daily nutrition for the supplied week. The 1 minute 29 second silent MP4 follows those ingredients from a food record to a shopping list, then shows how the optional optimiser proposes a week of practical portions. The MP4 includes chapter markers. The table below is a text companion.

## Generate

From the repository root, use Python 3.10, uv, FFmpeg with H.264 support, and DejaVu fonts. On Ubuntu the system packages are `ffmpeg` and `fonts-dejavu-core`. Rendering uses Pillow and the pinned SciPy optimiser on the CPU.

```bash
uv sync --locked --extra demo --extra optimise
uv run --locked --extra demo --extra optimise python scripts/render_demo.py
```

The renderer writes `demo.mp4`, `preview.gif`, and `demo-data.json` to `docs/media/`. To inspect one still per chapter in a different directory, run

```bash
uv run --locked --extra demo --extra optimise python scripts/render_demo.py --stills-only --output-dir /tmp/meal-demo-stills
```

## What the film demonstrates

| Time | Follow the example |
| --- | --- |
| 0:00–0:08 | **Daily intake.** Food labels give values per 100 g. At 374 kcal per 100 g, 75 g of oats supplies 280.50 kcal. The full Monday adds up to 2,399.67 kcal and 136.79 g of protein. |
| 0:08–0:17 | **Batch meals.** Monday’s 161 g of rice supplies 120.75 g to Tuesday lunch and 40.25 g to Wednesday dinner. Its calories follow the same split. |
| 0:17–0:26 | **Edit a meal.** In a copy of the plan, change breakfast oats from 75 g to 100 g. Monday gains 93.50 kcal, and the same breakfast recurs each day. |
| 0:26–0:37 | **Shopping.** From Monday to Wednesday the plan prepares 271 g of rice and eats 269.75 g, including portions from earlier batches. Both totals reach 613 g over the full weekly cycle. |
| 0:37–0:50 | **Targets.** Monday meets the example 120 g protein minimum. Its largest contribution is 22.69 g of protein from the salmon cooked in Sunday’s batch and eaten at Monday lunch. |
| 0:50–1:01 | **Optional powder.** Tuesday’s default includes the run-day tablet. Selecting Tuesday adds 6 g of powder and takes daily salt from 3.33 g to 4.11 g. |
| 1:01–1:14 | **Portion rules.** The example strength day has a total budget of 2,400 kcal. The solver can move oats in 5 g steps, omit optional oil, and count eggs in whole units using the example conversion. |
| 1:14–1:29 | **Proposal.** First minimise gaps outside the preferred ranges, then minimise portion changes at that fit. The sum of normalised gaps falls from 2.20 to 0.38. Thirteen daily soft targets still fall outside their ranges. Weekly prepared oats increase from 525 g to 1,050 g. |

Try the target and contribution chapter with the supplied data.

```bash
uv run meal-plan-calc --days 1 --report targets --targets data/targets.example.json --contributors protein
```

To reproduce the final chapter, use the supplied example files and fresh output paths. The summary identifies the largest portion changes, remaining soft gaps, and shopping changes. The export can be read by the usual reporting commands.

```bash
uv run --extra optimise python -m meal_plan_calc.optimise \
  --profile data/profile.macros.example.json --portion-rules data/portion-rules.example.json \
  --summary --output proposals/demo-report.json --export-meals proposals/demo-meals.json
uv run meal-plan-calc --meals proposals/demo-meals.json --days 1 --report nutrition
```

`scripts/demo_reports.py` extends the original `build_demo()` recording with production target comparisons, contribution records, a selected-day powder calculation, and a real two-stage optimiser run. The recording includes input SHA-256 checksums, exact decimal quantities, solver status, and the CLI summary. The breakfast edit uses a copy. All amounts use the food’s recorded raw or cooked state. The body weight, nutrient targets, and egg mass are illustrative. [Calculation notes](CALCULATIONS.md) · [Optimiser and portion rules](OPTIMISATION.md) · [Food-data audit](DATA_AUDIT.md)

## Validate

```bash
uv run --locked --extra optimise pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
ffprobe -v error -show_chapters docs/media/demo.mp4
ffmpeg -v error -i docs/media/demo.mp4 -f null -
ffmpeg -v error -i docs/media/preview.gif -f null -
```

When replacing the media, commit the MP4, GIF, and JSON together. Pin both README video links to that media commit. Encoded bytes can vary with FFmpeg and font versions.
