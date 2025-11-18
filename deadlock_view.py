import customtkinter as ctk
import psutil
import os
from collections import defaultdict

class DeadlockView(ctk.CTkFrame):
    """
    An animated, pausable view to demonstrate Deadlock Detection.
    It simulates a deadlock scenario using the names of the top 2
    live processes and real resources (open files) from the user's system.
    """
    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.animation_job = None
        self.is_paused = False
        self.animation_steps = []
        self.current_step = 0

        # Title
        title_label = ctk.CTkLabel(self, text="Deadlock Detection (Live Process Simulation)", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        
        # --- Controls and Status Frame ---
        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.run_button = ctk.CTkButton(controls_frame, text="Run Deadlock Simulation", command=self.run_simulation)
        self.run_button.pack(side="left", padx=10, pady=10)
        
        self.pause_button = ctk.CTkButton(controls_frame, text="Pause", command=self.toggle_pause, state="disabled")
        self.pause_button.pack(side="left", padx=10, pady=10)
        
        self.result_label = ctk.CTkLabel(controls_frame, text="Click 'Run' to start the simulation.", font=ctk.CTkFont(size=16))
        self.result_label.pack(side="left", padx=20, pady=10)

        # --- Graph Visualization Frame ---
        self.graph_frame = ctk.CTkFrame(self)
        self.graph_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        
        self.canvas = ctk.CTkCanvas(self.graph_frame, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.info_label = ctk.CTkLabel(self.graph_frame, text="This simulation will fetch your top processes and their open files to create a hypothetical deadlock.", wraplength=500, font=ctk.CTkFont(size=14))
        self.info_label.place(relx=0.5, rely=0.5, anchor="center")

    def get_top_memory_processes(self, num_processes=2):
        """Fetches the top N processes by memory usage (RSS)."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                pinfo = proc.as_dict()
                if pinfo['memory_info'] and pinfo['memory_info'].rss > 0:
                    processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, AttributeError):
                pass
        
        sorted_processes = sorted(processes, key=lambda p: p['memory_info'].rss, reverse=True)
        return sorted_processes[:num_processes]

    def get_open_file_for_pid(self, pid):
        """Tries to get a meaningful open file name for a given PID."""
        try:
            proc = psutil.Process(pid)
            open_files = proc.open_files()
            # Try to find a log, db, or common file, not a DLL
            for file in open_files:
                if file.path.endswith(('.log', '.db', '.txt', '.dat')) and 'Windows' not in file.path:
                    return os.path.basename(file.path)
            # Fallback: return the first non-system file if any
            for file in open_files:
                 if 'Windows' not in file.path and 'System32' not in file.path:
                    return os.path.basename(file.path)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass # Ignore processes we can't inspect
        return None # Return None if no suitable file is found

    def toggle_pause(self):
        """Toggles the paused state of the animation."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.configure(text="Resume")
        else:
            self.pause_button.configure(text="Pause")
            self.animate_step() # Restart the animation loop if resuming
            
    def _truncate_name(self, name, max_len=15):
        """Helper to truncate long names for display."""
        if len(name) > max_len:
            return name[:max_len] + "..."
        return name

    def run_simulation(self):
        """Sets up and starts the animation based on live data."""
        if self.animation_job:
            self.after_cancel(self.animation_job)

        self.is_paused = False
        self.current_step = 0
        self.info_label.place_forget()
        self.canvas.delete("all")
        
        self.run_button.configure(state="disabled")
        self.pause_button.configure(state="normal", text="Pause")

        # --- Fetch Live Data ---
        live_procs = self.get_top_memory_processes(2)
        if len(live_procs) < 2:
            self.result_label.configure(text="Not enough running processes to simulate deadlock.", text_color="orange")
            self.run_button.configure(state="normal")
            self.pause_button.configure(state="disabled")
            return
            
        p1_name = live_procs[0]['name']
        p1_pid = live_procs[0]['pid']
        p2_name = live_procs[1]['name']
        p2_pid = live_procs[1]['pid']

        # Attempt to get real resource names (open files)
        r1_name = self.get_open_file_for_pid(p1_pid) or "Resource_A"
        r2_name = self.get_open_file_for_pid(p2_pid) or "Resource_B"

        # --- Define the scenario and animation steps ---
        p1_display = self._truncate_name(p1_name, 12)
        p2_display = self._truncate_name(p2_name, 12)
        r1_display = self._truncate_name(r1_name, 12)
        r2_display = self._truncate_name(r2_name, 12)

        self.processes = {p1_display: {'pos': (200, 150)}, p2_display: {'pos': (500, 150)}}
        self.resources = {r1_display: {'pos': (200, 350)}, r2_display: {'pos': (500, 350)}}
        
        self.animation_steps = [
            ("TEXT", f"Fetching processes... Found {p1_name} and {p2_name}."),
            ("DRAW_PROCESS", p1_display),
            ("TEXT", f"Fetching resources... Found {r1_name} (held by {p1_name})."),
            ("DRAW_RESOURCE", r1_display),
            ("TEXT", f"{p1_display} acquires and holds {r1_display}."),
            ("DRAW_ASSIGN_EDGE", r1_display, p1_display),
            ("TEXT", f"Creating process {p2_display}..."),
            ("DRAW_PROCESS", p2_display),
            ("TEXT", f"Fetching resources... Found {r2_name} (held by {p2_name})."),
            ("DRAW_RESOURCE", r2_display),
            ("TEXT", f"{p2_display} acquires and holds {r2_display}."),
            ("DRAW_ASSIGN_EDGE", r2_display, p2_display),
            ("TEXT", f"Now, {p1_display} requests resource {r2_display} (held by {p2_display})..."),
            ("DRAW_REQUEST_EDGE", p1_display, r2_display),
            ("TEXT", f"And {p2_display} requests resource {r1_display} (held by {p1_display})..."),
            ("DRAW_REQUEST_EDGE", p2_display, r1_display),
            ("TEXT", "A circular wait is formed! Detecting cycle..."),
            ("DETECT_CYCLE", [p1_display, r2_display, p2_display, r1_display, p1_display]),
        ]
        
        self.animate_step()

    def animate_step(self):
        """Executes a single step of the animation."""
        if self.is_paused or self.current_step >= len(self.animation_steps):
            if not self.is_paused: # Animation finished
                 self.run_button.configure(state="normal")
                 self.pause_button.configure(state="disabled")
            return

        step_type, *args = self.animation_steps[self.current_step]
        
        if step_type == "TEXT":
            self.result_label.configure(text=args[0], text_color="white")
        elif step_type == "DRAW_PROCESS":
            name = args[0]
            x, y = self.processes[name]['pos']
            self.canvas.create_oval(x-50, y-25, x+50, y+25, fill="#4682B4", outline="white", width=2, tags=name)
            self.canvas.create_text(x, y, text=name, fill="white", font=ctk.CTkFont(size=12, weight="bold"), tags=name)
        elif step_type == "DRAW_RESOURCE":
            name = args[0]
            x, y = self.resources[name]['pos']
            self.canvas.create_rectangle(x-50, y-20, x+50, y+20, fill="#32CD32", outline="white", width=2, tags=name)
            self.canvas.create_text(x, y, text=name, fill="white", font=ctk.CTkFont(size=12, weight="bold"), tags=name)
        elif step_type == "DRAW_ASSIGN_EDGE":
            r_name, p_name = args
            px, py = self.processes[p_name]['pos']
            rx, ry = self.resources[r_name]['pos']
            self.canvas.create_line(rx, ry-20, px, py+25, arrow=ctk.LAST, fill="white", width=2)
        elif step_type == "DRAW_REQUEST_EDGE":
            p_name, r_name = args
            px, py = self.processes[p_name]['pos']
            rx, ry = self.resources[r_name]['pos']
            self.canvas.create_line(px+50 if self.processes[p_name]['pos'][0] < 300 else px-50, py, rx-50 if self.processes[p_name]['pos'][0] < 300 else rx+50, ry, arrow=ctk.LAST, fill="orange", width=2, dash=(5, 3))
        elif step_type == "DETECT_CYCLE":
            cycle = args[0]
            cycle_str = " -> ".join(cycle)
            self.result_label.configure(text=f"DEADLOCK DETECTED! Cycle: {cycle_str}", text_color="red")
            # Highlight the cycle
            for name in self.processes: self.canvas.itemconfig(name, fill="red")
            for name in self.resources: self.canvas.itemconfig(name, fill="red")


        self.current_step += 1
        self.animation_job = self.after(1500, self.animate_step)
