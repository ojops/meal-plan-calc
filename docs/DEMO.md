# Portfolio video: reproduction and verification

The README embeds an **eight-second looping GIF** (`docs/media/preview.gif`) linked to the complete **36-second, silent 1080p MP4** (`docs/media/demo.mp4`).

The recording is a historical meal-plan snapshot. It predates the cooked-state
correction for quinoa and grains, and includes 6 g of powder on every run day.
Current demo generation reads the current food and meal files with no optional
powder selected. Run-day salt is therefore 0.78 g lower, with corresponding changes
to the other powder nutrients. Regenerated results and input hashes need not match
the recording. Targets and contribution reports are CLI features outside the film.

## Generate

From the repository root, with Python 3.10 and [uv](https://docs.astral.sh/uv/):

```bash
uv sync --locked --extra demo
uv run --locked --extra demo python scripts/render_demo.py
```

Install FFmpeg with H.264 support and DejaVu fonts (Ubuntu: `ffmpeg`, `fonts-dejavu-core`). The optional `demo` extra installs Pillow. Normal calculations do not require it. Rendering is CPU-based and needs no graphics display or external data.

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
| 26–36 s | Compare 3-, 7-, and 14-day prepared/eaten shopping quantities |

`meal_plan_calc.demo_data.build_demo()` loads and validates the current data and calls the production nutrition and shopping functions. The scenario is calculated from a deep copy without modifying the input files. It uses oats and Monday's rice when present, or other suitable ingredients otherwise.

The recorder retains full-precision `Decimal` values (as strings) and SHA-256 checksums in `docs/media/demo-data.json`. Floating point is used only for plotting. Displayed values are rounded. The renderer does not implement a separate nutrition engine or an optimisation algorithm.

See [calculation notes](CALCULATIONS.md) for batch allocation, shopping bases, units, and input-data limitations.

## Validate

```bash
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked --extra demo python scripts/render_demo.py --stills-only --output-dir /tmp/meal-demo-stills
ffmpeg -v error -i docs/media/demo.mp4 -f null -
ffmpeg -v error -i docs/media/preview.gif -f null -
```

Tests cover changed ingredients, quantities, and nutrient values, plus input isolation, shopping conservation, and CLI agreement. The still-frame command checks rendering without generating a new MP4.

**When updating the media:** regenerate and commit the MP4, GIF, and data recording together. The README's MP4 link is pinned to a media commit. Update it when the MP4 changes. Media bytes may vary with FFmpeg and font versions.
