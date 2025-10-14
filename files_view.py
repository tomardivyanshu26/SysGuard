import customtkinter as ctk
import os

class FilesView(ctk.CTkFrame):
    """
    A view to display all the project files (.py, .txt, .md)
    found in the current working directory.
    """
    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Title
        title_label = ctk.CTkLabel(self, text="Project Files", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        
        # --- File List Frame ---
        self.files_frame = ctk.CTkFrame(self)
        self.files_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        self.load_files()

    def load_files(self):
        """Scans the directory and displays the list of relevant files."""
        # Clear any existing file labels
        for widget in self.files_frame.winfo_children():
            widget.destroy()
            
        try:
            current_directory = os.getcwd()
            files = os.listdir(current_directory)
            
            project_files = [f for f in files if f.endswith(('.py', '.txt', '.md'))]
            
            if not project_files:
                ctk.CTkLabel(self.files_frame, text="No project files found in this directory.", font=ctk.CTkFont(size=16)).pack(padx=10, pady=10)
                return

            for i, filename in enumerate(sorted(project_files)):
                file_label = ctk.CTkLabel(self.files_frame, text=f"📄 {filename}", font=ctk.CTkFont(size=16), anchor="w")
                file_label.pack(fill="x", padx=20, pady=5)

        except Exception as e:
            ctk.CTkLabel(self.files_frame, text=f"Error loading files: {e}", text_color="red").pack(padx=10, pady=10)
