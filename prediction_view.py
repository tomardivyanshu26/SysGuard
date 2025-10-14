import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class PredictionView(ctk.CTkFrame):
    """
    A view to display performance graphs and predict future usage
    based on historical system data, now with text display for values.
    """
    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Graph frame
        self.grid_rowconfigure(2, weight=0) # Info frame

        # --- Title ---
        title_label = ctk.CTkLabel(self, text="Performance & Prediction", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        
        # --- Graph Frame ---
        self.graph_frame = ctk.CTkFrame(self)
        self.graph_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.graph_frame.grid_columnconfigure(0, weight=1)
        self.graph_frame.grid_rowconfigure(0, weight=1)

        plt.style.use("dark_background")
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
        self.fig.patch.set_facecolor('#2b2b2b')

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        self.setup_plot(self.ax1, "CPU Usage (%)")
        self.setup_plot(self.ax2, "Memory Usage (%)")

        # --- Info & Prediction Frame ---
        info_frame = ctk.CTkFrame(self)
        info_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        info_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        font_style = ctk.CTkFont(size=14)
        ctk.CTkLabel(info_frame, text="Current CPU:", font=font_style, anchor="e").grid(row=0, column=0, sticky="ew", padx=5)
        self.current_cpu_label = ctk.CTkLabel(info_frame, text="N/A", font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        self.current_cpu_label.grid(row=0, column=1, sticky="ew")

        ctk.CTkLabel(info_frame, text="Predicted CPU (next step):", font=font_style, anchor="e").grid(row=0, column=2, sticky="ew", padx=5)
        self.predicted_cpu_label = ctk.CTkLabel(info_frame, text="N/A", font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        self.predicted_cpu_label.grid(row=0, column=3, sticky="ew")

        ctk.CTkLabel(info_frame, text="Current Memory:", font=font_style, anchor="e").grid(row=1, column=0, sticky="ew", padx=5)
        self.current_mem_label = ctk.CTkLabel(info_frame, text="N/A", font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        self.current_mem_label.grid(row=1, column=1, sticky="ew")

        ctk.CTkLabel(info_frame, text="Predicted Memory (next step):", font=font_style, anchor="e").grid(row=1, column=2, sticky="ew", padx=5)
        self.predicted_mem_label = ctk.CTkLabel(info_frame, text="N/A", font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        self.predicted_mem_label.grid(row=1, column=3, sticky="ew")


        self.cpu_history = []
        self.mem_history = []
        
    def setup_plot(self, ax, title):
        ax.set_facecolor('#3c3c3c')
        ax.set_title(title, color='white', fontsize=14)
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['top'].set_color('none')
        ax.spines['right'].set_color('none')
        ax.set_ylim(0, 105)

    def set_data_history(self, cpu_history, mem_history):
        self.cpu_history = list(cpu_history)
        self.mem_history = list(mem_history)
        self.update_plots()

    def update_plots(self):
        if not self.cpu_history or not self.mem_history:
            return

        # --- Update CPU Plot ---
        self.ax1.clear()
        self.setup_plot(self.ax1, "CPU Usage (%)")
        self.ax1.plot(self.cpu_history, label="Actual Usage", color="#1f77b4")
        cpu_prediction_line, next_cpu_pred = self.get_prediction_line(self.cpu_history)
        if cpu_prediction_line is not None:
            self.ax1.plot(range(len(cpu_prediction_line)), cpu_prediction_line, linestyle='--', label="Prediction", color="#ff7f0e")
            self.current_cpu_label.configure(text=f"{self.cpu_history[-1]:.1f}%")
            self.predicted_cpu_label.configure(text=f"{next_cpu_pred:.1f}%")
        self.ax1.legend()

        # --- Update Memory Plot ---
        self.ax2.clear()
        self.setup_plot(self.ax2, "Memory Usage (%)")
        self.ax2.plot(self.mem_history, label="Actual Usage", color="#2ca02c")
        mem_prediction_line, next_mem_pred = self.get_prediction_line(self.mem_history)
        if mem_prediction_line is not None:
            self.ax2.plot(range(len(mem_prediction_line)), mem_prediction_line, linestyle='--', label="Prediction", color="#d62728")
            self.current_mem_label.configure(text=f"{self.mem_history[-1]:.1f}%")
            self.predicted_mem_label.configure(text=f"{next_mem_pred:.1f}%")
        self.ax2.legend()
        
        self.ax2.set_xlabel("Time (updates ago)", color='white')
        self.fig.tight_layout()
        self.canvas.draw()
        
    def get_prediction_line(self, data):
        """Calculates a linear regression and returns the line and the next predicted value."""
        if len(data) < 2:
            return None, 0
            
        x = np.arange(len(data))
        y = np.array(data)
        coeffs = np.polyfit(x, y, 1)
        slope, intercept = coeffs

        future_x = np.arange(len(data) + 10) # Predict next 10 points
        prediction = slope * future_x + intercept
        prediction = np.clip(prediction, 0, 100)

        next_predicted_value = prediction[len(data)] # The value for the very next step
        
        return prediction, next_predicted_value

