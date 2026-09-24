import json
import random
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    import pygame
except ImportError:
    pygame = None

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


class CyberpunkDesktop:
    DEFAULT_MUSIC_FOLDER = Path.home() / "OneDrive" / "Documents" / "Euro Truck Simulator 2" / "music"
    SETTINGS_FILE = Path.home() / ".cyberpunk_desktop.json"
    AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}

    def __init__(self, root):
        self.root = root
        self.root.title("Cyberpunk Desktop")
        self.root.geometry("1280x820")
        self.root.minsize(900, 620)
        self.root.configure(bg="#080611")

        self.music_files = []
        self.music_index = 0
        self.shuffle_enabled = False
        self.repeat_enabled = False
        self.current_folder = self.DEFAULT_MUSIC_FOLDER
        self.widget_frames = {}
        self.widget_buttons = {}
        self.colors = {"cyan": "#00eaff", "pink": "#ff3b9d", "text": "#f5f2ff", "panel": "#121020"}

        self.load_settings()
        self.build_styles()
        self.build_background()
        self.build_interface()
        self.update_clock()
        self.restore_folder_if_available()

        if pygame:
            pygame.mixer.init()

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def build_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Cyber.TButton", background="#171528", foreground=self.colors["cyan"], borderwidth=1, padding=7)
        self.style.map("Cyber.TButton", background=[("active", "#30203b")], foreground=[("active", self.colors["pink"])])
        self.style.configure("Cyber.Horizontal.TScale", troughcolor="#242131", background=self.colors["cyan"])

    def build_interface(self):
        self.build_calculator()
        self.build_clock()
        self.build_notes()
        self.build_music()
        self.build_monitor()
        self.build_theme_panel()
        self.build_dock()

    def build_background(self):
        self.background_label = tk.Label(self.root, bg="#080611")
        self.background_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.background_label.lower()
        self.background_frames = []
        self.background_durations = []
        self.background_index = 0

        if Image is None:
            return

        background_path = Path(__file__).with_name("background.gif")
        if not background_path.exists():
            return

        try:
            image = Image.open(background_path)
            for frame_index in range(getattr(image, "n_frames", 1)):
                image.seek(frame_index)
                frame = image.convert("RGB")
                self.background_frames.append(frame)
                self.background_durations.append(image.info.get("duration", 100))
            self.animate_background()
        except Exception:
            self.background_frames = []

    def animate_background(self):
        if not self.background_frames:
            return
        frame = self.background_frames[self.background_index]
        resized = frame.resize((self.root.winfo_width(), self.root.winfo_height()))
        self.background_image = ImageTk.PhotoImage(resized)
        self.background_label.configure(image=self.background_image)
        self.background_index = (self.background_index + 1) % len(self.background_frames)
        duration = self.background_durations[self.background_index - 1]
        self.root.after(max(40, duration), self.animate_background)

    def panel(self, parent, title, width=260):
        frame = tk.Frame(parent, bg="#101020", highlightbackground="#254b58", highlightthickness=1)
        header = tk.Frame(frame, bg="#171528", height=34)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=title, bg="#171528", fg=self.colors["cyan"], font=("Consolas", 10, "bold")).pack(side="left", padx=10)
        content = tk.Frame(frame, bg="#101020")
        content.pack(fill="both", expand=True, padx=12, pady=12)
        frame.configure(width=width)
        return frame, content

    def build_calculator(self):
        frame = tk.Frame(self.root, bg="#0a0816", highlightbackground="#ff1e82", highlightthickness=1)
        frame.place(relx=.5, rely=.5, anchor="center", width=375, height=667)
        self.widget_frames["calculator"] = frame

        title_bar = tk.Frame(frame, bg="#171020", height=32)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)
        tk.Label(title_bar, text="◈ CALCULATION CORE", bg="#171020", fg=self.colors["cyan"], font=("Consolas", 10, "bold")).pack(side="left", padx=12)
        tk.Label(title_bar, text="ONLINE", bg="#171020", fg="#ffd166", font=("Consolas", 8, "bold")).pack(side="right", padx=12)

        display = tk.Frame(frame, bg="#080612", height=221)
        display.pack(fill="x")
        display.pack_propagate(False)

        smart_controls = tk.Frame(display, bg="#080612")
        smart_controls.pack(fill="x", padx=10, pady=10)
        for label in ["ANS", "M+", "M−", "MR", "MC", "COPY", "↶", "SCI"]:
            tk.Button(smart_controls, text=label, bg="#121020", fg="#8d8aa8", activebackground="#25152c", activeforeground=self.colors["cyan"], relief="flat", bd=0, font=("Consolas", 8, "bold"), height=1).pack(side="left", fill="x", expand=True, padx=2)

        expression = tk.Frame(display, bg="#080612")
        expression.pack(side="bottom", fill="x", padx=22, pady=18)
        self.total_display = tk.StringVar(value="")
        tk.Label(expression, textvariable=self.total_display, anchor="e", bg="#080612", fg="#8d8aa8", font=("Consolas", 11)).pack(fill="x")
        self.calculator_display = tk.StringVar(value="0")
        tk.Label(expression, textvariable=self.calculator_display, anchor="e", bg="#080612", fg=self.colors["text"], font=("Consolas", 34, "bold"), padx=0).pack(fill="x")

        buttons = ["C", "⌫", "%", "÷", "7", "8", "9", "×", "4", "5", "6", "−", "1", "2", "3", "+", "±", "0", ".", "=", "(", ")", "x²", "√"]
        grid = tk.Frame(frame, bg="#121020", height=414)
        grid.pack(fill="both", expand=True)
        grid.pack_propagate(False)
        for index, label in enumerate(buttons):
            is_operator = label in {"÷", "×", "−", "+"}
            is_equals = label == "="
            button_bg = "#21152b" if is_operator else "#35152d" if is_equals else "#121020"
            button_fg = self.colors["cyan"] if is_operator else self.colors["pink"] if is_equals else "#e8e5f2"
            button = tk.Button(grid, text=label, bg=button_bg, fg=button_fg, activebackground="#2d1a3c", activeforeground=self.colors["pink"], relief="flat", bd=0, font=("Consolas", 18, "bold"), command=lambda value=label: self.calculator_input(value))
            button.grid(row=index // 4, column=index % 4, sticky="nsew", padx=1, pady=1)
        for index in range(4):
            grid.columnconfigure(index, weight=1)
        for index in range(6):
            grid.rowconfigure(index, weight=1)

    def calculator_input(self, value):
        current = self.calculator_display.get()
        if value == "C":
            self.calculator_display.set("0")
        elif value == "⌫":
            self.calculator_display.set(current[:-1] or "0")
        elif value == "=":
            try:
                expression = current.replace("×", "*").replace("÷", "/").replace("√", "**0.5")
                self.calculator_display.set(str(round(eval(expression, {"__builtins__": {}}, {}), 10)))
            except Exception:
                self.calculator_display.set("Error")
        elif value == "x²":
            try:
                self.calculator_display.set(str(round(float(current) ** 2, 10)))
            except ValueError:
                self.calculator_display.set("Error")
        elif value == "√":
            try:
                self.calculator_display.set(str(round(float(current) ** .5, 10)))
            except (ValueError, TypeError):
                self.calculator_display.set("Error")
        elif value == "±":
            self.calculator_display.set(current[1:] if current.startswith("-") else "-" + current)
        elif value == "%":
            try:
                self.calculator_display.set(str(float(current) / 100))
            except ValueError:
                self.calculator_display.set("Error")
        else:
            self.calculator_display.set("" if current == "0" or current == "Error" else current)
            self.calculator_display.set(self.calculator_display.get() + value)

    def build_clock(self):
        frame, content = self.panel(self.root, "◈ SYSTEM CLOCK", 280)
        frame.place(x=22, y=22, width=280, height=120)
        self.widget_frames["clock"] = frame
        self.clock_label = tk.Label(content, bg="#101020", fg=self.colors["cyan"], font=("Consolas", 30, "bold"))
        self.clock_label.pack()
        self.date_label = tk.Label(content, bg="#101020", fg="#ffd166", font=("Consolas", 10))
        self.date_label.pack(pady=(5, 0))

    def update_clock(self):
        from datetime import datetime
        now = datetime.now()
        self.clock_label.configure(text=now.strftime("%H:%M:%S"))
        self.date_label.configure(text=now.strftime("%a // %d %b %Y").upper())
        self.root.after(1000, self.update_clock)

    def build_notes(self):
        frame, content = self.panel(self.root, "◈ MINI NOTEPAD", 300)
        frame.place(x=22, rely=1, y=-72, anchor="sw", width=300, height=220)
        self.widget_frames["notes"] = frame
        self.notes = tk.Text(content, bg="#090914", fg="white", insertbackground=self.colors["cyan"], relief="flat", height=7, font=("Consolas", 10))
        self.notes.pack(fill="both", expand=True)
        self.notes.insert("1.0", self.settings.get("notes", ""))
        self.notes.bind("<KeyRelease>", lambda _event: self.save_settings())

    def build_music(self):
        frame, content = self.panel(self.root, "◈ AUDIO LINK", 410)
        frame.place(relx=1, rely=1, x=-22, y=-72, anchor="se", width=410, height=265)
        self.widget_frames["music"] = frame
        self.music_name = tk.Label(content, text="NO AUDIO LOADED", anchor="w", bg="#171528", fg=self.colors["text"], font=("Consolas", 11), padx=10, pady=8)
        self.music_name.pack(fill="x")
        self.music_next = tk.Label(content, text="NEXT // NO NEXT TRACK", anchor="w", bg="#101020", fg="#88859b", font=("Consolas", 9), padx=10, pady=5)
        self.music_next.pack(fill="x")
        folder_row = tk.Frame(content, bg="#303036")
        folder_row.pack(fill="x", pady=8)
        self.folder_label = tk.Label(folder_row, text=str(self.current_folder), anchor="w", bg="#303036", fg="#b2b0b8", font=("Consolas", 8))
        self.folder_label.pack(side="left", fill="x", expand=True, padx=8, pady=7)
        ttk.Button(folder_row, text="↗", width=3, style="Cyber.TButton", command=self.choose_folder).pack(side="right", padx=4, pady=3)
        controls = tk.Frame(content, bg="#101020")
        controls.pack(fill="x")
        for label, command in [("◀◀", self.previous_track), ("▶", self.toggle_music), ("▶▶", self.next_track)]:
            ttk.Button(controls, text=label, style="Cyber.TButton", command=command).pack(side="left", padx=2)
        self.shuffle_button = ttk.Button(controls, text="⤨", style="Cyber.TButton", command=self.toggle_shuffle)
        self.shuffle_button.pack(side="left", padx=2)
        self.repeat_button = ttk.Button(controls, text="↻", style="Cyber.TButton", command=self.toggle_repeat)
        self.repeat_button.pack(side="left", padx=2)
        ttk.Button(controls, text="⌫", style="Cyber.TButton", command=self.clear_library).pack(side="left", padx=2)
        self.volume = ttk.Scale(controls, from_=0, to=1, value=self.settings.get("volume", .7), style="Cyber.Horizontal.TScale", command=self.set_volume)
        self.volume.pack(side="left", fill="x", expand=True, padx=8)
        self.music_status = tk.Label(content, text="READY", anchor="w", bg="#101020", fg="#ffd166", font=("Consolas", 8))
        self.music_status.pack(fill="x", pady=(6, 0))

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=str(self.current_folder if self.current_folder.exists() else Path.home()))
        if folder:
            self.current_folder = Path(folder)
            self.folder_label.configure(text=str(self.current_folder))
            self.load_folder()
            self.save_settings()

    def restore_folder_if_available(self):
        if self.current_folder.exists():
            self.load_folder()

    def load_folder(self):
        self.music_files = sorted([path for path in self.current_folder.iterdir() if path.suffix.lower() in self.AUDIO_EXTENSIONS])
        self.music_index = 0
        self.music_status.configure(text=f"{len(self.music_files)} TRACKS READY")
        self.update_music_labels()

    def update_music_labels(self):
        if not self.music_files:
            self.music_name.configure(text="NO AUDIO LOADED")
            self.music_next.configure(text="NEXT // NO NEXT TRACK")
            return
        self.music_name.configure(text=self.music_files[self.music_index].name)
        next_index = (self.music_index + 1) % len(self.music_files)
        self.music_next.configure(text=f"NEXT // {self.music_files[next_index].name}")
        self.music_status.configure(text=f"TRACK {self.music_index + 1} / {len(self.music_files)}")

    def load_current_track(self):
        if not self.music_files or not pygame:
            if not pygame:
                self.music_status.configure(text="INSTALL pygame TO PLAY AUDIO")
            return
        try:
            pygame.mixer.music.load(str(self.music_files[self.music_index]))
            pygame.mixer.music.play()
            self.update_music_labels()
        except pygame.error:
            self.music_status.configure(text="UNABLE TO PLAY FILE")

    def toggle_music(self):
        if not self.music_files or not pygame:
            return
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.music_status.configure(text="PAUSED")
        else:
            try:
                pygame.mixer.music.unpause()
                self.music_status.configure(text="PLAYING")
            except pygame.error:
                self.load_current_track()

    def next_track(self):
        if not self.music_files:
            return
        if self.shuffle_enabled:
            self.music_index = random.randrange(len(self.music_files))
        else:
            self.music_index = (self.music_index + 1) % len(self.music_files)
        self.load_current_track()

    def previous_track(self):
        if not self.music_files:
            return
        self.music_index = (self.music_index - 1) % len(self.music_files)
        self.load_current_track()

    def toggle_shuffle(self):
        self.shuffle_enabled = not self.shuffle_enabled
        self.shuffle_button.configure(text="⤨ ON" if self.shuffle_enabled else "⤨")

    def toggle_repeat(self):
        self.repeat_enabled = not self.repeat_enabled
        self.repeat_button.configure(text="↻ ON" if self.repeat_enabled else "↻")

    def clear_library(self):
        if pygame:
            pygame.mixer.music.stop()
        self.music_files = []
        self.music_index = 0
        self.update_music_labels()
        self.music_status.configure(text="LIBRARY CLEARED")

    def set_volume(self, value):
        if pygame:
            pygame.mixer.music.set_volume(float(value))
        self.save_settings()

    def build_monitor(self):
        frame, content = self.panel(self.root, "◈ SYSTEM MONITOR", 280)
        frame.place(relx=1, y=22, x=-22, anchor="ne", width=280, height=150)
        self.widget_frames["monitor"] = frame
        self.cpu_label = tk.Label(content, bg="#101020", fg=self.colors["cyan"], font=("Consolas", 10))
        self.ram_label = tk.Label(content, bg="#101020", fg=self.colors["cyan"], font=("Consolas", 10))
        self.cpu_label.pack(anchor="w")
        self.ram_label.pack(anchor="w")
        self.update_monitor()

    def update_monitor(self):
        import random as random_module
        self.cpu_label.configure(text=f"CPU  {random_module.randrange(20, 46)}%")
        self.ram_label.configure(text="RAM  browser mode")
        self.root.after(2000, self.update_monitor)

    def build_theme_panel(self):
        frame, content = self.panel(self.root, "◈ THEME MATRIX", 230)
        frame.place(x=22, y=160, width=230, height=145)
        self.widget_frames["theme"] = frame
        for name, colors in [("CYBERPUNK", ("#00eaff", "#ff3b9d")), ("NEON BLUE", ("#55aaff", "#7c5cff")), ("MATRIX", ("#39ff88", "#00c96b")), ("MINIMAL", ("#dddddd", "#888888"))]:
            ttk.Button(content, text=name, style="Cyber.TButton", command=lambda pair=colors: self.set_theme(pair)).pack(fill="x", pady=2)

    def set_theme(self, colors):
        self.colors["cyan"], self.colors["pink"] = colors
        self.build_styles()
        for widget in self.widget_frames.values():
            widget.configure(highlightbackground=self.colors["cyan"])

    def build_dock(self):
        dock = tk.Frame(self.root, bg="#171528", highlightbackground="#254b58", highlightthickness=1)
        dock.place(relx=.5, rely=1, y=-15, anchor="s")
        for key, icon in [("clock", "◷"), ("notes", "✎"), ("music", "♫"), ("monitor", "▥"), ("theme", "◈")]:
            button = ttk.Button(dock, text=icon, width=3, style="Cyber.TButton", command=lambda name=key: self.toggle_widget(name))
            button.pack(side="left", padx=3, pady=4)
            self.widget_buttons[key] = button

    def toggle_widget(self, name):
        frame = self.widget_frames[name]
        if frame.winfo_viewable():
            frame.place_forget()
        else:
            self.place_widget(name)

    def place_widget(self, name):
        placements = {
            "calculator": {"relx": .5, "rely": .5, "anchor": "center", "width": 375, "height": 667},
            "clock": {"x": 22, "y": 22, "width": 280, "height": 120},
            "notes": {"x": 22, "rely": 1, "y": -72, "anchor": "sw", "width": 300, "height": 220},
            "music": {"relx": 1, "rely": 1, "x": -22, "y": -72, "anchor": "se", "width": 410, "height": 265},
            "monitor": {"relx": 1, "y": 22, "x": -22, "anchor": "ne", "width": 280, "height": 150},
            "theme": {"x": 22, "y": 160, "width": 230, "height": 145},
        }
        self.widget_frames[name].place(**placements[name])

    def load_settings(self):
        try:
            self.settings = json.loads(self.SETTINGS_FILE.read_text(encoding="utf-8"))
            saved_folder = self.settings.get("music_folder")
            if saved_folder:
                self.current_folder = Path(saved_folder)
        except (OSError, json.JSONDecodeError):
            self.settings = {}

    def save_settings(self):
        self.settings["notes"] = self.notes.get("1.0", "end-1c") if hasattr(self, "notes") else ""
        self.settings["volume"] = float(self.volume.get()) if hasattr(self, "volume") else .7
        self.settings["music_folder"] = str(self.current_folder)
        try:
            self.SETTINGS_FILE.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")
        except OSError:
            pass

    def close(self):
        self.save_settings()
        if pygame:
            pygame.mixer.quit()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = CyberpunkDesktop(root)
    root.mainloop()

