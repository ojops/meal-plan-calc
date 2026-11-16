"""Readable summaries of audited proposals, without changing their quantities."""

from decimal import Decimal


def number(value, *, signed=False):
    value = Decimal(str(value))
    if value and abs(value) < Decimal("0.01"):
        return format(value, "+.2E" if signed else ".2E")
    return format(value, "+.2f" if signed else ".2f")


def proposal_summary(report, *, limit=5):
    """Summarise the in-memory report or its saved JSON equivalent."""
    if type(limit) is not int or limit < 1:
        raise ValueError("Summary limit must be a positive integer")
    if report["status"] != "optimal":
        return "\n".join(
            [
                "No accepted meal plan.",
                report.get("message", report["status"]),
                report.get("guidance", "Inspect the solver stages in the JSON report."),
            ]
        )
    lines = [
        f"Proposal for one repeating cycle ({len(report['days'])} days).",
        "Target-range deviation (sum of normalised gaps): "
        f"{number(report['baseline_primary_objective_value'])} -> "
        f"{number(report['primary_objective_value'])}",
        "Largest source-portion changes (prepared batch or shared meal grams):",
    ]

    def show(items):
        lines.extend(items[:limit] or ["  None."])
        if len(items) > limit:
            lines.append(f"  ... {len(items) - limit} more in the JSON report.")

    changes = sorted(
        report["changes"],
        key=lambda item: (
            -abs(Decimal(str(item["delta_g"]))),
            item["source"],
            item["food"],
        ),
    )
    show(
        [
            f"  {item['source']} / {item['food']}: {number(item['before_g'])} -> "
            f"{number(item['after_g'])} g ({number(item['delta_g'], signed=True)} g)"
            for item in changes
        ]
    )
    gaps = []
    for day, values in report["days"].items():
        for nutrient, target in values["targets"].items():
            gap = Decimal(str(values["target_deviations"][nutrient]["outside_range"]))
            if target["hard"] or gap <= 0:
                continue
            relative = gap / max(Decimal(str(target["value"])), Decimal(1))
            unit = "kcal" if nutrient == "calories" else "g"
            centre = Decimal(str(target["value"]))
            tolerance = Decimal(str(target["tolerance"]))
            bounds = (
                f"{number(centre - tolerance)} to {number(centre + tolerance)}"
                if target["mode"] == "aim"
                else f"at least {number(centre - tolerance)}"
                if target["mode"] == "minimum"
                else f"at most {number(centre + tolerance)}"
            )
            gaps.append(
                (
                    relative,
                    f"  {day} / {nutrient}: {number(values['proposed'][nutrient])} "
                    f"{unit}; target {bounds} {unit}; outside by {number(gap)} {unit}",
                )
            )
    lines.append(
        f"Remaining soft target gaps: {len(gaps)} (largest proportional gaps first)."
    )
    show([line for _, line in sorted(gaps, key=lambda item: (-item[0], item[1]))])
    for basis in ("prepared", "eaten"):
        items = sorted(
            report["shopping"][basis].items(),
            key=lambda item: (-abs(Decimal(str(item[1]["delta_g"]))), item[0]),
        )
        lines.append(
            f"Largest shopping changes ({basis}, full cycle; recorded food states):"
        )
        show(
            [
                f"  {food} [{item['state']}]: {number(item['before_g'])} -> "
                f"{number(item['after_g'])} g ({number(item['delta_g'], signed=True)} g)"
                for food, item in items
                if abs(Decimal(str(item["delta_g"]))) > Decimal("0.000001")
            ]
        )
    lines.append(
        "Shopping quantities exclude cooking-yield, pack-size and stock conversions."
    )
    lines.append(
        "Optimal refers to the configured model; soft targets can remain unmet."
    )
    return "\n".join(lines)
