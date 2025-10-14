import customtkinter as ctk
from collections import defaultdict

class DeadlockView(ctk.CTkFrame):
    """
    An animated, pausable view to demonstrate Deadlock Detection using a simulated
    Resource Allocation Graph (RAG) with a guaranteed cycle.
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
        title_label = ctk.CTkLabel(self, text="Deadlock Detection (Animated Simulation)", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        
        # --- Controls and Status Frame ---
        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.run_button = ctk.CTkButton(controls_frame, text="Run Deadlock Animation", command=self.run_simulation)
        self.run_button.pack(side="left", padx=10, pady=10)
        
        self.pause_button = ctk.CTkButton(controls_frame, text="Pause", command=self.toggle_pause, state="disabled")
        self.pause_button.pack(side="left", padx=10, pady=10)
        
        self.result_label = ctk.CTkLabel(controls_frame, text="Click 'Run' to start the animation.", font=ctk.CTkFont(size=16))
        self.result_label.pack(side="left", padx=20, pady=10)

        # --- Graph Visualization Frame ---
        self.graph_frame = ctk.CTkFrame(self)
        self.graph_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        
        self.canvas = ctk.CTkCanvas(self.graph_frame, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.info_label = ctk.CTkLabel(self.graph_frame, text="This simulation will animate the creation of a classic deadlock.", wraplength=500, font=ctk.CTkFont(size=14))
        self.info_label.place(relx=0.5, rely=0.5, anchor="center")

    def toggle_pause(self):
        """Toggles the paused state of the animation."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.configure(text="Resume")
        else:
            self.pause_button.configure(text="Pause")
            self.animate_step() # Restart the animation loop if resuming

    def run_simulation(self):
        """Sets up and starts the animation."""
        if self.animation_job:
            self.after_cancel(self.animation_job)

        self.is_paused = False
        self.current_step = 0
        self.info_label.place_forget()
        self.canvas.delete("all")
        
        self.run_button.configure(state="disabled")
        self.pause_button.configure(state="normal", text="Pause")

        # --- Define the scenario and animation steps ---
        self.processes = {'P1': {'pos': (200, 150)}, 'P2': {'pos': (500, 150)}}
        self.resources = {'R1': {'pos': (200, 350)}, 'R2': {'pos': (500, 350)}}
        
        self.animation_steps = [
            ("TEXT", "Creating Process P1..."),
            ("DRAW_PROCESS", "P1"),
            ("TEXT", "Creating Resource R1..."),
            ("DRAW_RESOURCE", "R1"),
            ("TEXT", "P1 acquires and holds R1."),
            ("DRAW_ASSIGN_EDGE", "R1", "P1"),
            ("TEXT", "Creating Process P2..."),
            ("DRAW_PROCESS", "P2"),
            ("TEXT", "Creating Resource R2..."),
            ("DRAW_RESOURCE", "R2"),
            ("TEXT", "P2 acquires and holds R2."),
            ("DRAW_ASSIGN_EDGE", "R2", "P2"),
            ("TEXT", "Now, P1 requests resource R2 (held by P2)..."),
            ("DRAW_REQUEST_EDGE", "P1", "R2"),
            ("TEXT", "And P2 requests resource R1 (held by P1)..."),
            ("DRAW_REQUEST_EDGE", "P2", "R1"),
            ("TEXT", "A circular wait is formed! Detecting cycle..."),
            ("DETECT_CYCLE",),
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
            self.result_label.configure(text=args[0])
        elif step_type == "DRAW_PROCESS":
            name = args[0]
            x, y = self.processes[name]['pos']
            self.canvas.create_oval(x-25, y-25, x+25, y+25, fill="#4682B4", outline="white", width=2, tags=name)
            self.canvas.create_text(x, y, text=name, fill="white", font=ctk.CTkFont(size=14, weight="bold"), tags=name)
        elif step_type == "DRAW_RESOURCE":
            name = args[0]
            x, y = self.resources[name]['pos']
            self.canvas.create_rectangle(x-20, y-20, x+20, y+20, fill="#32CD32", outline="white", width=2, tags=name)
            self.canvas.create_text(x, y, text=name, fill="white", font=ctk.CTkFont(size=14, weight="bold"), tags=name)
        elif step_type == "DRAW_ASSIGN_EDGE":
            r_name, p_name = args
            px, py = self.processes[p_name]['pos']
            rx, ry = self.resources[r_name]['pos']
            self.canvas.create_line(rx, ry-20, px, py+25, arrow=ctk.LAST, fill="white", width=2)
        elif step_type == "DRAW_REQUEST_EDGE":
            p_name, r_name = args
            px, py = self.processes[p_name]['pos']
            rx, ry = self.resources[r_name]['pos']
            self.canvas.create_line(px+25 if p_name == 'P1' else px-25, py, rx-20 if p_name == 'P1' else rx+20, ry, arrow=ctk.LAST, fill="orange", width=2, dash=(5, 3))
        elif step_type == "DETECT_CYCLE":
            cycle = ['P1', 'R2', 'P2', 'R1', 'P1']
            cycle_str = " -> ".join(cycle)
            self.result_label.configure(text=f"DEADLOCK DETECTED! Cycle: {cycle_str}", text_color="red")
            # Highlight the cycle
            for name in self.processes: self.canvas.itemconfig(name, fill="red")
            for name in self.resources: self.canvas.itemconfig(name, fill="red")


        self.current_step += 1
        self.animation_job = self.after(1500, self.animate_step)

