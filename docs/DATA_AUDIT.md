# Food records: evidence still to collect

The 76 records in `data/foods.json` pass the calculator's structural checks. Their
product labels, measured serving masses, and preparation states have not been
independently verified. No nutrient values were changed during this review.

[food-data-audit.csv](food-data-audit.csv) inventories every current food key,
product description, and recorded state. All rows start as `pending`: this is an
evidence register, not a completed label audit. The calculator does not read it.

## Check these records first

| Records | What the repository shows | Evidence needed |
|---|---|---|
| `vitamin_d3_and_k2`, `zinc`, `omega_3`, `magnesium_glycinate` | Quantity `1` in the supplements meal, interpreted as 1 g; all eight nutrients recorded as zero | Exact product label, units taken, edible mass per capsule/tablet, and any tracked nutrient contribution. In particular, check the oil product's energy/fat. |
| `chicken`, `beef`, `salmon` | Product names describe fresh products; records say cooked | Confirm whether nutrient values are for the product as sold or cooked, and whether portions were weighed in that same state. A product name does not resolve this. |
| `mackerel`, `lentils`, `chickpeas` | Packaged/canned or ready-to-eat descriptions; records say raw | Define as-sold, drained, or prepared basis explicitly. Confirm the nutrient denominator and the actual weight used. |
| `milk`, oils, vinegars | All quantities are treated as grams | Check whether labels use 100 ml or 100 g. If conversion is needed, record measured or sourced density; do not silently equate ml and g. |
| `quinoa`, `grains`, `pasta` | Records say cooked | Verify that label basis and weighed portions both refer to the ready-to-eat/cooked product. |
| `electrolytes_powder`, `electrolytes_tablet` | Powder portion and tablet weights are configured; powder values are estimates | Exact serving mass, salt/sodium label basis and unit conversion. Preserve explicit day selection. |
| `egg` | The example optimiser uses 70 g per unit | Confirm edible weight, excluding shell, for the actual eggs used; the example conversion is illustrative. |

These are questions to resolve, not confirmed nutritional errors. The eight
tracked nutrients do not cover vitamin or mineral adequacy.

## Completing a row

Record a source URL or label reference, the date actually checked, label basis
(for example per 100 g as sold), portion basis/state, measured unit mass where
needed, and notes. Keep private photographs locally if desired; record a useful
reference without including personal information. Replace `pending` with
`verified` only after reconciling the source with the JSON values and quantities.
If evidence is unavailable, use `unresolved` with the reason; never substitute
guessed values or mark a product description as label verification.

For each correction, retain the old/new values and reason in the commit or PR.
Re-run nutrition, shopping, and optimiser examples and explain changed totals.
Add a regression check if a correction exposes a calculation or unit-conversion
bug. Keep the inventory aligned when ingredients are added or renamed.

## Next modelling work

After this audit, define cooking yield separately from nutrient basis, then add
pack rounding and stock. Distinguish consumed grams, prepared grams, and purchased
grams. The current repeating schedule assumes previous batches already exist;
starting without carryover needs an explicit initial-stock model.
