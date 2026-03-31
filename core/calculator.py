# --SECTION 1-- IMPORTS

from core.config import (
    DEFAULT_INLET_PRESSURE,
    HIGH_RPM_MIN,
    HIGH_RPM_MAX,
    LOW_RPM_MIN,
    LOW_RPM_MAX,
    HIGH_A,
    HIGH_B,
    LOW_A,
    LOW_B,
    SCALE,
)


# --SECTION 2-- HELPER FUNCTIONS

def _validate_positive_number(value, field_name):
    try:
        num = float(value)
    except Exception:
        raise ValueError(f"{field_name} must be a valid number.")

    if num <= 0:
        raise ValueError(f"{field_name} must be greater than 0.")

    return num


def _base_high_capacity(x):
    return (HIGH_A * x) - HIGH_B


def _base_low_capacity(x):
    return (LOW_A * x) - LOW_B


def _safe_round(value, digits=4):
    return round(float(value), digits)


# --SECTION 3-- CORE SOLVER

def calculate_compressor_plan(target_production, inlet_pressure=DEFAULT_INLET_PRESSURE):
    """
    Logic:
    - 1 high + 1 low compressor
    - same load ratio:
        high_rpm / HIGH_RPM_MAX = low_rpm / LOW_RPM_MAX = load_ratio
    - total production:
        target = high_y + low_y

    high_y = ((0.3173*x) - 0.0948) * (high_rpm / 1000) * 1e6
    low_y  = ((0.1305*x) - 0.0350) * (low_rpm / 1180) * 1e6

    Since same load ratio:
        high_rpm = load_ratio * 1000
        low_rpm  = load_ratio * 1180

    So:
        target = [((0.3173*x) - 0.0948) + ((0.1305*x) - 0.0350)] * load_ratio * 1e6
    """

    target = _validate_positive_number(target_production, "Target Production")
    x = _validate_positive_number(inlet_pressure, "Inlet Pressure")

    high_base = _base_high_capacity(x)
    low_base = _base_low_capacity(x)

    if high_base <= 0:
        raise ValueError(
            f"At inlet pressure {x}, high compressor base capacity becomes non-positive. Check formula/input."
        )

    if low_base <= 0:
        raise ValueError(
            f"At inlet pressure {x}, low compressor base capacity becomes non-positive. Check formula/input."
        )

    total_base = high_base + low_base
    theoretical_load_ratio = target / (total_base * SCALE)

    high_min_load_ratio = HIGH_RPM_MIN / HIGH_RPM_MAX
    high_max_load_ratio = HIGH_RPM_MAX / HIGH_RPM_MAX

    low_min_load_ratio = LOW_RPM_MIN / LOW_RPM_MAX
    low_max_load_ratio = LOW_RPM_MAX / LOW_RPM_MAX

    # Same load ratio rule
    common_min_load_ratio = max(high_min_load_ratio, low_min_load_ratio)
    common_max_load_ratio = min(high_max_load_ratio, low_max_load_ratio)

    load_ratio = theoretical_load_ratio
    status = "OK"
    message = "Required RPM calculated from the entered target."

    if theoretical_load_ratio < common_min_load_ratio:
        status = "BELOW_MIN_LIMIT"
        message = (
            "Required RPM calculated from target, but this operating point is below the machine minimum RPM limit."
        )
    elif theoretical_load_ratio > common_max_load_ratio:
        status = "ABOVE_MAX_LIMIT"
        message = (
            "Required RPM calculated from target, but this operating point is above the machine maximum RPM limit."
        )

    high_rpm = load_ratio * HIGH_RPM_MAX
    low_rpm = load_ratio * LOW_RPM_MAX

    high_y = high_base * load_ratio * SCALE
    low_y = low_base * load_ratio * SCALE
    total_y = high_y + low_y

    result = {
        "status": status,
        "message": message,

        "input_target_production": _safe_round(target, 2),
        "input_inlet_pressure": _safe_round(x, 4),

        "load_ratio": _safe_round(load_ratio, 6),
        "load_ratio_percent": _safe_round(load_ratio * 100, 2),

        "high_rpm": _safe_round(high_rpm, 2),
        "low_rpm": _safe_round(low_rpm, 2),

        "high_capacity": _safe_round(high_y, 2),
        "low_capacity": _safe_round(low_y, 2),
        "total_capacity": _safe_round(total_y, 2),

        "high_capacity_share_percent": _safe_round((high_y / total_y) * 100, 2) if total_y > 0 else 0.0,
        "low_capacity_share_percent": _safe_round((low_y / total_y) * 100, 2) if total_y > 0 else 0.0,

        "min_possible_total_capacity": _safe_round(total_base * common_min_load_ratio * SCALE, 2),
        "max_possible_total_capacity": _safe_round(total_base * common_max_load_ratio * SCALE, 2),

        "high_formula_base": _safe_round(high_base, 6),
        "low_formula_base": _safe_round(low_base, 6),
    }

    return result
