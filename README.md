# ---

**pyShortVid2Gif-Engine**

A simple GUI and CLI for converting videos to GIFs using MoviePy. Ideal for short videos and clips.

## ---

**✨ Features**

* **GUI**: Drag-and-drop interface with live file size and frame count estimation.  
* **CLI**: Command-line control for batch processing and long videos.  
* **Flexible Backends**: Use imageio (no dependencies) or ffmpeg (faster, smaller files).  
* **Precision Trimming**: Optional start/end time control.  
* **Optimization**: Adjustable resize percentage and FPS control.  
* **Cross-platform**: Seamlessly runs on Windows, macOS, and Linux.

## ---

**🚀 Getting Started**

### **Prerequisites**

* **Python**: 3.10, 3.11, or 3.12 (Python 3.13+ is currently not recommended due to Pillow compatibility).  
* **FFmpeg (Recommended)**: For significantly faster processing and smaller files.

### **Installation**

1. **Clone the repository:**  
   Bash  
   git clone https://github.com/socialandrc/pyShortVid2Gif-Engine.git  
   cd pyShortVid2Gif-Engine

2. **Install dependencies:**  
   Bash  
   pip install \-r requirements.txt

3. **Install FFmpeg (Optional but Recommended):**  
   * **Ubuntu/Debian:** sudo apt-get install ffmpeg  
   * **macOS:** brew install ffmpeg  
   * **Windows:** Download via [Gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or use winget install ffmpeg.

## ---

**💻 Usage**

### **GUI Mode**

Best for visual editing and quick estimates.

Bash

python localvideo.py

**Note:** The GUI limits video length to **30 seconds** to prevent system hangs. For longer clips, please use the CLI.

### **CLI Mode**

Best for automation and handling larger files.

Bash

\# Basic usage  
python cli.py /path/to/video.mp4 \--output out.gif

\# Full optimization  
python cli.py /path/to/video.mp4 \\  
  \--output out.gif \\  
  \--resize 50 \\  
  \--fps 15 \\  
  \--start 2 \\  
  \--end 8 \\  
  \--program ffmpeg \\  
  \--loop

\# Run a smoke test to verify environment  
python cli.py \--test \--output test.gif

#### **CLI Options Reference**

| Option | Type | Default | Description |
| :---- | :---- | :---- | :---- |
| input | str | *Required* | Path to input video file |
| \--output, \-o | str | out.gif | Output GIF filename |
| \--resize, \-r | int | 100 | Resize percentage (1–100) |
| \--fps, \-f | int | 10 | Frames per second |
| \--start, \-s | float | \- | Start trim time (seconds) |
| \--end, \-e | float | \- | End trim time (seconds) |
| \--program, \-p | str | imageio | Backend: imageio or ffmpeg |
| \--loop | flag | False | Loop GIF forever (imageio only) |
| \--test | flag | False | Generate test GIF (no input needed) |

## ---

**🛠 Project Structure**

Plaintext

pyShortVid2Gif-Engine/  
├── .github/workflows/      \# CI/CD configurations  
├── tests/                  \# Unit tests  
├── cli.py                  \# CLI entry point  
├── localvideo.py           \# GUI application (Tkinter/CustomTkinter)  
├── pyproject.toml          \# Project metadata  
├── requirements.txt        \# Python dependencies  
└── LICENSE                 \# MIT License

## ---

**⚠️ Performance & Troubleshooting**

### **Backend Comparison**

* **ffmpeg**: Recommended. Faster encoding and better compression.  
* **imageio**: Best for portability. No external software required, but results in larger files.

### **Common Issues**

| Issue | Solution |
| :---- | :---- |
| **"FFmpeg not found"** | Install FFmpeg system-wide or switch to \--program imageio. |
| **Pillow build fails** | Ensure you are on Python 3.10–3.12 or install Visual C++ Build Tools. |
| **Large GIF size** | Lower the FPS, increase the Resize percentage, or trim the clip. |

## ---

**🤝 Contributing**

Contributions are welcome\!

1. Fork the repo.  
2. Create a feature branch (git checkout \-b feature/AmazingFeature).  
3. Commit your changes (git commit \-m 'Add some AmazingFeature').  
4. Push to the branch (git push origin feature/AmazingFeature).  
5. Open a Pull Request.

**Author:** socialandrc