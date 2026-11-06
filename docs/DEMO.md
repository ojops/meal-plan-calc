# Reproducing the portfolio demonstration

`media/demo.mp4` is a 36-second silent film, 1920 × 1080 at 30 FPS,
encoded as H.264/yuv420p with fast-start metadata. `media/preview.gif` loops the opening eight seconds at 768 × 432 and 10 FPS.
The full-length MP4 remains available from the README.

Both media files are tracked in Git. The animation uses a relative link;
the MP4 link uses a raw GitHub URL pinned to its media commit to avoid
branch-dependent redirects. When regenerating and committing a new MP4,
update the pinned README links to that commit. The link opens or downloads
the MP4 depending on the browser; the README animation itself has no
play/pause controls. No external hosting service is required.

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
| 0–8 s | Current seven-day nutrition totals and a breakfast ingredient contribution |
| 8–17 s | Trace a recorded carbohydrate batch into later lunch/dinner servings |
| 17–26 s | Increase a breakfast ingredient by 25 g in an isolated copy and recalculate |
| 26–36 s | Compare current 3-, 7- and 14-day prepared/eaten shopping totals |

The scenario derives baseline amounts and nutrient differences from the current
input files without modifying the saved plan. If oats are absent, another
breakfast ingredient is used; if Monday's rice is absent, a different prepared
carbohydrate is traced. It is a demonstration, not target optimisation.

Category fractions and the repeating schedule come from `planning.py`. Prepared
and eaten shopping totals agree over a complete cycle but may differ over a
partial cycle because consumption includes earlier batches. Full quantities for
each period are recorded even when only selected rows appear in the film.

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

The original video and GIF were validated by full FFmpeg decoding. The shorter
preview is the verified eight-second excerpt of that same video. Current tests
check CLI agreement, dynamic input changes, allocation conservation, full-cycle
shopping, fortnight scaling and source-file isolation. Regeneration can be
checked without encoding using the still-frame command above. The calculation JSON is
deterministic; video bytes can differ with FFmpeg or font versions.
