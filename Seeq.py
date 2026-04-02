import pandas as pd
from seeq import spy

spy.options.compatibility = 200

# Paste your Seeq worksheet URL here
worksheet_url = "PASTE_YOUR_FULL_WORKSHEET_URL_HERE"

# Set time range and target production
start = "2026-03-20 00:00:00"
end = "2026-03-21 00:00:00"
grid = "1min"
target_production = 40000.0

# Use the exact signal name from your worksheet
inlet_col = "Inlet Pressure"

HIGH_RPM_MIN = 800.0
HIGH_RPM_MAX = 1000.0
LOW_RPM_MIN = 800.0
LOW_RPM_MAX = 1180.0
SCALE = 10**6


def calculate_rpm(target, inlet_pressure):
    if pd.isna(inlet_pressure):
        return None, None, "MISSING_INLET_PRESSURE"

    x = float(inlet_pressure)

    high_base = (0.3173 * x) - 0.0948
    low_base = (0.1305 * x) - 0.0350

    if high_base <= 0 or low_base <= 0:
        return None, None, "INVALID_INLET_PRESSURE"

    load_ratio = float(target) / ((high_base + low_base) * SCALE)
    high_rpm = load_ratio * HIGH_RPM_MAX
    low_rpm = load_ratio * LOW_RPM_MAX

    status = "OK"
    if high_rpm < HIGH_RPM_MIN or low_rpm < LOW_RPM_MIN:
        status = "BELOW_MIN_LIMIT"
    elif high_rpm > HIGH_RPM_MAX or low_rpm > LOW_RPM_MAX:
        status = "ABOVE_MAX_LIMIT"

    return round(high_rpm, 2), round(low_rpm, 2), status


def resolve_column_name(columns, preferred_name):
    columns = list(columns)
    normalized_map = {str(col).strip().lower(): col for col in columns}
    preferred_normalized = preferred_name.strip().lower()
    search_terms = [
        preferred_normalized,
        "inlet pressure",
        "inlet pressur",
        "pressure inlet",
    ]

    if preferred_normalized in normalized_map:
        return normalized_map[preferred_normalized]

    for term in search_terms:
        partial_matches = [
            col for col in columns
            if term in str(col).strip().lower()
        ]
        if len(partial_matches) == 1:
            return partial_matches[0]

    token_groups = [
        preferred_normalized.split(),
        ["inlet", "pressure"],
        ["inlet", "pressur"],
    ]
    for tokens in token_groups:
        token_matches = [
            col for col in columns
            if all(token in str(col).strip().lower() for token in tokens)
        ]
        if len(token_matches) == 1:
            return token_matches[0]

    ranked_matches = sorted(
        columns,
        key=lambda col: (
            "inlet" not in str(col).strip().lower(),
            "press" not in str(col).strip().lower(),
            len(str(col))
        )
    )
    best_match = ranked_matches[0] if ranked_matches else None
    if best_match and "inlet" in str(best_match).strip().lower() and "press" in str(best_match).strip().lower():
        return best_match

    raise KeyError(
        f"Could not find a unique column for '{preferred_name}'. "
        f"Available columns: {list(columns)}"
    )


# Pull data from the worksheet
df = spy.pull(worksheet_url, start=start, end=end, grid=grid)

# Check pulled column names if needed
print(df.columns.tolist())

# Resolve the real column name from the worksheet output
resolved_inlet_col = resolve_column_name(df.columns, inlet_col)
print(f"Using inlet pressure column: {resolved_inlet_col}")

# Keep only inlet pressure and build result table
result = df[[resolved_inlet_col]].copy()
result = result.rename(columns={resolved_inlet_col: inlet_col})

# For each inlet pressure value, calculate required RPM
result["Required High RPM"] = result[inlet_col].apply(
    lambda x: calculate_rpm(target_production, x)[0]
)
result["Required Low RPM"] = result[inlet_col].apply(
    lambda x: calculate_rpm(target_production, x)[1]
)
result["RPM Status"] = result[inlet_col].apply(
    lambda x: calculate_rpm(target_production, x)[2]
)

# If fuel columns already exist on the worksheet, keep them for comparison
fuel_candidates = [
    "Fuel per second",
    "Predicted fuel per second",
    "Fuel consumption per day",
    "Predicted fuel per day",
]
for col in fuel_candidates:
    if col in df.columns:
        result[col] = df[col]

print(result.head())
result
