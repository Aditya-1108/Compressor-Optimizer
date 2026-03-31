import tkinter as tk
from tkinter import ttk, messagebox


APP_TITLE = "Compressor RPM Calculator"
WINDOW_WIDTH = 980
WINDOW_HEIGHT = 720

DEFAULT_INLET_PRESSURE = 1.1

HIGH_RPM_MIN = 800.0
HIGH_RPM_MAX = 1000.0

LOW_RPM_MIN = 800.0
LOW_RPM_MAX = 1180.0

HIGH_A = 0.3173
HIGH_B = 0.0948

LOW_A = 0.1305
LOW_B = 0.0350

SCALE = 10**6


def _validate_positive_number(value, field_name):
    try:
        num = float(value)
    except Exception:
        raise ValueError(f"{field_name} must be a valid number.")

    if num <= 0:
        raise ValueError(f"{field_name} must be greater than 0.")

    return num


def _safe_round(value, digits=4):
    return round(float(value), digits)


def calculate_compressor_plan(target_production, inlet_pressure=DEFAULT_INLET_PRESSURE):
    target = _validate_positive_number(target_production, "Target Production")
    x = _validate_positive_number(inlet_pressure, "Inlet Pressure")

    high_base = (HIGH_A * x) - HIGH_B
    low_base = (LOW_A * x) - LOW_B

    if high_base <= 0:
        raise ValueError(f"At inlet pressure {x}, high compressor base capacity becomes non-positive.")

    if low_base <= 0:
        raise ValueError(f"At inlet pressure {x}, low compressor base capacity becomes non-positive.")

    total_base = high_base + low_base
    load_ratio = target / (total_base * SCALE)

    high_rpm = load_ratio * HIGH_RPM_MAX
    low_rpm = load_ratio * LOW_RPM_MAX

    high_y = high_base * load_ratio * SCALE
    low_y = low_base * load_ratio * SCALE
    total_y = high_y + low_y

    status = "OK"
    message = "Required RPM calculated from the entered target."

    if high_rpm < HIGH_RPM_MIN or low_rpm < LOW_RPM_MIN:
        status = "BELOW_MIN_LIMIT"
        message = "Required RPM is below machine minimum."
    elif high_rpm > HIGH_RPM_MAX or low_rpm > LOW_RPM_MAX:
        status = "ABOVE_MAX_LIMIT"
        message = "Required RPM is above machine maximum."

    return {
        "status": status,
        "message": message,
        "input_target_production": _safe_round(target, 2),
        "input_inlet_pressure": _safe_round(x, 4),
        "load_ratio_percent": _safe_round(load_ratio * 100, 2),
        "high_rpm": _safe_round(high_rpm, 2),
        "low_rpm": _safe_round(low_rpm, 2),
        "high_capacity": _safe_round(high_y, 2),
        "low_capacity": _safe_round(low_y, 2),
        "total_capacity": _safe_round(total_y, 2),
    }


class CompressorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

        self.target_var = tk.StringVar()
        self.inlet_var = tk.StringVar(value=str(DEFAULT_INLET_PRESSURE))
        self.status_var = tk.StringVar(value="Ready")

        self._build_ui()

    def _add_result_row(self, parent, row_no, label_text, attr_name):
        ttk.Label(parent, text=label_text, font=("Segoe UI", 10, "bold")).grid(
            row=row_no, column=0, sticky="w", padx=(0, 20), pady=6
        )
        value_label = ttk.Label(parent, text="-", font=("Segoe UI", 10))
        value_label.grid(row=row_no, column=1, sticky="w", pady=6)
        setattr(self, attr_name, value_label)

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)

        ttk.Label(main, text="Compressor RPM Calculator", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        ttk.Label(main, text="Target se required high aur low RPM nikaalta hai.", font=("Segoe UI", 10)).grid(
            row=1, column=0, sticky="w", pady=(0, 12)
        )

        input_card = ttk.LabelFrame(main, text="Input", padding=12)
        input_card.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        input_card.columnconfigure(1, weight=1)

        ttk.Label(input_card, text="Target Production").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Entry(input_card, textvariable=self.target_var, width=30).grid(row=0, column=1, sticky="w", pady=6)

        ttk.Label(input_card, text="Inlet Pressure (bara)").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Entry(input_card, textvariable=self.inlet_var, width=30).grid(row=1, column=1, sticky="w", pady=6)

        button_row = ttk.Frame(input_card)
        button_row.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))
        ttk.Button(button_row, text="Calculate", command=self.calculate).pack(side="left")
        ttk.Button(button_row, text="Reset", command=self.reset).pack(side="left", padx=(8, 0))

        result_card = ttk.LabelFrame(main, text="Result", padding=12)
        result_card.grid(row=3, column=0, sticky="ew")
        result_card.columnconfigure(0, weight=1)
        result_card.columnconfigure(1, weight=1)

        self.summary_label = ttk.Label(result_card, text="Enter values and click Calculate.", font=("Segoe UI", 11, "bold"))
        self.summary_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        self._add_result_row(result_card, 1, "Target Production", "target_value")
        self._add_result_row(result_card, 2, "Inlet Pressure", "pressure_value")
        self._add_result_row(result_card, 3, "Required High RPM", "high_rpm_value")
        self._add_result_row(result_card, 4, "Required Low RPM", "low_rpm_value")
        self._add_result_row(result_card, 5, "High Capacity", "high_capacity_value")
        self._add_result_row(result_card, 6, "Low Capacity", "low_capacity_value")
        self._add_result_row(result_card, 7, "Total Capacity", "total_capacity_value")
        self._add_result_row(result_card, 8, "Load Ratio", "load_ratio_value")
        self._add_result_row(result_card, 9, "Operating Status", "operating_status_value")

        ttk.Label(main, textvariable=self.status_var).grid(row=4, column=0, sticky="w", pady=(10, 0))

    def reset(self):
        self.target_var.set("")
        self.inlet_var.set(str(DEFAULT_INLET_PRESSURE))
        self.summary_label.config(text="Enter values and click Calculate.")

        for attr in (
            "target_value",
            "pressure_value",
            "high_rpm_value",
            "low_rpm_value",
            "high_capacity_value",
            "low_capacity_value",
            "total_capacity_value",
            "load_ratio_value",
            "operating_status_value",
        ):
            getattr(self, attr).config(text="-")

        self.status_var.set("Ready")

    def calculate(self):
        try:
            result = calculate_compressor_plan(
                target_production=self.target_var.get().strip(),
                inlet_pressure=self.inlet_var.get().strip(),
            )
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            self.status_var.set("Error")
            return

        self.summary_label.config(
            text=(
                f"Required RPM for target {result['input_target_production']}: "
                f"High {result['high_rpm']} RPM | Low {result['low_rpm']} RPM. {result['message']}"
            )
        )

        self.target_value.config(text=f"{result['input_target_production']}")
        self.pressure_value.config(text=f"{result['input_inlet_pressure']} bara")
        self.high_rpm_value.config(text=f"{result['high_rpm']} RPM")
        self.low_rpm_value.config(text=f"{result['low_rpm']} RPM")
        self.high_capacity_value.config(text=f"{result['high_capacity']}")
        self.low_capacity_value.config(text=f"{result['low_capacity']}")
        self.total_capacity_value.config(text=f"{result['total_capacity']}")
        self.load_ratio_value.config(text=f"{result['load_ratio_percent']} %")
        self.operating_status_value.config(text=f"{result['status']}")
        self.status_var.set(result["status"])


def run_app():
    root = tk.Tk()
    app = CompressorApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_app()
