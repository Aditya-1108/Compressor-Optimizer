# --SECTION 1-- IMPORTS

from pathlib import Path
import textwrap


# --SECTION 2-- ROOT CONFIG

PROJECT_NAME = "compressor_optimizer_local"


# --SECTION 3-- FILE CONTENTS

MAIN_PY = r'''# --SECTION 1-- IMPORTS

from ui.app import run_app


# --SECTION 2-- ENTRY POINT

if __name__ == "__main__":
    run_app()
'''


CONFIG_PY = r'''# --SECTION 1-- APP CONFIG

APP_TITLE = "Compressor Optimizer - Local Offline Tool"
WINDOW_WIDTH = 980
WINDOW_HEIGHT = 720

DEFAULT_INLET_PRESSURE = 1.1

HIGH_RPM_MIN = 800.0
HIGH_RPM_MAX = 1000.0

LOW_RPM_MIN = 800.0
LOW_RPM_MAX = 1180.0


# --SECTION 2-- FORMULA CONSTANTS

HIGH_A = 0.3173
HIGH_B = 0.0948

LOW_A = 0.1305
LOW_B = 0.0350

SCALE = 10**6
'''


CALCULATOR_PY = r'''# --SECTION 1-- IMPORTS

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

    status = "OK"
    message = "Solution found within allowed limits."

    if theoretical_load_ratio < common_min_load_ratio:
        load_ratio = common_min_load_ratio
        status = "BELOW_MIN_LIMIT"
        message = (
            "Requested production is below the minimum achievable production "
            "under same-load-ratio and RPM lower-limit rule. Showing minimum possible operating point."
        )
    elif theoretical_load_ratio > common_max_load_ratio:
        load_ratio = common_max_load_ratio
        status = "ABOVE_MAX_LIMIT"
        message = (
            "Requested production is above the maximum achievable production "
            "under same-load-ratio and RPM upper-limit rule. Showing maximum possible operating point."
        )
    else:
        load_ratio = theoretical_load_ratio

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
'''


FUTURE_FUEL_PY = r'''# --SECTION 1-- PLACEHOLDER

def future_fuel_prediction_module():
    """
    Future scope:
    - Historical fuel data import
    - Production vs fuel relationship
    - Min / avg / max fuel prediction
    - Optional separate model for each compressor combination
    """
    return "Fuel prediction module reserved for future implementation."
'''


UI_APP_PY = r'''# --SECTION 1-- IMPORTS

import tkinter as tk
from tkinter import ttk, messagebox

from core.config import (
    APP_TITLE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    DEFAULT_INLET_PRESSURE,
)
from core.calculator import calculate_compressor_plan


# --SECTION 2-- SCROLLABLE FRAME

class ScrollableFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)

        self.inner = ttk.Frame(self.canvas)

        self.inner.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.canvas.configure(
            yscrollcommand=self.v_scroll.set,
            xscrollcommand=self.h_scroll.set
        )

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll.grid(row=1, column=0, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


# --SECTION 3-- MAIN APP

class CompressorOptimizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(900, 620)

        self.target_var = tk.StringVar()
        self.inlet_var = tk.StringVar(value=str(DEFAULT_INLET_PRESSURE))
        self.status_var = tk.StringVar(value="Ready")

        self._build_ui()

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill="both", expand=True)

        scroll = ScrollableFrame(outer)
        scroll.pack(fill="both", expand=True)

        main = scroll.inner
        main.columnconfigure(0, weight=1)

        title = ttk.Label(
            main,
            text="Compressor Optimizer",
            font=("Segoe UI", 18, "bold")
        )
        title.grid(row=0, column=0, sticky="w", pady=(0, 4))

        subtitle = ttk.Label(
            main,
            text="Offline formula-based calculator for 1 High + 1 Low compressor using same load ratio.",
            font=("Segoe UI", 10)
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(0, 12))

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

        note = (
            "Rule used: same load ratio\n"
            "high_rpm / 1000 = low_rpm / 1180\n"
            "Default inlet pressure = 1.1 bara"
        )
        ttk.Label(input_card, text=note, justify="left").grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))

        result_card = ttk.LabelFrame(main, text="Result", padding=12)
        result_card.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        result_card.columnconfigure(0, weight=1)

        self.result_text = tk.Text(
            result_card,
            height=24,
            wrap="word",
            font=("Consolas", 10)
        )
        self.result_text.grid(row=0, column=0, sticky="nsew")

        result_scroll = ttk.Scrollbar(result_card, orient="vertical", command=self.result_text.yview)
        result_scroll.grid(row=0, column=1, sticky="ns")
        self.result_text.configure(yscrollcommand=result_scroll.set)

        footer = ttk.Frame(main)
        footer.grid(row=4, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)

        ttk.Label(footer, textvariable=self.status_var).grid(row=0, column=0, sticky="w")

    def reset(self):
        self.target_var.set("")
        self.inlet_var.set(str(DEFAULT_INLET_PRESSURE))
        self.result_text.delete("1.0", tk.END)
        self.status_var.set("Ready")

    def calculate(self):
        try:
            result = calculate_compressor_plan(
                target_production=self.target_var.get().strip(),
                inlet_pressure=self.inlet_var.get().strip()
            )
            self._show_result(result)
            self.status_var.set(result["status"])
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Error")

    def _show_result(self, result):
        self.result_text.delete("1.0", tk.END)

        lines = [
            "COMPRESSOR OPTIMIZATION RESULT",
            "=" * 70,
            "",
            f"Status                     : {result['status']}",
            f"Message                    : {result['message']}",
            "",
            "INPUT",
            "-" * 70,
            f"Target Production          : {result['input_target_production']}",
            f"Inlet Pressure             : {result['input_inlet_pressure']} bara",
            "",
            "CALCULATED OPERATING POINT",
            "-" * 70,
            f"Common Load Ratio          : {result['load_ratio']}",
            f"Common Load Ratio %        : {result['load_ratio_percent']} %",
            f"High Compressor RPM        : {result['high_rpm']}",
            f"Low Compressor RPM         : {result['low_rpm']}",
            "",
            "CAPACITY OUTPUT",
            "-" * 70,
            f"High Capacity              : {result['high_capacity']}",
            f"Low Capacity               : {result['low_capacity']}",
            f"Total Capacity             : {result['total_capacity']}",
            f"High Share %               : {result['high_capacity_share_percent']} %",
            f"Low Share %                : {result['low_capacity_share_percent']} %",
            "",
            "LIMIT WINDOW",
            "-" * 70,
            f"Minimum Possible Total     : {result['min_possible_total_capacity']}",
            f"Maximum Possible Total     : {result['max_possible_total_capacity']}",
            "",
            "FORMULA BASE VALUES",
            "-" * 70,
            f"High Base                  : {result['high_formula_base']}",
            f"Low Base                   : {result['low_formula_base']}",
            "",
            "FORMULA USED",
            "-" * 70,
            "High: ((0.3173 * X) - 0.0948) * (HighRPM / 1000) * 10^6",
            "Low : ((0.1305 * X) - 0.0350) * (LowRPM / 1180) * 10^6",
            "",
            "Same-load rule:",
            "HighRPM / 1000 = LowRPM / 1180",
        ]

        self.result_text.insert("1.0", "\\n".join(lines))


# --SECTION 4-- RUN APP

def run_app():
    root = tk.Tk()

    try:
        from tkinter import ttk
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass

    app = CompressorOptimizerApp(root)
    root.mainloop()
'''


REQUIREMENTS_TXT = r'''pandas
openpyxl
'''

README_TXT = r'''COMPRESSOR OPTIMIZER - LOCAL OFFLINE TOOL

How to run:
1. Open terminal in this project folder
2. Create venv
3. Activate venv
4. Install requirements
5. Run main.py

CMD commands:

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py

EXE build command:

pyinstaller --noconfirm --clean --onefile --windowed --name "Compressor_Optimizer" main.py

EXE output:
dist\Compressor_Optimizer.exe
'''


# --SECTION 4-- WRITE HELPER

def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


# --SECTION 5-- BUILD PROJECT

def build_project():
    root = Path.cwd() / PROJECT_NAME
    root.mkdir(parents=True, exist_ok=True)

    files = {
        root / "main.py": MAIN_PY,
        root / "requirements.txt": REQUIREMENTS_TXT,
        root / "README.txt": README_TXT,
        root / "core" / "__init__.py": "",
        root / "core" / "config.py": CONFIG_PY,
        root / "core" / "calculator.py": CALCULATOR_PY,
        root / "core" / "future_fuel.py": FUTURE_FUEL_PY,
        root / "ui" / "__init__.py": "",
        root / "ui" / "app.py": UI_APP_PY,
    }

    for path, content in files.items():
        write_file(path, content)

    print("=" * 70)
    print("Project created successfully")
    print(root)
    print("=" * 70)
    print("Next commands:")
    print(f'cd /d "{root}"')
    print("python -m venv .venv")
    print(r".venv\Scripts\activate")
    print("pip install -r requirements.txt")
    print("python main.py")
    print("=" * 70)


# --SECTION 6-- ENTRY POINT

if __name__ == "__main__":
    build_project()