"""Two-stage HiGHS MILP with explicit quantity units and audited incumbents."""

from decimal import Decimal as D
from math import isfinite

PRIMARY_TOLERANCE = D("0.000001")
AUDIT_TOLERANCE = D("0.0000001")


def solve_portions(baseline, bounds, rules, rows, time_limit):
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, milp

    if isinstance(time_limit, bool) or not isfinite(time_limit) or time_limit <= 0:
        raise ValueError("time_limit must be finite and positive")
    n = len(baseline)
    units = [r["step"] or D(1) for r in rules]
    lower = [
        float(lo / step) if r["required"] else 0.0
        for (lo, _), step, r in zip(bounds, units, rules)
    ]
    upper = [float(hi / step) for (_, hi), step in zip(bounds, units)]
    integer = [int(r["step"] is not None) for r in rules]
    primary, secondary = [0.0] * n, [0.0] * n
    constraints = []

    def variable(cost1=0.0, cost2=0.0, max_value=float("inf"), integral=0):
        index = len(lower)
        lower.append(0.0)
        upper.append(max_value)
        integer.append(integral)
        primary.append(cost1)
        secondary.append(cost2)
        return index

    def constraint(coeff, bound):
        constraints.append((coeff, float(bound)))

    if n == 0:
        # A no-op exclusion can leave every food fixed; still assess target fit.
        variable(max_value=0)

    for label, vector, bound, penalty in rows:
        # Convert the Decimal gram-level model to solver quantity units once.
        scale = max(D(1), abs(bound), *(abs(c * u) for c, u in zip(vector, units)))
        coeff = {
            i: float(c * u / scale) for i, (c, u) in enumerate(zip(vector, units)) if c
        }
        if penalty is not None:
            slack = variable(cost1=float(penalty * scale))
            coeff[slack] = -1.0
        constraint(coeff, bound / scale)
    for i, (original, (lo, hi), unit, rule) in enumerate(
        zip(baseline, bounds, units, rules)
    ):
        if not rule["required"]:
            active = variable(max_value=1, integral=1)
            constraint({i: float(unit), active: -float(hi)}, 0)
            constraint({i: -float(unit), active: float(lo)}, 0)
        deviation = variable(cost2=1 / float(max(original, D(50))))
        constraint({i: float(unit), deviation: -1.0}, original)
        constraint({i: -float(unit), deviation: -1.0}, -original)

    def run(objective):
        matrix = np.zeros((len(constraints), len(lower)))
        for row, (coeff, _) in enumerate(constraints):
            for col, value in coeff.items():
                matrix[row, col] = value
        return milp(
            np.array(objective),
            integrality=np.array(integer),
            bounds=Bounds(lower, upper),
            constraints=LinearConstraint(matrix, -np.inf, [b for _, b in constraints]),
            options={"time_limit": time_limit, "mip_rel_gap": 0.0},
        )

    def info(result):
        return {
            "status": int(result.status),
            "message": result.message,
            "objective": float(result.fun) if result.fun is not None else None,
            "mip_gap": float(result.mip_gap)
            if getattr(result, "mip_gap", None) is not None and isfinite(result.mip_gap)
            else None,
            "dual_bound": float(result.mip_dual_bound)
            if getattr(result, "mip_dual_bound", None) is not None
            and isfinite(result.mip_dual_bound)
            else None,
            "time_limit_seconds": time_limit,
        }

    first = run(primary)
    stages = {"target_fit": info(first)}
    if first.status != 0:
        return None, stages
    optimum = max(D(0), D(str(first.fun)))
    constraint({i: c for i, c in enumerate(primary) if c}, optimum + PRIMARY_TOLERANCE)
    second = run(secondary)
    stages["baseline_change"] = info(second)
    if second.status != 0:
        return None, stages
    quantities = []
    for value, unit, rule, (lo, hi) in zip(second.x[:n], units, rules, bounds):
        if rule["step"] is not None:
            count = round(value)
            if abs(value - count) > 1e-5:
                raise ValueError("Solver returned a nonintegral portion count")
            x = D(count) * unit
        else:
            x = D(str(value))
            if abs(x) < AUDIT_TOLERANCE:
                x = D(0)
        if (
            x < -AUDIT_TOLERANCE
            or x > hi + AUDIT_TOLERANCE
            or ((rule["required"] or x != 0) and x < lo - AUDIT_TOLERANCE)
        ):
            raise ValueError("Final quantity violates required/optional portion bounds")
        quantities.append(x)
    audit, actual_primary = [], D(0)
    for label, vector, bound, penalty in rows:
        excess = max(
            D(0), sum((x * c for x, c in zip(quantities, vector)), D(0)) - bound
        )
        tolerance = AUDIT_TOLERANCE * max(D(1), abs(bound))
        if penalty is None and excess > tolerance:
            raise ValueError(f"Final plan failed hard constraint audit: {label}")
        if penalty is not None:
            actual_primary += penalty * excess
        audit.append(
            {
                "constraint": label,
                "hard": penalty is None,
                "violation": excess,
                "numerical_tolerance": tolerance,
            }
        )
    if actual_primary > optimum + PRIMARY_TOLERANCE + AUDIT_TOLERANCE:
        raise ValueError("Final portion reconstruction degraded the primary optimum")
    stages.update(
        primary_optimum=optimum,
        primary_actual=actual_primary,
        primary_preservation_tolerance=PRIMARY_TOLERANCE,
        constraint_audit=audit,
    )
    return quantities, stages
