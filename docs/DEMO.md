# Reproducing the portfolio demonstration

`media/demo.mp4` is a 36-second silent film, 1920 × 1080 at 30 FPS, encoded as
H.264/yuv420p with fast-start metadata. `media/preview.gif` is an 8-second,
768 × 432, 10 FPS looping excerpt. Both are small enough to keep in Git; relative
README links work on review branches and after merging without external hosting.

From the repository root, with Python 3.10 and uv:

```bash
uv sync --locked --extra demo
uv run --locked --extra demo python scripts/render_demo.py
```

Install FFmpeg with libx264 and DejaVu Sans/Mono (Ubuntu packages `ffmpeg` and
`fonts-dejavu-core`). Pillow 12.3.0 is an optional `demo` extra; runtime
calculation dependencies and public interfaces are unchanged. Rendering uses the
CPU and needs no display, browser, graphics driver or external data service.

Use `--output-dir /path/to/output` to select another destination. To inspect the
four chapter layouts without encoding a video:

```bash
uv run --locked --extra demo python scripts/render_demo.py --stills-only --output-dir /tmp/meal-demo-stills
```

## Source of every result

`meal_plan_calc.demo_data.build_demo()` loads and validates the repository's
`data/foods.json` and `data/meals.json`. It calls the existing
`calculate_day_eating_nutrition`, `calculate_meal_nutrition`,
`calculate_shopping_quantities` and `calculate_eating_quantities` functions.
There is no alternative nutrition engine in the renderer.

The JSON recording retains Decimal values as strings, along with SHA-256
checksums of both inputs, so display rounding never becomes a calculation input.
Conversion to floating point is used only for chart geometry. The video rounds
tables to two places and weekly bar labels to whole kcal; full precision remains
in `media/demo-data.json`.

| Time | Demonstration and recorded example |
| --- | --- |
| 0–8 s | Seven daily results; Monday 2,399.67 kcal and 136.79 g protein |
| 8–17 s | Monday's 161 g raw rice allocates 120.75 g to Tuesday lunch and 40.25 g to Wednesday dinner |
| 17–26 s | A copied plan changes breakfast oats from 75 g to 100 g; each day gains 93.50 kcal and 2.75 g protein |
| 26–36 s | Prepared shopping for 3, 7 and 14 days, plus prepared/eaten comparison over a partial cycle |

The scenario never writes to the source plan. It is an explicitly chosen input
change, not target optimisation. Category fractions and the repeating schedule
come from `planning.py`. Seven-day rice totals are 613 g on both bases; the
three-day totals differ (271 g prepared and 269.75 g eaten) because consumption
includes earlier batches. All ingredient quantities for every period are saved,
even when the film only displays selected rows.

The food records' original raw/cooked states are retained. These are arithmetic
results from supplied records, not verified food labels or purchase weights.
Supplement units remain unresolved in the source dataset; the film states this
and does not present supplement counts as shopping recommendations. There is no
yield conversion, pack rounding, stock tracking or implemented optimisation.

## Validation

```bash
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
ffmpeg -v error -i docs/media/demo.mp4 -f null -
ffmpeg -v error -i docs/media/preview.gif -f null -
```

The completed run passed 29 tests, Ruff lint and formatting. Recording tests
check the CLI's displayed daily totals, independent expected oats deltas,
allocation conservation, full-cycle prepared/eaten equality, fortnight scaling
and source-file isolation. Representative encoded frames were inspected across
all chapters for readability, units and clipping. The calculation JSON is
deterministic; video bytes can differ with FFmpeg or font versions.
