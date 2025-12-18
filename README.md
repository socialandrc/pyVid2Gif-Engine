# pyShortVid2Gif-Engine: Video to GIF Converter

[![CI](https://github.com/socialandrc/pyShortVid2Gif-Engine/actions/workflows/lint-test.yml/badge.svg?branch=main)](https://github.com/socialandrc/pyShortVid2Gif-Engine/actions/workflows/lint-test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10–3.12](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](#)

A simple GUI and CLI for converting videos to GIFs using MoviePy.

## Prerequisites

- Python 3.10+
- FFmpeg (optional, recommended for better performance)

### Install FFmpeg (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

## Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## GUI Usage

```bash
python localvideo.py
```

**GUI Limitation:** Videos longer than **30 seconds** are disabled in the GUI. This is by design to prevent system overload and excessive file sizes. For longer videos, use the CLI.

- Drag & drop a video or select via dialog.
- Configure:
  - Output name and directory
  - Resize percentage
  - FPS
  - Optional start/end trim
  - Program: `imageio` (no FFmpeg needed) or `ffmpeg`
  - Loop forever (imageio only)
- Watch real-time estimated file size and frame count.
- Convert and watch progress. If FFmpeg is missing, the app will warn and fall back to `imageio` when needed.

> **Tip:** Use the CLI for videos longer than 30 seconds or if you have large files and want full control.

## CLI Usage

```bash
python cli.py /path/to/video.mp4 \
  --output out.gif \
  --resize 50 \
  --fps 15 \
  --start 2 --end 8 \
  --program imageio \
  --loop
```

### Smoke Test (no input video)

```bash
python cli.py --test --output test.gif
```

Generates a 1s red square GIF to verify environment.

## Limitations & Notes

- **GUI**: Videos longer than 30 seconds are not allowed (disabled button) to prevent system overload and excessive GIF file sizes. Use the **CLI** for longer videos at your discretion.
- **Output Size**: Large videos with high FPS can produce very large GIF files. The GUI estimates output size; watch for warnings.
- **Program**:
  - `imageio` works without FFmpeg but may be slower for large videos and produce larger files.
  - `ffmpeg` is faster and produces smaller files; the app falls back to `imageio` if unavailable.
- **Performance**: Trimming long videos or very high resolutions may take time. Consider reducing FPS or resize percentage.

