"""Render actual meal-plan calculations and an optional portion proposal."""

import argparse
from pathlib import Path

from demo_reports import record_walkthrough
from demo_style import (
    AMBER,
    BLUE,
    GRID,
    INK,
    MUTED,
    TEAL,
    base,
    ease,
    encode,
    label,
    metric,
    panel,
    preview,
    save_data,
    text,
)

DURATION = 89
CHAPTERS = [
    (0, "Daily intake"),
    (8, "Batch meals"),
    (17, "Edit a meal"),
    (26, "Shopping"),
    (37, "Targets"),
    (50, "Powder"),
    (61, "Portion rules"),
    (74, "Proposal"),
]


def targets_frame(draw, data):
    panel(draw, (80, 250, 1060, 917))
    panel(draw, (1100, 250, 1840, 917))
    label(draw, 120, 288, "Monday · example goals")
    for x, name in [
        (125, "Nutrient"),
        (463, "Actual"),
        (752, "Goal"),
        (1015, "Result"),
    ]:
        text(draw, (x, 378), name, 24, MUTED, anchor="lt" if x == 125 else "rt")
    for i, name in enumerate(("calories", "protein", "fibre", "salt")):
        row = data["monday_targets"][name]
        target = row["target"]
        unit = "kcal" if name == "calories" else "g"
        goal = {"minimum": "≥ ", "maximum": "≤ ", "aim": ""}[
            target["mode"]
        ] + f"{target['value']:g}"
        if target["tolerance"]:
            goal += f" ± {target['tolerance']:g}"
        y = 454 + i * 86
        text(draw, (125, y), name.title(), 30)
        text(
            draw,
            (463, y),
            f"{row['actual']:,.2f} {unit}",
            26,
            INK,
            mono=True,
            anchor="rt",
        )
        text(draw, (752, y), goal, 25, TEAL, mono=True, anchor="rt")
        text(draw, (1015, y), row["status"], 23, MUTED, anchor="rt")
        draw.line((125, y + 53, 1015, y + 53), fill=GRID)
    text(draw, (125, 844), "Targets can vary by exercise type.", 27, MUTED)
    label(draw, 1140, 288, "Where Monday’s protein came from", TEAL)
    for i, item in enumerate(data["protein_contributors"][:3]):
        y = 386 + i * 128
        text(draw, (1140, y), item["ingredient"].title(), 32)
        text(
            draw,
            (1798, y),
            f"{item['nutrients']['protein']:.2f} g",
            31,
            TEAL,
            mono=True,
            anchor="rt",
        )
        text(
            draw,
            (1140, y + 49),
            f"{item['quantity']:.2f} g eaten · {item['meal']} (from {item['source']})",
            23,
            MUTED,
        )
    text(draw, (1140, 835), "The CLI lists the five largest contributions.", 24, MUTED)


def powder_frame(draw, data):
    powder = data["tuesday_powder"]
    label(draw, 80, 270, "Tuesday · same plan, one optional ingredient")
    for x, name, key, colour in [
        (80, "Default plan", "default", BLUE),
        (980, "Extra powder selected", "selected", TEAL),
    ]:
        panel(draw, (x, 355, x + 860, 708))
        label(draw, x + 42, 400, name, colour)
        metric(
            draw,
            x + 42,
            489,
            f"{powder[key]['salt']:.2f} g",
            "salt in the full day",
            colour,
        )
    grams = powder["portion"]["electrolytes_powder"]
    delta = powder["selected"]["salt"] - powder["default"]["salt"]
    text(
        draw,
        (80, 778),
        f"Selecting Tuesday adds {grams} g of powder and {delta:.2f} g of salt on each Tuesday.",
        33,
    )
    text(
        draw,
        (80, 856),
        "The run-day tablet is already counted in both totals.",
        28,
        MUTED,
    )


def rules_frame(draw, data):
    proposal = data["proposal"]
    profile, rules = data["profile"], data["rules"]["adjustable"]
    day = proposal["days"]["monday"]
    targets = day["targets"]
    panel(draw, (80, 250, 925, 917))
    panel(draw, (965, 250, 1840, 917))
    label(draw, 123, 290, "Illustrative strength day", BLUE)
    metric(
        draw,
        123,
        365,
        f"{targets['calories']['value']:,.0f} kcal",
        "total daily budget, including exercise",
        BLUE,
    )
    y = 545
    for key in ("protein", "fat", "carbs"):
        text(draw, (125, y), key.title(), 29)
        text(
            draw,
            (868, y),
            f"{targets[key]['value']:.0f} g",
            31,
            TEAL,
            mono=True,
            anchor="rt",
        )
        y += 71
    text(draw, (125, 810), f"Example body weight {profile['weight_kg']} kg.", 27, MUTED)
    text(draw, (125, 858), "The profile supplies the macro assumptions.", 25, MUTED)
    label(draw, 1005, 290, "What the optimiser is allowed to change", TEAL)
    for y, title, detail in [
        (
            380,
            "Oats",
            f"{rules['oats']['min_g']}–{rules['oats']['max_g']} g in {rules['oats']['step_g']} g steps",
        ),
        (
            540,
            "Olive oil",
            f"Optional · zero or {rules['extra_virgin_olive_oil']['min_g']}–{rules['extra_virgin_olive_oil']['max_g']} g in {rules['extra_virgin_olive_oil']['step_g']} g steps",
        ),
        (
            700,
            "Eggs",
            f"Whole units · {rules['egg']['unit_g']} g per illustrative edible portion",
        ),
    ]:
        text(draw, (1005, y), title, 34, bold=True)
        text(draw, (1005, y + 62), detail, 27, MUTED)
    text(draw, (1005, 855), "Hard nutrient limits still apply to every day.", 25, AMBER)


def proposal_frame(draw, data):
    proposal = data["proposal"]
    panel(draw, (80, 250, 1060, 917))
    panel(draw, (1100, 250, 1840, 917))
    label(draw, 120, 295, "Stage 1 · minimise gaps outside target ranges", TEAL)
    before, after = (
        proposal["baseline_primary_objective_value"],
        proposal["primary_objective_value"],
    )
    metric(
        draw,
        120,
        369,
        f"{before:.2f}  →  {after:.2f}",
        "sum of normalised daily gaps",
        TEAL,
    )
    label(draw, 120, 560, "Stage 2 · minimise portion changes at that fit", BLUE)
    changes = sorted(
        proposal["changes"],
        key=lambda item: (-abs(item["delta_g"]), item["source"], item["food"]),
    )
    for i, item in enumerate(changes[:3]):
        y = 640 + i * 72
        text(draw, (120, y), f"{item['source'].title()} / {item['food']}", 28)
        text(
            draw,
            (1015, y),
            f"{item['before_g']:g} → {item['after_g']:g} g",
            28,
            BLUE,
            mono=True,
            anchor="rt",
        )
    label(draw, 1140, 295, "Read the proposal summary")
    gaps = sum(
        1
        for day in proposal["days"].values()
        for name, target in day["targets"].items()
        if not target["hard"] and day["target_deviations"][name]["outside_range"] > 0
    )
    metric(draw, 1140, 370, str(gaps), "daily soft targets still outside range", AMBER)
    oats = proposal["shopping"]["prepared"]["oats"]
    text(draw, (1140, 542), "Weekly oats to prepare", 30)
    text(
        draw,
        (1140, 606),
        f"{oats['before_g']:,.0f} → {oats['after_g']:,.0f} g",
        40,
        TEAL,
        bold=True,
    )
    text(draw, (1140, 710), "Review the JSON report and export", 27, MUTED)
    text(draw, (1140, 754), "a separate meals file to try the plan.", 27, MUTED)
    text(draw, (1140, 844), "--summary   --export-meals", 25, TEAL, mono=True)


def frame(t, data):
    section = max(i for i, (start, _) in enumerate(CHAPTERS) if t >= start)
    titles = [
        "What does each day of meals add up to?",
        "Prepared today. Eaten across days.",
        "Change one input. Recalculate.",
        "The same plan becomes a shopping list.",
        "Which targets did Monday meet?",
        "Choose the days that need extra powder.",
        "Give the optimiser a budget and portion rules.",
        "What would the proposed week change?",
    ]
    image, draw = base(
        "meal-plan-calc",
        2,
        titles[section],
        [
            "First run  /  uv run meal-plan-calc --report nutrition",
            "A repeating schedule carries prepared ingredients into the next two days.",
            "Edit an ingredient in a copy of meals.json to compare two plans.",
            "Use --shopping-basis prepared or --shopping-basis eaten for the same dates.",
            "uv run meal-plan-calc --days 1 --report targets --targets data/targets.example.json --contributors protein",
            "uv run meal-plan-calc --start-day tuesday --days 1 --report nutrition --sweaty tuesday",
            "data/profile.macros.example.json  /  data/portion-rules.example.json",
            "The optional optimiser writes a report. Read the portion changes, remaining gaps, and shopping totals.",
        ][section],
        CHAPTERS,
        t,
        DURATION,
        TEAL,
        "Illustrative food records and targets. Shopping uses recorded raw or cooked weights. Supplement units still need verification.",
    )
    if section == 0:
        panel(draw, (80, 250, 1210, 747))
        label(draw, 120, 282, "Daily intake · kcal")
        growth = 0.55 + 0.45 * ease(t / 2)
        highest = max(float(data["daily"][day]["calories"]) for day in data["days"])
        ceiling = max(500, ((highest + 499) // 500) * 500)
        for value in (0, ceiling / 3, ceiling * 2 / 3, ceiling):
            y = 650 - value / ceiling * 270
            draw.line((180, y, 1160, y), fill=GRID, width=1)
            text(draw, (160, y), f"{value:,.0f}", 20, MUTED, mono=True, anchor="rm")
        for i, day in enumerate(data["days"]):
            value = float(data["daily"][day]["calories"])
            x = 205 + i * 137
            top = 650 - value / ceiling * 270 * growth
            draw.rounded_rectangle(
                (x, top, x + 74, 650), radius=8, fill=TEAL if i == 0 else BLUE
            )
            text(
                draw,
                (x + 37, top - 28),
                f"{value:.0f}",
                21,
                INK,
                mono=True,
                anchor="mt",
            )
            text(draw, (x + 37, 680), day[:3].title(), 23, MUTED, anchor="mt")
        panel(draw, (1250, 250, 1840, 917))
        label(draw, 1290, 290, "Monday · calculated totals")
        daily = data["daily"]["monday"]
        metric(draw, 1290, 350, f"{daily['calories']:,.2f}", "kcal", TEAL)
        for i, (key, caption) in enumerate(
            [
                ("protein", "protein"),
                ("carbs", "carbohydrates"),
                ("fat", "fat"),
                ("fibre", "fibre"),
            ]
        ):
            y = 505 + i * 85
            text(draw, (1290, y), caption, 25, MUTED)
            text(
                draw, (1800, y), f"{daily[key]:.2f} g", 28, INK, mono=True, anchor="rt"
            )
        panel(draw, (80, 777, 1210, 917))
        label(draw, 120, 801, f"One contribution · {data['scenario']['ingredient']}")
        amount = data["scenario"]["before_g"]
        per_100 = data["example"]["per_100g"]["calories"]
        contribution = data["example"]["breakfast_contribution"]["calories"]
        text(
            draw,
            (120, 847),
            f"{amount} g × {per_100} kcal / 100 g = {contribution:.2f} kcal",
            32,
            TEAL,
            mono=True,
        )
    elif section == 1:
        rice = data["batch_allocation"]
        label(draw, 80, 260, "One ingredient traced through the repeating schedule")
        cards = [
            (
                80,
                f"{rice['prepared_day'].upper()} / PREPARE",
                f"{rice['prepared_g']} g",
                f"{rice['ingredient']} in prepared batch",
                BLUE,
            ),
            (
                690,
                f"{rice['lunch_day'].upper()} / LUNCH",
                f"{rice['lunch_g']:.2f} g",
                f"{rice['lunch_fraction']:.0%} of prepared {rice['ingredient']}",
                TEAL,
            ),
            (
                1300,
                f"{rice['dinner_day'].upper()} / DINNER",
                f"{rice['dinner_g']:.2f} g",
                f"remaining {1 - rice['lunch_fraction']:.0%}",
                AMBER,
            ),
        ]
        for i, (x, caption, value, sub, colour) in enumerate(cards):
            panel(draw, (x, 325, x + 540, 635))
            label(draw, x + 35, 363, caption, colour)
            metric(draw, x + 35, 425, value, sub, colour, size=48)
            if i < 2:
                text(draw, (x + 560, 450), "→", 42, MUTED)
        ratio = ease((t - 8) / 2)
        split = 80 + 1760 * float(rice["lunch_fraction"])
        draw.rounded_rectangle((80, 685, 1840, 728), radius=10, fill=GRID)
        draw.rounded_rectangle(
            (80, 685, 80 + (split - 80) * ratio, 728), radius=10, fill=TEAL
        )
        if ratio > 0:
            draw.rectangle(
                (split, 685, split + (1840 - split) * ratio, 728), fill=AMBER
            )
        text(
            draw,
            (80, 760),
            f"Lunch contribution: {rice['lunch']['calories']:.2f} kcal",
            30,
            TEAL,
        )
        text(
            draw,
            (1100, 760),
            f"Dinner: {rice['dinner']['calories']:.2f} kcal",
            30,
            AMBER,
        )
        text(
            draw,
            (80, 840),
            "Allocation applies to each nutrient using the ingredient’s category fraction.",
            30,
        )
        text(
            draw,
            (80, 888),
            "Lunch uses yesterday’s batch. Dinner uses the batch from two days earlier.",
            26,
            MUTED,
        )
    elif section == 2:
        baseline = data["daily"]["monday"]
        scenario = data["scenario"]
        changed = t >= 19
        panel(draw, (80, 250, 720, 917))
        label(draw, 120, 290, "Isolated example · breakfast")
        text(draw, (120, 356), f'"{scenario["ingredient"]}":', 38, MUTED, mono=True)
        text(
            draw,
            (360, 346),
            f'"{scenario["after_g"]}"' if changed else f'"{scenario["before_g"]}"',
            60,
            TEAL,
            mono=True,
            bold=True,
        )
        text(
            draw,
            (120, 450),
            f"{scenario['before_g']} g → {scenario['after_g']} g",
            40,
            TEAL,
        )
        text(draw, (120, 525), "The saved source plan is unchanged.", 26, MUTED)
        label(draw, 120, 628, "Every day gains")
        metric(
            draw,
            120,
            682,
            f"+{scenario['monday_delta']['calories']:.2f}",
            f"kcal from {scenario['after_g'] - scenario['before_g']} g more {scenario['ingredient']}",
            TEAL,
        )
        text(draw, (120, 842), "Only this breakfast portion changes.", 25, AMBER)
        panel(draw, (760, 250, 1840, 917))
        label(draw, 800, 290, "Monday · full day recalculated")
        text(
            draw,
            (1170, 350),
            f"{scenario['before_g']} g {scenario['ingredient']}",
            25,
            MUTED,
            anchor="rt",
        )
        text(
            draw,
            (1500, 350),
            f"{scenario['after_g']} g {scenario['ingredient']}",
            25,
            TEAL,
            anchor="rt",
        )
        text(draw, (1800, 350), "Change", 25, MUTED, anchor="rt")
        for i, (key, caption, unit) in enumerate(
            [
                ("calories", "Calories", "kcal"),
                ("protein", "Protein", "g"),
                ("carbs", "Carbs", "g"),
                ("fat", "Fat", "g"),
                ("fibre", "Fibre", "g"),
            ]
        ):
            y = 435 + i * 87
            draw.line((800, y + 54, 1800, y + 54), fill=GRID)
            text(draw, (800, y), caption, 27)
            text(
                draw,
                (1170, y),
                f"{baseline[key]:,.2f}",
                28,
                MUTED,
                mono=True,
                anchor="rt",
            )
            value = scenario["daily"]["monday"][key] if changed else baseline[key]
            text(draw, (1500, y), f"{value:,.2f}", 28, TEAL, mono=True, anchor="rt")
            text(
                draw,
                (1800, y),
                f"+{value - baseline[key]:.2f} {unit}",
                25,
                TEAL,
                mono=True,
                anchor="rt",
            )
    elif section == 3:
        panel(draw, (80, 250, 1210, 917))
        label(draw, 120, 288, "Selected shopping quantities · prepared basis")
        text(draw, (120, 340), "Ingredient / recorded state", 22, MUTED)
        for x, length in [(680, 3), (900, 7), (1160, 14)]:
            text(draw, (x, 340), f"{length} days", 24, TEAL, anchor="rt")
        for i, ingredient in enumerate(data["display_ingredients"]):
            y = 420 + i * 97
            text(draw, (120, y), ingredient.title(), 28)
            text(draw, (340, y + 4), data["units"][ingredient], 23, MUTED)
            for x, length in [(680, 3), (900, 7), (1160, 14)]:
                amount = data["shopping"][str(length)]["prepared"][ingredient]
                text(
                    draw,
                    (x, y),
                    f"{amount:,.0f} g",
                    28,
                    TEAL if length == 7 else INK,
                    mono=True,
                    anchor="rt",
                )
            draw.line((120, y + 56, 1170, y + 56), fill=GRID)
        text(
            draw,
            (120, 840),
            "Periods begin Monday. Full output is saved as JSON.",
            26,
            MUTED,
        )
        panel(draw, (1250, 250, 1840, 917))
        label(draw, 1290, 290, "Prepared ≠ eaten · partial week")
        tracked = data["batch_allocation"]["ingredient"]
        text(draw, (1290, 355), f"{tracked.title()} / Monday–Wednesday", 29)
        amounts = data["shopping"]["3"]
        metric(
            draw,
            1290,
            430,
            f"{amounts['prepared'].get(tracked, 0):.2f} g",
            "prepared during those three days",
            BLUE,
            size=46,
        )
        metric(
            draw,
            1290,
            585,
            f"{amounts['eaten'].get(tracked, 0):.2f} g",
            "eaten, including earlier batches",
            AMBER,
            size=46,
        )
        text(draw, (1290, 760), "Over the full 7-day cycle:", 26, MUTED)
        weekly = data["shopping"]["7"]["prepared"][tracked]
        text(draw, (1290, 805), f"both total {weekly:.2f} g of {tracked}.", 28, TEAL)
    elif section == 4:
        targets_frame(draw, data)
    elif section == 5:
        powder_frame(draw, data)
    elif section == 6:
        rules_frame(draw, data)
    else:
        proposal_frame(draw, data)
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("docs/media"))
    parser.add_argument("--stills-only", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = record_walkthrough(Path(__file__).resolve().parents[1] / "data")
    save_data(args.output_dir / "demo-data.json", data)
    if args.stills_only:
        for start, _ in CHAPTERS:
            t = start + 4
            frame(t, data).save(args.output_dir / f"frame-{t}.png")
        return
    encode(lambda t: frame(t, data), args.output_dir / "demo.mp4", DURATION, CHAPTERS)
    preview(args.output_dir / "demo.mp4", args.output_dir / "preview.gif", 0, 8)


if __name__ == "__main__":
    main()
