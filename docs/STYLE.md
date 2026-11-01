# Shared Python coding standard

Use Python 3.10-compatible syntax, four-space indentation, snake_case functions
and variables, CapWords classes and UPPER_CASE constants. Keep two blank lines
between module-level definitions; let Ruff format collections, expressions and
signatures at 88 columns rather than hand-aligning them. Preserve blank lines
that separate different ideas inside a function, not every statement.

Use explicit imports grouped as standard library, third party and local modules.
Rendering now names its Manim imports, making the source of constants/classes
visible. Avoid unused placeholder imports and modules with no responsibilities.

Use concise imperative docstrings for public behaviour and document units,
mutation, error behaviour and mathematical assumptions where those matter.
Comments should explain why, constraints, or conventions; avoid narrating obvious
assignments. Use ordinary sentences and consistent capitalisation. Do not add
docstrings or annotations to every trivial test/helper just to satisfy a rule.

Annotate public boundaries and non-obvious result structures when useful.
Use small dataclasses for search/backtest results with several related fields;
retain dictionaries for the existing JSON food format. Nutrition uses Decimal
because decimal quantities are part of its data contract; financial time-series
analysis uses binary float and tolerance-based tests. These differences are
intentional. Do not silently mix them or use Decimal for all scientific work.

Validate at external boundaries, fail with informative ValueError/TypeError,
and keep calculation functions independent of printing. CLI argument errors
produce exit code 2. Never silently fill unknown food nutrients, market prices
or unsupported cube state. A bounded-search failure is not proof of unsolvability.

Tooling is shared: Ruff 0.14.3, Python target py310, 88 columns, import sorting,
syntax/undefined-name/unused-code checks (E4/E7/E9/F/I). There is no mandatory
all-annotations policy, docstring linter, broad rewrite or new type-checking gate.

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Formatting/import cleanup was committed separately before behavioural work.
Keep future formatting changes separate from correctness/algorithm commits too.
