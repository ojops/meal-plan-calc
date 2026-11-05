"""Render actual meal-plan calculations as a 36-second silent demonstration."""

import argparse
from pathlib import Path

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

from meal_plan_calc.demo_data import build_demo

DURATION = 36
CHAPTERS = [
    (0, "Calculate the week"),
    (8, "Allocate a batch"),
    (17, "Change one input"),
    (26, "Build a shopping list"),
]


def frame(t, data):
    section = 0 if t < 8 else 1 if t < 17 else 2 if t < 26 else 3
    titles = [
        "A meal plan becomes a calculation.",
        "Prepared today. Eaten across days.",
        "Change one input. Recalculate.",
        "The same plan becomes a shopping list.",
    ]
    image, draw = base(
        "meal-plan-calc",
        2,
        titles[section],
        "Structured JSON inputs  /  Decimal arithmetic  /  eight nutrients",
        CHAPTERS,
        t,
        DURATION,
        TEAL,
        "Supplied food records; supplement units need verification. Recorded raw/cooked grams; no yield or pack conversion.",
    )
    if section == 0:
        panel(draw, (80, 250, 1210, 747))
        label(draw, 120, 282, "Daily intake · kcal")
        growth = 0.55 + 0.45 * ease(t / 2)
        for value in (0, 1000, 2000, 3000):
            y = 650 - value / 3000 * 270
            draw.line((180, y, 1160, y), fill=GRID, width=1)
            text(draw, (160, y), str(value), 20, MUTED, mono=True, anchor="rm")
        for i, day in enumerate(data["days"]):
            value = float(data["daily"][day]["calories"])
            x = 205 + i * 137
            top = 650 - value / 3000 * 270 * growth
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
        label(draw, 120, 801, "One contribution · breakfast oats")
        amount = data["scenario"]["before_g"]
        per_100 = data["oats"]["per_100g"]["calories"]
        contribution = data["oats"]["breakfast_contribution"]["calories"]
        text(
            draw,
            (120, 847),
            f"{amount} g × {per_100} kcal / 100 g = {contribution:.2f} kcal",
            32,
            TEAL,
            mono=True,
        )
    elif section == 1:
        rice = data["rice_allocation"]
        label(draw, 80, 260, "One ingredient traced through the repeating schedule")
        cards = [
            (
                80,
                "MONDAY / PREPARE",
                f"{rice['prepared_g']} g",
                "raw rice in the cooked batch",
                BLUE,
            ),
            (
                690,
                "TUESDAY / LUNCH",
                f"{rice['lunch_g']:.2f} g",
                "75% of Monday’s rice",
                TEAL,
            ),
            (
                1300,
                "WEDNESDAY / DINNER",
                f"{rice['dinner_g']:.2f} g",
                "remaining 25%",
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
        draw.rounded_rectangle((80, 685, 1840, 728), radius=10, fill=GRID)
        draw.rounded_rectangle((80, 685, 80 + 1320 * ratio, 728), radius=10, fill=TEAL)
        if ratio > 0:
            draw.rectangle((1400, 685, 1400 + 440 * ratio, 728), fill=AMBER)
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
            "Lunch uses yesterday’s batch; dinner uses the batch from two days earlier.",
            26,
            MUTED,
        )
    elif section == 2:
        baseline = data["daily"]["monday"]
        scenario = data["scenario"]
        changed = t >= 19
        panel(draw, (80, 250, 720, 917))
        label(draw, 120, 290, "Isolated example · breakfast")
        text(draw, (120, 356), '"oats":', 38, MUTED, mono=True)
        text(
            draw,
            (360, 346),
            '"100"' if changed else '"75"',
            60,
            TEAL,
            mono=True,
            bold=True,
        )
        text(draw, (120, 450), "75 g → 100 g", 44, TEAL)
        text(draw, (120, 525), "The saved source plan is unchanged.", 26, MUTED)
        label(draw, 120, 628, "Every day gains")
        metric(
            draw,
            120,
            682,
            f"+{scenario['monday_delta']['calories']:.2f}",
            "kcal from 25 g more oats",
            TEAL,
        )
        text(draw, (120, 842), "Scenario analysis; no optimisation.", 25, AMBER)
        panel(draw, (760, 250, 1840, 917))
        label(draw, 800, 290, "Monday · full day recalculated")
        text(draw, (1170, 350), "75 g oats", 25, MUTED, anchor="rt")
        text(draw, (1500, 350), "100 g oats", 25, TEAL, anchor="rt")
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
    else:
        panel(draw, (80, 250, 1210, 917))
        label(draw, 120, 288, "Selected shopping quantities · prepared basis")
        text(draw, (120, 340), "Ingredient / recorded state", 22, MUTED)
        for x, length in [(680, 3), (900, 7), (1160, 14)]:
            text(draw, (x, 340), f"{length} days", 24, TEAL, anchor="rt")
        for i, ingredient in enumerate(["oats", "rice", "chicken", "broccoli"]):
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
        text(draw, (1290, 355), "Rice / Monday–Wednesday", 29)
        amounts = data["shopping"]["3"]
        metric(
            draw,
            1290,
            430,
            f"{amounts['prepared']['rice']:.2f} g",
            "prepared during those three days",
            BLUE,
            size=46,
        )
        metric(
            draw,
            1290,
            585,
            f"{amounts['eaten']['rice']:.2f} g",
            "eaten, including earlier batches",
            AMBER,
            size=46,
        )
        text(draw, (1290, 760), "Over the full 7-day cycle:", 26, MUTED)
        weekly = data["shopping"]["7"]["prepared"]["rice"]
        text(draw, (1290, 805), f"both total {weekly:.2f} g of rice.", 28, TEAL)
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("docs/media"))
    parser.add_argument("--stills-only", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = build_demo(Path(__file__).resolve().parents[1] / "data")
    save_data(args.output_dir / "demo-data.json", data)
    if args.stills_only:
        for t in (3, 12, 22, 31):
            frame(t, data).save(args.output_dir / f"frame-{t}.png")
        return
    encode(lambda t: frame(t, data), args.output_dir / "demo.mp4", DURATION)
    preview(args.output_dir / "demo.mp4", args.output_dir / "demo.gif", 0, DURATION)


if __name__ == "__main__":
    main()
