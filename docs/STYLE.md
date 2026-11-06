# Coding conventions

These conventions favour clear calculations and dependable input handling.

## Python

- Target Python 3.10; use four-space indentation and Ruff's 88-character formatting.
- Use `snake_case` for names and `UPPER_CASE` for constants. Let Ruff organise imports.
- Use concise public docstrings and type annotations where they clarify interfaces.
- Keep calculations separate from CLI output. Prefer simple functions to unnecessary abstractions.

## Numerical and data rules

- Use `Decimal` for food quantities, nutrient values and allocation fractions.
- Round only for display, not during calculations.
- Validate external JSON data and report malformed values rather than substituting guesses.
- Explain non-obvious units, schedule behaviour and assumptions in comments; avoid narrating straightforward code.

## Checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Apply formatting with `uv run ruff format .`. Keep purely cosmetic edits separate from calculation changes when practical.
