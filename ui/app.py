# --SECTION 1-- IMPORTS

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
        self.root.minsize(920, 620)

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
            text="1 High + 1 Low compressor calculator using same load ratio.",
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
            "Rule: same load ratio\n"
            "High RPM / 1000 = Low RPM / 1180\n"
            "Default inlet pressure = 1.1 bara"
        )
        ttk.Label(input_card, text=note, justify="left").grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))

        result_card = ttk.LabelFrame(main, text="Result", padding=12)
        result_card.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        result_card.columnconfigure(0, weight=1)
        result_card.columnconfigure(1, weight=1)

        self.summary_label = ttk.Label(
            result_card,
            text="Enter values and click Calculate.",
            font=("Segoe UI", 11, "bold")
        )
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

        footer = ttk.Frame(main)
        footer.grid(row=4, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)

        ttk.Label(footer, textvariable=self.status_var).grid(row=0, column=0, sticky="w")

    def _add_result_row(self, parent, row_no, label_text, attr_name):
        ttk.Label(
            parent,
            text=label_text,
            font=("Segoe UI", 10, "bold")
        ).grid(row=row_no, column=0, sticky="w", padx=(0, 20), pady=6)

        value_label = ttk.Label(
            parent,
            text="-",
            font=("Segoe UI", 10)
        )
        value_label.grid(row=row_no, column=1, sticky="w", pady=6)

        setattr(self, attr_name, value_label)

    def reset(self):
        self.target_var.set("")
        self.inlet_var.set(str(DEFAULT_INLET_PRESSURE))
        self.summary_label.config(text="Enter values and click Calculate.")

        self.target_value.config(text="-")
        self.pressure_value.config(text="-")
        self.high_rpm_value.config(text="-")
        self.low_rpm_value.config(text="-")
        self.high_capacity_value.config(text="-")
        self.low_capacity_value.config(text="-")
        self.total_capacity_value.config(text="-")
        self.load_ratio_value.config(text="-")
        self.operating_status_value.config(text="-")

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
        status = result["status"]

        if status == "OK":
            status_note = "Target-based RPM is within allowed machine range."
        elif status == "BELOW_MIN_LIMIT":
            status_note = "Target-based RPM is below the allowed machine minimum."
        elif status == "ABOVE_MAX_LIMIT":
            status_note = "Target-based RPM is above the allowed machine maximum."
        else:
            status_note = result.get("message", "Calculation completed.")

        self.summary_label.config(
            text=(
                f"Required RPM for target {result['input_target_production']}: "
                f"High {result['high_rpm']} RPM | Low {result['low_rpm']} RPM. {status_note}"
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



# --SECTION 4-- RUN APP

def run_app():
    root = tk.Tk()

    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass

    app = CompressorOptimizerApp(root)
    root.mainloop()
