import datetime
import inspect
import os
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Any, Callable, Dict, Optional

import proglog
from moviepy import VideoFileClip
from tkinterdnd2 import DND_FILES, TkinterDnD

__version__ = "0.1.0"
MAX_GUI_DURATION = 30  # seconds; CLI has no limit
WARN_SIZE_MB = 100  # warn if estimated GIF exceeds this


class GifConverterLogic:
    """
    Handles the business logic for converting videos to GIFs.
    """
    def validate_inputs(self, resize_percentage: int, fps: str) -> tuple[float, int]:
        """
        Validates user inputs for resize percentage and FPS.
        """
        try:
            r_val = float(resize_percentage)
            if not (1 <= r_val <= 100):
                 raise ValueError("Resize percentage must be between 1 and 100.")
            resize_val = r_val / 100.0
        except ValueError:
             raise ValueError("Resize percentage must be a valid number.")

        try:
            fps_val = int(fps)
            if fps_val <= 0:
                raise ValueError("FPS must be a positive integer.")
        except ValueError:
             raise ValueError("FPS must be a valid integer.")
        
        return resize_val, fps_val

    def estimate_gif_size(self, duration: float, width: int, height: int, fps: int) -> float:
        """
        Rough estimate of output GIF size in MB (uncompressed frame buffer approx).
        """
        frames = int(duration * fps)
        bytes_per_frame = width * height * 3  # RGB
        total_bytes = frames * bytes_per_frame
        return total_bytes / (1024 * 1024)

    def validate_times(self, start: str, end: str, duration: Optional[float]) -> tuple[Optional[float], Optional[float]]:
        """
        Validate optional start/end times (in seconds). If duration is provided, clamp to [0, duration].
        """
        def parse_time(val: str) -> Optional[float]:
            v = val.strip()
            if v == "":
                return None
            try:
                f = float(v)
                if f < 0:
                    raise ValueError("Time must be >= 0.")
                return f
            except ValueError:
                raise ValueError("Start/End times must be numbers (seconds).")

        s = parse_time(start)
        e = parse_time(end)

        if duration is not None:
            if s is not None:
                s = max(0.0, min(s, duration))
            if e is not None:
                e = max(0.0, min(e, duration))

        if s is not None and e is not None and e < s:
            raise ValueError("End time must be greater than start time.")

        return s, e

    def has_ffmpeg(self) -> bool:
        """Return True if ffmpeg is available on PATH."""
        return shutil.which("ffmpeg") is not None

    def get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        Extracts metadata from the video file.
        """
        if not video_path or not os.path.exists(video_path):
            return {}

        metadata = {}
        try:
            # File Size
            size_bytes = os.path.getsize(video_path)
            metadata['size_mb'] = round(size_bytes / (1024 * 1024), 2)

            # Metadata from MoviePy
            with VideoFileClip(video_path) as clip:
                metadata['resolution'] = clip.size
                metadata['duration'] = round(clip.duration, 2)
                metadata['fps'] = clip.fps
            
            return metadata
        except Exception as e:
            raise e

    def convert_video_to_gif(
        self, 
        video_path: str, 
        output_path: str,
        resize_val: float, 
        fps_val: int, 
        progress_callback: Optional[Callable[[str], None]] = None,
        logger=None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        program: str = "imageio",
        loop: Optional[int] = None,
    ) -> str:
        if not video_path or not os.path.exists(video_path):
            raise FileNotFoundError("Video file not found or not selected.")
        
        # Ensure output has .gif extension
        if not output_path.lower().endswith(".gif"):
            output_path += ".gif"

        try:
            if progress_callback:
                progress_callback("Loading video...")

            # Ensure the clip is properly closed using a context manager
            with VideoFileClip(video_path) as clip:
                if progress_callback:
                    progress_callback(f"Resizing video ({int(resize_val*100)}%)...")

                # Support both MoviePy 2.x (`resized`) and older (`resize`) APIs
                if hasattr(clip, "resized"):
                    clip_resized = clip.resized(resize_val)
                else:
                    clip_resized = clip.resize(resize_val)

                if progress_callback:
                    progress_callback(f"Writing GIF (FPS: {fps_val})...")

                # Trim if requested (support both old and new MoviePy APIs)
                if start_time is not None or end_time is not None:
                    st = start_time if start_time is not None else 0
                    et = end_time if end_time is not None else clip_resized.duration
                    if hasattr(clip_resized, "subclip"):
                        clip_resized = clip_resized.subclip(st, et)
                    elif hasattr(clip_resized, "subclipped"):
                        clip_resized = clip_resized.subclipped(st, et)

                # Choose program, fallback to imageio if ffmpeg missing
                use_program = program
                if program == "ffmpeg" and not self.has_ffmpeg():
                    use_program = "imageio"
                    if progress_callback:
                        progress_callback("FFmpeg not found. Falling back to imageio.")

                # Use provided logger and safe kwargs
                write_kwargs: Dict[str, Any] = {"fps": fps_val}
                # Only include supported parameters based on signature
                sig = inspect.signature(clip_resized.write_gif)
                if "logger" in sig.parameters:
                    write_kwargs["logger"] = logger
                if loop is not None and "loop" in sig.parameters and use_program == "imageio":
                    write_kwargs["loop"] = loop
                if "program" in sig.parameters:
                    write_kwargs["program"] = use_program
                clip_resized.write_gif(output_path, **write_kwargs)

            return output_path

        except Exception as e:
            raise e

class UILogger(proglog.ProgressBarLogger):
    """
    Custom logger to redirect MoviePy progress to UI components.
    """
    def __init__(self, log_callback: Callable[[str], None], progress_callback: Callable[[float], None]):
        super().__init__()
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.last_message = ""

    def callback(self, **changes):
        # Every time the logger is updated, look for bars
        for (task, progress_info) in self.bars.items():
            # progress_info is a dictionary {'index': ..., 'total': ..., ...}
            # We want to find the main writing task usually
            total = progress_info.get('total')
            index = progress_info.get('index')
            if total and index is not None:
                percent = (index / total) * 100
                self.progress_callback(percent)
        
        # Capture messages
        message = changes.get('message')
        if message and message != self.last_message:
            self.log_callback(f"[MoviePy] {message}")
            self.last_message = message

class GifConverterApp:
    """
    GUI for the Video to GIF Converter.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("pyShortVid2Gif-Engine")
        self.root.geometry("500x700") # Increased height for new fields
        
        self.logic = GifConverterLogic()

        # Layout variables
        self.video_path: str = ""
        self.output_dir: str = ""
        self.video_metadata: Dict[str, Any] = {}
        
        # Configure DND
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.drop_video)

        self.create_widgets()
        self.log_message("Application started. Ready.")

    def create_widgets(self):
        # 1. Header / Instruction
        lbl_instr = tk.Label(self.root, text="Drag & Drop a video here or click Select", font=("Arial", 12, "bold"))
        lbl_instr.pack(pady=10)

        # 2. File Selection
        self.btn_select = tk.Button(self.root, text="Select Video", command=self.select_video, width=20, bg="#e1e1e1")
        self.btn_select.pack(pady=5)

        self.label_file = tk.Label(self.root, text="No file selected", fg="gray", font=("Arial", 9))
        self.label_file.pack(pady=5)
        
        # 2.5 File Info (New)
        self.frame_info = tk.LabelFrame(self.root, text="File Info", padx=10, pady=5)
        self.frame_info.pack(pady=5, fill="x", padx=20)
        
        # Grid layout for info
        self.lbl_size = tk.Label(self.frame_info, text="Size: -")
        self.lbl_size.grid(row=0, column=0, padx=10, sticky="w")
        
        self.lbl_res = tk.Label(self.frame_info, text="Res: -")
        self.lbl_res.grid(row=0, column=1, padx=10, sticky="w")
        
        self.lbl_fps = tk.Label(self.frame_info, text="FPS: -")
        self.lbl_fps.grid(row=0, column=2, padx=10, sticky="w")
        
        self.lbl_dur = tk.Label(self.frame_info, text="Dur: -")
        self.lbl_dur.grid(row=0, column=3, padx=10, sticky="w")

        # Estimated frames/info
        self.lbl_est = tk.Label(self.frame_info, text="Est frames: -")
        self.lbl_est.grid(row=1, column=0, padx=10, sticky="w")


        # 3. Settings Frame
        self.frame_settings = tk.LabelFrame(self.root, text="Settings", padx=10, pady=10)
        self.frame_settings.pack(pady=10, fill="x", padx=20)
        
        # Output Name (New)
        tk.Label(self.frame_settings, text="Output Name:").grid(row=0, column=0, sticky="w")
        self.entry_output = tk.Entry(self.frame_settings, width=30)
        self.entry_output.grid(row=0, column=1, padx=10, sticky="w", columnspan=2)

        # Output Directory Picker (New)
        tk.Label(self.frame_settings, text="Output Dir:").grid(row=1, column=0, sticky="w")
        self.entry_outdir = tk.Entry(self.frame_settings, width=24)
        self.entry_outdir.grid(row=1, column=1, padx=10, sticky="w")
        self.btn_outdir = tk.Button(self.frame_settings, text="Choose...", command=self.choose_output_dir)
        self.btn_outdir.grid(row=1, column=2, sticky="w")

        # Resize Slider
        tk.Label(self.frame_settings, text="Resize:").grid(row=2, column=0, sticky="w", pady=5)
        self.resize_var = tk.IntVar(value=50)
        self.scale_resize = tk.Scale(self.frame_settings, from_=10, to=100, orient=tk.HORIZONTAL, variable=self.resize_var, length=200, label="%")
        self.scale_resize.grid(row=2, column=1, padx=10, sticky="w", columnspan=2)

        # FPS Entry
        tk.Label(self.frame_settings, text="FPS:").grid(row=3, column=0, sticky="w", pady=5)
        self.entry_fps = tk.Entry(self.frame_settings, width=10)
        self.entry_fps.insert(0, "15") 
        self.entry_fps.grid(row=3, column=1, padx=10, sticky="w", pady=5)

        # Start/End Trim (New)
        tk.Label(self.frame_settings, text="Start (s):").grid(row=4, column=0, sticky="w")
        self.entry_start = tk.Entry(self.frame_settings, width=10)
        self.entry_start.grid(row=4, column=1, sticky="w")

        tk.Label(self.frame_settings, text="End (s):").grid(row=4, column=2, sticky="w")
        self.entry_end = tk.Entry(self.frame_settings, width=10)
        self.entry_end.grid(row=4, column=3, sticky="w")

        # Program selection (New)
        tk.Label(self.frame_settings, text="Program:").grid(row=5, column=0, sticky="w")
        self.program_var = tk.StringVar(value="imageio")
        self.combo_program = ttk.Combobox(self.frame_settings, textvariable=self.program_var, values=["imageio", "ffmpeg"], state="readonly", width=10)
        self.combo_program.grid(row=5, column=1, sticky="w")

        # Loop option (New)
        self.loop_var = tk.BooleanVar(value=True)
        self.chk_loop = tk.Checkbutton(self.frame_settings, text="Loop forever (imageio)", variable=self.loop_var)
        self.chk_loop.grid(row=5, column=2, columnspan=2, sticky="w")

        # 4. Action & Progress
        self.btn_convert = tk.Button(self.root, text="Convert to GIF", command=self.start_conversion_thread, state=tk.DISABLED, bg="#dddddd", font=("Arial", 10, "bold"))
        self.btn_convert.pack(pady=10, fill="x", padx=50)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(pady=5, fill="x", padx=20)

        self.status_label = tk.Label(self.root, text="")
        self.status_label.pack()

        # 5. Log Console
        lbl_log = tk.Label(self.root, text="Log Console:", anchor="w")
        lbl_log.pack(fill="x", padx=20, pady=(10, 0))
        self.console = scrolledtext.ScrolledText(self.root, height=8, state='disabled', font=("Consolas", 8))
        self.console.pack(fill="both", expand=True, padx=20, pady=5)

    def log_message(self, msg: str, error=False):
        """Thread-safe logging to the text widget."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {msg}\n"
        
        def _log():
            self.console.config(state='normal')
            tag = "error" if error else "info"
            self.console.tag_config("error", foreground="red")
            self.console.tag_config("info", foreground="black")
            
            self.console.insert(tk.END, full_msg, tag)
            self.console.see(tk.END)
            self.console.config(state='disabled')
        
        self.root.after(0, _log)

    def update_progress(self, percent: float):
        self.progress_var.set(percent)

    def drop_video(self, event):
        file_path = event.data
        # Clean up path (sometimes DnD returns {path} with braces)
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        
        self.set_file(file_path)

    def select_video(self):
        file_path = filedialog.askopenfilename(filetypes=[
            ("Video files", "*.mp4;*.mov;*.avi;*.mkv;*.webm;*.flv;*.wmv;*.m4v"),
            ("All files", "*.*")
        ])
        if file_path:
            self.set_file(file_path)

    def set_file(self, file_path):
        if os.path.isfile(file_path):
            self.video_path = file_path
            self.label_file.config(text=os.path.basename(file_path), fg="black")
            
            # Auto-fill output name
            default_out = os.path.splitext(os.path.basename(file_path))[0] + ".gif"
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, default_out)
            # Default outdir same as video dir
            self.output_dir = os.path.dirname(file_path)
            self.entry_outdir.delete(0, tk.END)
            self.entry_outdir.insert(0, self.output_dir)
            
            # Fetch and display metadata
            self.log_message(f"Selected file: {file_path}")
            self.fetch_metadata_thread(file_path)
            
            self.btn_convert.config(state=tk.NORMAL, bg="#4CAF50", fg="white")
            self.status_label.config(text="Ready to convert", fg="blue")
            self.progress_var.set(0)
        else:
            self.log_message(f"Invalid file dropped: {file_path}", error=True)

    def fetch_metadata_thread(self, file_path):
        """Fetch metadata in background to avoid freezing UI."""
        def _fetch():
            try:
                self.root.after(0, lambda: self.status_label.config(text="Reading metadata...", fg="blue"))
                meta = self.logic.get_video_metadata(file_path)
                self.video_metadata = meta
                
                # Check if exceeds GUI limit
                duration = meta.get('duration', 0)
                exceeds_limit = duration > MAX_GUI_DURATION
                
                # Update UI in main thread
                def _update_ui():
                    self.lbl_size.config(text=f"Size: {meta.get('size_mb', '?')} MB")
                    self.lbl_res.config(text=f"Res: {meta.get('resolution', '?')}")
                    self.lbl_fps.config(text=f"FPS: {meta.get('fps', '?')}")
                    self.lbl_dur.config(text=f"Dur: {meta.get('duration', '?')}s")
                    
                    # Warn if duration exceeds 30s
                    if exceeds_limit:
                        self.lbl_est.config(text=f"⚠ Over {MAX_GUI_DURATION}s: use CLI", fg="red")
                        self.status_label.config(text=f"Video exceeds {MAX_GUI_DURATION}s; use CLI for large files", fg="orange")
                        self.btn_convert.config(state=tk.DISABLED, bg="#cccccc")
                        self.log_message(f"Video duration {duration}s exceeds GUI limit of {MAX_GUI_DURATION}s. Use CLI for better performance.")
                    else:
                        try:
                            fps_sel = int(self.entry_fps.get())
                            frames_est = int((meta.get('duration') or 0) * fps_sel)
                            # Estimate size with current resize
                            resize_pct = self.resize_var.get() / 100.0
                            res = meta.get('resolution', [0, 0])
                            w, h = int(res[0] * resize_pct), int(res[1] * resize_pct)
                            size_est = self.logic.estimate_gif_size(meta.get('duration', 0), w, h, fps_sel)
                            size_text = f"Est {size_est:.1f}MB"
                            if size_est > WARN_SIZE_MB:
                                size_text += " ⚠"
                            self.lbl_est.config(text=size_text)
                        except Exception:
                            self.lbl_est.config(text="Est frames: -")
                        self.status_label.config(text="Metadata loaded", fg="green")
                    self.log_message(f"Metadata loaded: {meta}")
                
                self.root.after(0, _update_ui)
            except Exception as e:
                self.log_message(f"Failed to read metadata: {e}", error=True)
                self.root.after(0, lambda: self.status_label.config(text="Metadata error", fg="red"))

        threading.Thread(target=_fetch, daemon=True).start()

    def choose_output_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.output_dir = d
            self.entry_outdir.delete(0, tk.END)
            self.entry_outdir.insert(0, d)

    def start_conversion_thread(self):
        # Build output path and check overwrite
        output_name = self.entry_output.get().strip() or "output.gif"
        outdir = self.entry_outdir.get().strip() or (self.output_dir or os.path.dirname(self.video_path))
        output_path = os.path.join(outdir, output_name)

        if os.path.exists(output_path):
            if not messagebox.askyesno("Overwrite?", f"{output_path} exists. Overwrite?"):
                return

        self.btn_convert.config(state=tk.DISABLED)
        threading.Thread(target=lambda: self.convert(output_path), daemon=True).start()

    def convert(self, output_path: Optional[str] = None):
        try:
            self.log_message("Starting conversion...")
            self.root.after(0, lambda: self.status_label.config(text="Converting...", fg="blue"))
            
            resize_in = self.resize_var.get()
            fps_in = self.entry_fps.get()
            output_name = self.entry_output.get().strip()
            
            if not output_name:
                output_name = "output.gif"

            # Construct output path (same dir as video) if not provided
            if output_path is None:
                output_dir = os.path.dirname(self.video_path)
                output_path = os.path.join(output_dir, output_name)
            
            # Helper to bridge logger calls to main thread UI
            def ui_progress_callback(percent):
                self.root.after(0, lambda: self.update_progress(percent))
            
            logger = UILogger(
                log_callback=self.log_message,
                progress_callback=ui_progress_callback
            )

            resize_val, fps_val = self.logic.validate_inputs(resize_in, fps_in)
            
            # Validate optional times
            duration = self.video_metadata.get('duration')
            start_val, end_val = self.logic.validate_times(self.entry_start.get(), self.entry_end.get(), duration)

            # Program and loop
            program_sel = self.program_var.get()
            loop_val = 0 if self.loop_var.get() else None

            final_output_path = self.logic.convert_video_to_gif(
                self.video_path,
                output_path, 
                resize_val, 
                fps_val, 
                progress_callback=lambda msg: self.log_message(msg),
                logger=logger,
                start_time=start_val,
                end_time=end_val,
                program=program_sel,
                loop=loop_val
            )

            self.root.after(0, lambda: self.status_label.config(text="Conversion Complete!", fg="green"))
            self.log_message(f"SUCCESS: GIF saved at {final_output_path}")
            self.root.after(0, lambda: messagebox.showinfo("Success", f"GIF created successfully!\n\n{final_output_path}"))

        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text="Error", fg="red"))
            error_msg = str(e)
            self.log_message(f"ERROR: {error_msg}", error=True)
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("Error", msg))
        
        finally:
            self.root.after(0, lambda: self.btn_convert.config(state=tk.NORMAL))

if __name__ == "__main__":
    # Use TkinterDnD.Tk instead of tk.Tk
    root = TkinterDnD.Tk()
    # Warn if ffmpeg missing
    if not GifConverterLogic().has_ffmpeg():
        messagebox.showwarning("FFmpeg Missing", "FFmpeg not found on PATH. You can still use 'imageio' program, but 'ffmpeg' option will be unavailable.")
    app = GifConverterApp(root)
    root.mainloop()
