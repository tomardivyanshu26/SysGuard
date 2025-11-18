import customtkinter as ctk
import os
from datetime import datetime

class FilesView(ctk.CTkFrame):
    """
    A view to display all the project files (.py, .txt, .md)
    found in the current working directory with details like size and modified date.
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
        self.files_frame.grid_columnconfigure(0, weight=2) # Name
        self.files_frame.grid_columnconfigure(1, weight=1) # Size
        self.files_frame.grid_columnconfigure(2, weight=1) # Modified
        
        self.load_files()

    def get_file_icon(self, filename):
        """Returns an emoji icon based on the file extension."""
        if filename.endswith(".py"):
            return "🐍" # Python
        elif filename.endswith(".txt"):
            return "📝" # Text
        elif filename.endswith(".md"):
            return "📰" # Markdown
        else:
            return "📄" # Generic file

    def load_files(self):
        """Scans the directory and displays the list of relevant files with details."""
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
            
            # --- Create Headers ---
            header_font = ctk.CTkFont(size=14, weight="bold")
            ctk.CTkLabel(self.files_frame, text="Name", font=header_font, anchor="w").grid(row=0, column=0, padx=20, pady=10, sticky="w")
            ctk.CTkLabel(self.files_frame, text="Size", font=header_font, anchor="w").grid(row=0, column=1, padx=10, pady=10, sticky="w")
            ctk.CTkLabel(self.files_frame, text="Last Modified", font=header_font, anchor="w").grid(row=0, column=2, padx=10, pady=10, sticky="w")

            # --- List Files ---
            for i, filename in enumerate(sorted(project_files)):
                filepath = os.path.join(current_directory, filename)
                
                try:
                    stat = os.stat(filepath)
                    size_kb = f"{stat.st_size / 1024:.2f} KB"
                    mod_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                except FileNotFoundError:
                    size_kb = "N/A"
                    mod_time = "N/A"
                
                icon = self.get_file_icon(filename)
                
                # Create labels for each column
                ctk.CTkLabel(self.files_frame, text=f"{icon} {filename}", font=ctk.CTkFont(size=16), anchor="w").grid(row=i+1, column=0, padx=20, pady=5, sticky="w")
                ctk.CTkLabel(self.files_frame, text=size_kb, font=ctk.CTkFont(size=16), anchor="w").grid(row=i+1, column=1, padx=10, pady=5, sticky="w")
                ctk.CTkLabel(self.files_frame, text=mod_time, font=ctk.CTkFont(size=16), anchor="w").grid(row=i+1, column=2, padx=10, pady=5, sticky="w")


        except Exception as e:
            ctk.CTkLabel(self.files_frame, text=f"Error loading files: {e}", text_color="red").pack(padx=10, pady=10)
