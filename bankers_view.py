import customtkinter as ctk
import random
import psutil

class BankersView(ctk.CTkFrame):
    """
    Banker's Algorithm view for simulating deadlock avoidance based on live system processes.
    """
    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.animation_job = None
        self.is_paused = False

        # Title
        title_label = ctk.CTkLabel(self, text="Banker's Algorithm (Deadlock Avoidance)", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        
        # --- Controls and Status Frame ---
        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.run_button = ctk.CTkButton(controls_frame, text="Run Safety Algorithm", command=self.run_algorithm)
        self.run_button.pack(side="left", padx=10, pady=10)
        
        self.pause_button = ctk.CTkButton(controls_frame, text="Pause", command=self.toggle_pause, state="disabled")
        self.pause_button.pack(side="left", padx=10, pady=10)
        
        self.reset_button = ctk.CTkButton(controls_frame, text="Reload Live Processes", command=self.setup_simulation)
        self.reset_button.pack(side="left", padx=10, pady=10)

        self.result_label = ctk.CTkLabel(controls_frame, text="Click 'Run' to start.", font=ctk.CTkFont(size=16))
        self.result_label.pack(side="left", padx=20, pady=10)
        
        # ... (rest of __init__ is unchanged) ...
        overview_frame = ctk.CTkFrame(self)
        overview_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        overview_frame.grid_columnconfigure((0, 1), weight=1)
        self.available_frame = ctk.CTkFrame(overview_frame)
        self.available_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(self.available_frame, text="Available System Memory (MB)").pack()
        self.sequence_frame = ctk.CTkFrame(overview_frame)
        self.sequence_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(self.sequence_frame, text="Safe Sequence").pack()
        self.matrix_frame = ctk.CTkFrame(self)
        self.matrix_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.matrix_frame.grid_columnconfigure((0,1,2,3), weight=1)
        self.setup_simulation()

    def toggle_pause(self):
        """Toggles the paused state of the animation."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.configure(text="Resume")
        else:
            self.pause_button.configure(text="Pause")
            # If we resume, we need to re-trigger the animation loop
            self.iterator(self.work, self.finish, self.safe_sequence, 0)

    def get_top_memory_processes(self, num_processes=5):
        """Fetches the top N processes by memory usage (RSS)."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                pinfo = proc.as_dict()
                if pinfo['memory_info'].rss > 0:
                    processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        sorted_processes = sorted(processes, key=lambda p: p['memory_info'].rss, reverse=True)
        return sorted_processes[:num_processes]

    def setup_simulation(self):
        """Initializes or resets the simulation."""
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        
        self.is_paused = False
        self.run_button.configure(state="normal")
        self.pause_button.configure(text="Pause", state="disabled")

        top_processes = self.get_top_memory_processes()
        self.num_processes = len(top_processes)
        self.processes_info = top_processes
        available_mem_mb = psutil.virtual_memory().available / (1024 * 1024)
        self.available = [int(available_mem_mb)]
        self.allocation = [[int(p['memory_info'].rss / (1024*1024))] for p in top_processes]
        self.max_claim = [[int(p['memory_info'].vms / (1024*1024))] for p in top_processes]
        for i in range(self.num_processes):
            if self.max_claim[i][0] <= self.allocation[i][0]:
                self.max_claim[i][0] = self.allocation[i][0] + int(self.allocation[i][0] * 0.2) + 10
        self.need = [[self.max_claim[i][0] - self.allocation[i][0]] for i in range(self.num_processes)]
        self.result_label.configure(text="Ready to run safety algorithm on live processes.", text_color="white")
        self.render_state()

    # ... (render_state is unchanged) ...
    def render_state(self, safe_sequence=None, highlight_row=None, highlight_color=None):
        if safe_sequence is None: safe_sequence = []
        for widget in self.available_frame.winfo_children():
            if "Available" not in widget.cget("text"): widget.destroy()
        for widget in self.sequence_frame.winfo_children():
            if widget.cget("text") != "Safe Sequence": widget.destroy()
        for widget in self.matrix_frame.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.available_frame, text=f"{self.available[0]} MB", font=ctk.CTkFont(size=18, weight="bold")).pack()
        for p_idx in safe_sequence:
            p_name = self.processes_info[p_idx]['name']
            ctk.CTkLabel(self.sequence_frame, text=f"{p_name[:10]}...", fg_color="green", corner_radius=5).pack(side="left", padx=5, pady=5)
        headers = ["Process", "Allocation (RSS)", "Max Claim (VMS)", "Need"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(self.matrix_frame, text=h, font=ctk.CTkFont(weight="bold")).grid(row=0, column=i, padx=5, pady=5)
        self.process_rows = []
        for i in range(self.num_processes):
            row_frame = ctk.CTkFrame(self.matrix_frame, corner_radius=5)
            if i == highlight_row: row_frame.configure(fg_color=highlight_color)
            row_frame.grid(row=i + 1, column=0, columnspan=4, sticky="ew", pady=2)
            self.process_rows.append(row_frame)
            p_info = self.processes_info[i]
            p_label = f"P{i} ({p_info['name']})"
            ctk.CTkLabel(row_frame, text=p_label, width=200, anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(row_frame, text=f"{self.allocation[i][0]} MB", width=150).pack(side="left", padx=10)
            ctk.CTkLabel(row_frame, text=f"{self.max_claim[i][0]} MB", width=150).pack(side="left", padx=10)
            ctk.CTkLabel(row_frame, text=f"{self.need[i][0]} MB", width=150).pack(side="left", padx=10)

    def run_algorithm(self):
        """Starts the safety algorithm animation."""
        self.run_button.configure(state="disabled")
        self.pause_button.configure(state="normal")
        
        self.work = list(self.available)
        self.finish = [False] * self.num_processes
        self.safe_sequence = []
        self.iterator(self.work, self.finish, self.safe_sequence, 0)
        
    def iterator(self, work, finish, safe_sequence, iteration_count):
        """The main animation loop for the safety algorithm."""
        if self.is_paused:
            return

        if len(safe_sequence) == self.num_processes:
            self.result_label.configure(text="System is SAFE.", text_color="green")
            self.render_state(safe_sequence)
            self.run_button.configure(state="normal")
            self.pause_button.configure(state="disabled")
            return

        found_process_this_pass = False
        for i in range(self.num_processes):
            if not finish[i] and self.need[i][0] <= work[0]:
                self.result_label.configure(text=f"Checking {self.processes_info[i]['name']}: Need <= Work. Executing...", text_color="white")
                self.render_state(safe_sequence, highlight_row=i, highlight_color="orange")
                self.animation_job = self.after(1500, self.execute_process, work, finish, safe_sequence, i)
                found_process_this_pass = True
                return

        if not found_process_this_pass and not all(finish):
            self.result_label.configure(text="System is UNSAFE. Deadlock possible.", text_color="red")
            self.render_state(safe_sequence)
            self.run_button.configure(state="normal")
            self.pause_button.configure(state="disabled")

    def execute_process(self, work, finish, safe_sequence, process_index):
        if self.is_paused: return

        work[0] += self.allocation[process_index][0]
        finish[process_index] = True
        safe_sequence.append(process_index)
        
        p_name = self.processes_info[process_index]['name']
        self.result_label.configure(text=f"{p_name} finished. Releasing resources.", text_color="green")
        self.render_state(safe_sequence, highlight_row=process_index, highlight_color="green")
        
        self.animation_job = self.after(1500, self.iterator, work, finish, safe_sequence, 0)

