# Coding conventions

- Use Python 3.10-compatible syntax, four-space indentation, `snake_case`
  functions and variables, and `UPPER_CASE` constants.
- Let Ruff handle formatting at 88 columns and import ordering: standard
  library, third-party packages, then local modules. Keep two blank lines
  between module-level definitions.
- Prefer readable names and straightforward code. Use comments to explain
  assumptions, units and decisions; avoid restating obvious operations.
- Give public functions concise docstrings and useful type annotations.
  Keep dictionaries for the JSON food and meal data.
- Use `Decimal` for quantities, nutrient values and allocation fractions.
  Round for display rather than during calculations.
- Keep calculations separate from printing. Reject invalid input with clear
  errors instead of silently substituting missing values.
- Keep formatting changes separate from changes to calculation behaviour.

Run these checks before committing:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Use `uv run ruff format .` to apply formatting. Ruff checks imports, unused code
and basic errors; there is no requirement to annotate every helper or test.
