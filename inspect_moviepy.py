import inspect

from moviepy import ColorClip

try:
    clip = ColorClip(size=(100, 100), color=(255, 0, 0), duration=1)
    sig = inspect.signature(clip.write_gif)
    print(f"write_gif signature: {sig}")
except Exception as e:
    print(f"Error inspecting write_gif: {e}")

