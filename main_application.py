import customtkinter as ctk
from dashboard_view import DashboardView
from bankers_view import BankersView
from scheduling_view import SchedulingView
from prediction_view import PredictionView
from deadlock_view import DeadlockView
from files_view import FilesView
from fcfs_view import FcfsView # Import the new FCFS view

# Set the appearance mode and default color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class App(ctk.CTk):
    """
    Main application class that initializes the window and manages views.
    """
    def __init__(self):
        super().__init__()

        self.title("System Health Monitor")
        self.geometry("1280x800") 

        # Configure grid layout (1x2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1) # Adjusted row configure for new button

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="System Monitor", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Navigation buttons
        self.dashboard_button = ctk.CTkButton(self.sidebar_frame, text="Processes", command=lambda: self.switch_view("dashboard"))
        self.dashboard_button.grid(row=1, column=0, padx=20, pady=10)

        self.bankers_button = ctk.CTkButton(self.sidebar_frame, text="Banker's Algorithm", command=lambda: self.switch_view("bankers"))
        self.bankers_button.grid(row=2, column=0, padx=20, pady=10)
        
        self.deadlock_button = ctk.CTkButton(self.sidebar_frame, text="Deadlock Detection", command=lambda: self.switch_view("deadlock"))
        self.deadlock_button.grid(row=3, column=0, padx=20, pady=10)

        self.scheduling_button = ctk.CTkButton(self.sidebar_frame, text="CPU Scheduling (RR)", command=lambda: self.switch_view("scheduling"))
        self.scheduling_button.grid(row=4, column=0, padx=20, pady=10)
        
        self.fcfs_button = ctk.CTkButton(self.sidebar_frame, text="CPU Scheduling (FCFS)", command=lambda: self.switch_view("fcfs"))
        self.fcfs_button.grid(row=5, column=0, padx=20, pady=10)

        self.prediction_button = ctk.CTkButton(self.sidebar_frame, text="Performance", command=lambda: self.switch_view("prediction"))
        self.prediction_button.grid(row=6, column=0, padx=20, pady=10)

        self.files_button = ctk.CTkButton(self.sidebar_frame, text="Project Files", command=lambda: self.switch_view("files"))
        self.files_button.grid(row=7, column=0, padx=20, pady=10)
        
        # --- Main Content Area ---
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)

        # Dictionary to hold the view frames
        self.views = {}

        # Initialize and pack the views
        for name, View in {
            "dashboard": DashboardView, 
            "bankers": BankersView, 
            "deadlock": DeadlockView,
            "scheduling": SchedulingView,
            "fcfs": FcfsView, # Add the new FCFS view
            "prediction": PredictionView,
            "files": FilesView
        }.items():
            frame = View(self.main_content_frame)
            self.views[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Start with the dashboard view
        self.switch_view("dashboard")


    def switch_view(self, view_name):
        """
        Brings the selected view to the front.
        If the prediction view is selected, it passes the dashboard's history.
        """
        if view_name == "prediction":
            dashboard = self.views["dashboard"]
            prediction_view = self.views["prediction"]
            if hasattr(dashboard, 'cpu_history'):
                prediction_view.set_data_history(dashboard.cpu_history, dashboard.mem_history)
        
        # Refresh the file list every time the view is switched to
        if view_name == "files":
            self.views["files"].load_files()

        frame = self.views[view_name]
        frame.tkraise()


if __name__ == "__main__":
    app = App()
    app.mainloop()
