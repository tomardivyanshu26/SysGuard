import customtkinter as ctk
from tkinter import ttk
import psutil
from collections import defaultdict
import threading
import time
import queue

class DashboardView(ctk.CTkFrame):
    """
    Dashboard view that mimics the Windows Task Manager's process list,
    using a thread-safe queue for UI updates and correcting for multi-core CPU usage.
    """
    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Title ---
        title_label = ctk.CTkLabel(self, text="Processes", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # --- Process Treeview ---
        style = ttk.Style()
        style.theme_use("default")
        
        style.configure("Treeview",
                        background="#2b2b2b",
                        foreground="white",
                        rowheight=25,
                        fieldbackground="#2b2b2b",
                        bordercolor="#333333",
                        borderwidth=0)
        style.map('Treeview', background=[('selected', '#1f538d')])
        
        style.configure("Treeview.Heading",
                        background="#2b2b2b",
                        foreground="white",
                        relief="flat",
                        font=('Calibri', 12, 'bold'))
        style.map("Treeview.Heading", background=[('active', '#3c3c3c')])
        
        self.tree = ttk.Treeview(self, columns=("status", "cpu", "mem", "disk", "network"), show="headings")
        self.tree.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)

        # Define Headings
        self.tree.heading("status", text="Name")
        self.tree.heading("cpu", text="CPU")
        self.tree.heading("mem", text="Memory")
        self.tree.heading("disk", text="Disk")
        self.tree.heading("network", text="Network")

        # Define Column widths
        self.tree.column("status", width=400)
        self.tree.column("cpu", width=100, anchor="e")
        self.tree.column("mem", width=150, anchor="e")
        self.tree.column("disk", width=150, anchor="e")
        self.tree.column("network", width=150, anchor="e")

        self.processes = {}
        self.cpu_history = []
        self.mem_history = []
        
        # --- Threading and Queue Setup ---
        self.data_queue = queue.Queue()
        self.update_running = True
        self.cpu_cores = psutil.cpu_count() # Get number of CPU cores
        self.update_thread = threading.Thread(target=self.update_processes_worker, daemon=True)
        self.update_thread.start()

        self.process_queue()
        self.bind("<Destroy>", self.on_destroy)

    def get_process_data(self):
        """Efficiently fetches, aggregates, and normalizes process data."""
        grouped_procs = defaultdict(lambda: {
            'pid': [], 'cpu_percent': 0, 'memory_info': [0, 0], 
            'num_threads': 0
        })
        
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'num_threads']):
            try:
                p_info = p.info
                # Normalize CPU percent by the number of cores
                p_info['cpu_percent'] = p_info.get('cpu_percent', 0) / self.cpu_cores
                
                name = p_info.get('name', 'N/A').split('.')[0].replace('-', ' ').title()
                if not name: continue

                group = grouped_procs[name]
                group['pid'].append(p_info['pid'])
                group['cpu_percent'] += p_info['cpu_percent']
                group['memory_info'][0] += p_info['memory_info'].rss if p_info.get('memory_info') else 0
                group['num_threads'] += p_info.get('num_threads', 0)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return grouped_procs

    def update_processes_worker(self):
        """
        Continuously fetches process data in a background thread
        and puts it into the queue.
        """
        while self.update_running:
            processes_data = self.get_process_data()
            self.data_queue.put(processes_data)
            time.sleep(2)

    def process_queue(self):
        """
        Checks the queue for new data and schedules a GUI update if found.
        """
        try:
            data = self.data_queue.get_nowait()
            self.update_gui(data)
        except queue.Empty:
            pass
        finally:
            if self.update_running:
                self.after(200, self.process_queue)

    def update_gui(self, processes_data):
        """Updates the Treeview widget on the main GUI thread."""
        if not self.winfo_exists(): return
        
        existing_items = {self.tree.item(item, "values")[0]: item for item in self.tree.get_children("")}
        
        total_cpu = psutil.cpu_percent()
        total_mem = psutil.virtual_memory()

        self.tree.heading("cpu", text=f"CPU\n{total_cpu:.1f}%")
        self.tree.heading("mem", text=f"Memory\n{total_mem.percent:.1f}%")
        self.tree.heading("disk", text="Disk\n-")
        self.tree.heading("network", text="Network\n-")

        self.cpu_history.append(total_cpu)
        self.mem_history.append(total_mem.percent)
        if len(self.cpu_history) > 100:
            self.cpu_history.pop(0)
            self.mem_history.pop(0)

        for name, data in processes_data.items():
            mem_mb = data['memory_info'][0] / (1024 * 1024)
            # Ensure CPU doesn't exceed 100% in the display
            cpu_percent = min(data['cpu_percent'], 100.0)
            values = (
                f"{name} ({len(data['pid'])})",
                f"{cpu_percent:.1f}%",
                f"{mem_mb:.1f} MB",
                "0.0 MB/s",
                "0.0 Mbps"
            )

            if values[0] in existing_items:
                item_id = existing_items.pop(values[0])
                if self.tree.exists(item_id):
                    self.tree.item(item_id, values=values)
            else:
                self.tree.insert("", "end", values=values)

        for item_id in existing_items.values():
            if self.tree.exists(item_id):
                self.tree.delete(item_id)

    def on_destroy(self):
        """Signal the update thread to stop when the widget is destroyed."""
        self.update_running = False

