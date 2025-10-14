import customtkinter as ctk
import psutil
import time

class SchedulingView(ctk.CTkFrame):
    """
    CPU Scheduling view for animating Round Robin algorithm on live processes,
    using actual CPU usage to determine simulated burst times.
    """
    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.quantum = 2
        self.colors = ['#FF6347', '#4682B4', '#32CD32', '#FFD700', '#6A5ACD']
        self.cpu_procs_cache = {} # Cache for CPU times
        self.animation_job = None
        self.is_paused = False
        
        # Title
        title_label = ctk.CTkLabel(self, text=f"CPU Scheduling: Round Robin on Live Processes (Quantum = {self.quantum}s)", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        
        # Controls
        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.run_button = ctk.CTkButton(controls_frame, text="Start Animation", command=self.start_animation)
        self.run_button.pack(side="left", padx=10, pady=10)
        
        self.pause_button = ctk.CTkButton(controls_frame, text="Pause", command=self.toggle_pause, state="disabled")
        self.pause_button.pack(side="left", padx=10, pady=10)

        self.reset_button = ctk.CTkButton(controls_frame, text="Reload Live Processes", command=self.setup_simulation)
        self.reset_button.pack(side="left", padx=10, pady=10)
        
        # ... (rest of __init__ is unchanged) ...
        viz_frame = ctk.CTkFrame(self)
        viz_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        viz_frame.grid_columnconfigure(0, weight=3)
        viz_frame.grid_columnconfigure(1, weight=1)
        gantt_frame = ctk.CTkFrame(viz_frame)
        gantt_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.timer_label = ctk.CTkLabel(gantt_frame, text="Timeline: 0s", font=ctk.CTkFont(size=16))
        self.timer_label.pack()
        self.gantt_canvas = ctk.CTkCanvas(gantt_frame, bg="#2b2b2b", height=80, highlightthickness=0)
        self.gantt_canvas.pack(fill="x", pady=10, padx=10)
        cpu_queue_frame = ctk.CTkFrame(viz_frame)
        cpu_queue_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(cpu_queue_frame, text="CPU").pack()
        self.cpu_box = ctk.CTkLabel(cpu_queue_frame, text="", width=80, height=80, fg_color="gray20", corner_radius=8, font=ctk.CTkFont(size=24, weight="bold"))
        self.cpu_box.pack(pady=5)
        ctk.CTkLabel(cpu_queue_frame, text="Ready Queue").pack(pady=(10,0))
        self.ready_queue_frame = ctk.CTkFrame(cpu_queue_frame, height=90)
        self.ready_queue_frame.pack(fill="x", padx=5, pady=5)
        self.process_frame = ctk.CTkFrame(self)
        self.process_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.setup_simulation()
    
    def toggle_pause(self):
        """Toggles the paused state of the animation."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.configure(text="Resume")
        else:
            self.pause_button.configure(text="Pause")
            self.tick() # Re-trigger the animation loop

    def get_top_cpu_processes_fast(self, num_processes=5):
        # ... (this function is unchanged) ...
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_times']):
            try:
                procs.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        time.sleep(0.2)
        processes_with_cpu = []
        for p in procs:
            try:
                cpu_usage = p.cpu_percent(interval=None)
                if cpu_usage > 0:
                    processes_with_cpu.append({'proc': p, 'cpu': cpu_usage})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        sorted_processes = sorted(processes_with_cpu, key=lambda x: x['cpu'], reverse=True)
        return sorted_processes[:num_processes]


    def setup_simulation(self):
        """Initializes simulation with live data, deriving burst times from CPU usage."""
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        
        self.is_paused = False
        self.run_button.configure(state="normal")
        self.pause_button.configure(text="Pause", state="disabled")
            
        top_processes = self.get_top_cpu_processes_fast()
        self.processes = []
        for i, proc_data in enumerate(top_processes):
            proc = proc_data['proc']
            cpu_usage = proc_data['cpu']
            burst_time = max(2, int(cpu_usage * 0.5) + 1)
            try:
                p_name = proc.name()
                p_pid = proc.pid
            except psutil.NoSuchProcess:
                continue
            self.processes.append({
                "id": p_name, "pid": p_pid, "cpu_usage": cpu_usage, "arrival": 0,
                "burst": burst_time, "remaining": burst_time,
                "color": self.colors[i % len(self.colors)]
            })
            
        self.timer = 0
        self.ready_queue = list(self.processes)
        self.current_process = None
        self.time_slice = 0
        self.gantt_data = []
        
        self.render_processes()
        self.render_queue_and_cpu()
        self.render_gantt()

    # ... (render functions are unchanged) ...
    def render_processes(self):
        for widget in self.process_frame.winfo_children(): widget.destroy()
        headers = ["Process", "PID", "CPU %", "Simulated Burst", "Remaining"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(self.process_frame, text=h, font=ctk.CTkFont(weight="bold")).grid(row=0, column=i, padx=10, pady=5)
        for i, p in enumerate(self.processes):
            ctk.CTkLabel(self.process_frame, text=p["id"][:20]).grid(row=i + 1, column=0, sticky="w")
            ctk.CTkLabel(self.process_frame, text=p["pid"]).grid(row=i + 1, column=1)
            ctk.CTkLabel(self.process_frame, text=f"{p['cpu_usage']:.1f}%").grid(row=i + 1, column=2)
            ctk.CTkLabel(self.process_frame, text=p["burst"]).grid(row=i + 1, column=3)
            ctk.CTkLabel(self.process_frame, text=p["remaining"]).grid(row=i + 1, column=4)

    def render_queue_and_cpu(self):
        for widget in self.ready_queue_frame.winfo_children(): widget.destroy()
        for p in self.ready_queue:
            label_text = p["id"][:5] + "..." if len(p["id"]) > 5 else p["id"]
            ctk.CTkLabel(self.ready_queue_frame, text=label_text, fg_color=p["color"], width=60, height=50, corner_radius=5).pack(side="left", padx=5)
        if self.current_process:
            label_text = self.current_process["id"][:5] + "..." if len(self.current_process["id"]) > 5 else self.current_process["id"]
            self.cpu_box.configure(text=label_text, fg_color=self.current_process["color"])
        else:
            self.cpu_box.configure(text="", fg_color="gray20")

    def render_gantt(self):
        self.gantt_canvas.delete("all")
        x_pos = 10
        scale = 25
        for item in self.gantt_data:
            width = item["duration"] * scale
            self.gantt_canvas.create_rectangle(x_pos, 10, x_pos + width, 70, fill=item["color"], outline="")
            label_text = item["id"][:8] if len(item["id"]) > 8 else item["id"]
            self.gantt_canvas.create_text(x_pos + width / 2, 40, text=label_text, fill="white")
            self.gantt_canvas.create_text(x_pos, 75, text=str(item["start"]), fill="white")
            x_pos += width
        self.gantt_canvas.create_text(x_pos, 75, text=str(self.timer), fill="white")


    def start_animation(self):
        self.run_button.configure(state="disabled")
        self.pause_button.configure(state="normal")
        self.tick()

    def tick(self):
        if self.is_paused:
            return

        if self.current_process:
            self.current_process["remaining"] -= 1
            self.time_slice += 1
            
            if self.current_process["remaining"] == 0:
                self.gantt_data.append({"id": self.current_process["id"], "start": self.timer - self.time_slice + 1, "duration": self.time_slice, "color": self.current_process["color"]})
                self.current_process = None
                self.time_slice = 0
            elif self.time_slice == self.quantum:
                self.gantt_data.append({"id": self.current_process["id"], "start": self.timer - self.time_slice + 1, "duration": self.time_slice, "color": self.current_process["color"]})
                self.ready_queue.append(self.current_process)
                self.current_process = None
                self.time_slice = 0
                
        if not self.current_process and self.ready_queue:
            self.current_process = self.ready_queue.pop(0)

        self.timer += 1
        self.timer_label.configure(text=f"Timeline: {self.timer}s")
        self.render_processes()
        self.render_queue_and_cpu()
        self.render_gantt()
        
        if any(p["remaining"] > 0 for p in self.processes) or self.ready_queue or self.current_process:
            self.animation_job = self.after(1000, self.tick)
        else:
            self.run_button.configure(state="normal")
            self.pause_button.configure(state="disabled")
            self.render_gantt()

