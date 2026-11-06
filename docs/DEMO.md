# Portfolio video: reproduction and verification

The README embeds an **eight-second looping GIF** (`docs/media/preview.gif`) linked to the complete **36-second, silent 1080p MP4** (`docs/media/demo.mp4`).

The committed media shows a **snapshot** of the supplied meal plan when the video was produced. Regenerating the video uses the **current** `data/foods.json` and `data/meals.json`; changing those files does not retroactively update the committed MP4 or GIF.

## Generate

From the repository root, with Python 3.10 and [uv](https://docs.astral.sh/uv/):

```bash
uv sync --locked --extra demo
uv run --locked --extra demo python scripts/render_demo.py
```

Install FFmpeg with H.264 support and DejaVu fonts (Ubuntu: `ffmpeg`, `fonts-dejavu-core`). The optional `demo` extra installs Pillow; normal calculations do not require it. Rendering is CPU-based and needs no graphics display or external data.

Use `--output-dir /path/to/output` for another destination. To inspect chapter layouts without video encoding:

```bash
uv run --locked --extra demo python scripts/render_demo.py --stills-only --output-dir /tmp/meal-demo-stills
```

## What the film demonstrates

| Time | Content |
| --- | --- |
| 0–8 s | Daily nutrient totals and one breakfast ingredient's contribution |
| 8–17 s | Allocation of a prepared carbohydrate batch to later meals |
| 17–26 s | Change one breakfast quantity by 25 g in a copy of the plan |
| 26–36 s | Compare 3-, 7- and 14-day prepared/eaten shopping quantities |

`meal_plan_calc.demo_data.build_demo()` loads and validates the current data and calls the production nutrition and shopping functions. The scenario is calculated from a deep copy without modifying the input files. It uses oats and Monday's rice when present, or other suitable ingredients otherwise.

The recorder retains full-precision `Decimal` values (as strings) and SHA-256 checksums in `docs/media/demo-data.json`. Floating point is used only for plotting; displayed values are rounded. The renderer does not implement a separate nutrition engine or an optimisation algorithm.

Category allocation follows `planning.py`. Prepared and eaten quantities agree across a complete schedule cycle but can differ for partial periods. Raw/cooked units are preserved; cooking-yield conversion, stock, packaging and supplement-unit verification are not implemented.

## Validate

```bash
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked --extra demo python scripts/render_demo.py --stills-only --output-dir /tmp/meal-demo-stills
ffmpeg -v error -i docs/media/demo.mp4 -f null -
ffmpeg -v error -i docs/media/preview.gif -f null -
```

The test suite checks changes to source ingredients, quantities and nutrient values, as well as source-file isolation, shopping conservation and CLI agreement. The still-frame command verifies rendering paths without generating a new MP4.

**When updating the media:** regenerate and commit the MP4, GIF and data recording together. The README's MP4 link is pinned to a media commit; update it when the MP4 changes. Media bytes may vary with FFmpeg and font versions.
