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


# Pull data from the worksheet
df = spy.pull(worksheet_url, start=start, end=end, grid=grid)

# Check pulled column names if needed
print(df.columns.tolist())

# Keep only inlet pressure and build result table
result = df[[inlet_col]].copy()

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
