# Calculation and data contracts

For ingredient i with quantity q_i grams, nutrient rate n_i per 100 g, and
allocated fraction f_i, its contribution is n_i*q_i*f_i/100. Meal totals sum these
contributions. Fat includes saturates; carbohydrate includes sugars; fibre is
separate. The stored calories are used directly rather than reconstructed from
macronutrients: labelling systems, fibre, alcohol and rounding may differ.

Input decimal strings (and JSON numeric literals loaded with parse_float=Decimal)
avoid an intermediate binary-float rounding step. Public functions still accept
ordinary numbers using Decimal(str(value)). Repeating rational fractions such
as 2/3 are rounded by the active Decimal context (default 28 significant digits),
not represented as exact rationals. Intermediate totals are not rounded to cents;
only display is rounded. This is amply precise for the supplied food labels.

Originally, a missing category fraction defaulted to one for lunch, and dinner's
complement dictionary omitted that category, causing dinner to default to one
as well. A 100 kcal batch could therefore contribute 200 kcal. Shared
`allocation_fractions` now builds a value for each category in the meal, using
one for missing lunch fractions and zero for the corresponding dinner fraction.
Both nutrition and eaten-quantity reports use the same allocation generator.

A repeating week with all batches consumed satisfies mass conservation:
sum of eaten quantities = sum of prepared quantities. The regression test checks
both quantities and all nutrient totals over the actual supplied week, using
1e-20 absolute tolerance for Decimal division effects. This is an internal
consistency test, not independent verification of food values.

Validation is intentionally small and local: numeric finiteness, non-negativity,
fraction limits, known food references, complete nutrient fields and component
relationships. Missing information is not silently converted to zero. Metadata
(`link`, `comment`, `instore_name`) do not affect calculations. Data source links
and raw/cooked labels have not been independently verified; many records have
no link. Some supplements appear to be counted by capsule/tablet while reports
assume grams. These need explicit units and conversion data supplied by the user,
not guessed changes to quantities or nutrition values.

Before adding optimisation, define whether objectives target consumption or
preparation, introduce verified units/yields, and choose constraints. A linear
nutrient-target model with bounds and a weighted absolute-deviation objective
would be a useful first mathematical proposal. Taste, practical portion sizes,
cost and nutrition tolerances need explicit decisions first. No optimiser or
medical/dietary recommendation is currently implemented.
