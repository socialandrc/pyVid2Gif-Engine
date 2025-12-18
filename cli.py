import argparse
import inspect
import os
import shutil
from typing import Optional

from moviepy import VideoFileClip

__version__ = "0.1.0"


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None

def convert_video_to_gif_cli(
    video_path: str,
    output_path: Optional[str],
    resize_percentage: int,
    fps: int,
    start: Optional[float],
    end: Optional[float],
    program: str,
    loop_forever: bool,
):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    if output_path is None:
        base = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(os.path.dirname(video_path), base + ".gif")

    if not output_path.lower().endswith('.gif'):
        output_path += '.gif'

    resize_val = max(1, min(resize_percentage, 100)) / 100.0

    use_program = program
    if program == "ffmpeg" and not has_ffmpeg():
        print("[warn] FFmpeg not found. Falling back to imageio.")
        use_program = "imageio"

    with VideoFileClip(video_path) as clip:
        # Resize (MoviePy 2.x: resized)
        if hasattr(clip, "resized"):
            clip_resized = clip.resized(resize_val)
        else:
            clip_resized = clip.resize(resize_val)

        # Trim with API compatibility
        if start is not None or end is not None:
            st = start if start is not None else 0
            et = end if end is not None else clip_resized.duration
            if hasattr(clip_resized, "subclip"):
                clip_resized = clip_resized.subclip(st, et)
            elif hasattr(clip_resized, "subclipped"):
                clip_resized = clip_resized.subclipped(st, et)

        # Build kwargs based on supported signature
        kwargs = {"fps": fps}
        sig = inspect.signature(clip_resized.write_gif)
        if loop_forever and "loop" in sig.parameters and use_program == "imageio":
            kwargs["loop"] = 0
        if "program" in sig.parameters:
            kwargs["program"] = use_program
        clip_resized.write_gif(output_path, **kwargs)

    print(f"[ok] GIF saved: {output_path}")


def generate_test_gif(output_path: str = "test.gif"):
    from moviepy import ColorClip
    clip = ColorClip(size=(100, 100), color=(255, 0, 0), duration=1)
    # Build kwargs compatibly
    sig = inspect.signature(clip.write_gif)
    kwargs = {"fps": 10}
    if "loop" in sig.parameters:
        kwargs["loop"] = 0
    clip.write_gif(output_path, **kwargs)
    print(f"[ok] Test GIF generated: {output_path}")


def main():
    p = argparse.ArgumentParser(description="Headless Video->GIF converter")
    p.add_argument("video", nargs="?", help="Path to input video")
    p.add_argument("--output", "-o", help="Output GIF path")
    p.add_argument("--resize", type=int, default=50, help="Resize percentage 1-100")
    p.add_argument("--fps", type=int, default=15, help="Frames per second")
    p.add_argument("--start", type=float, help="Start time in seconds")
    p.add_argument("--end", type=float, help="End time in seconds")
    p.add_argument("--program", choices=["imageio", "ffmpeg"], default="imageio")
    p.add_argument("--loop", action="store_true", help="Loop forever (imageio only)")
    p.add_argument("--test", action="store_true", help="Generate a small test GIF without input video")

    args = p.parse_args()

    if args.test:
        generate_test_gif(args.output or "test.gif")
        return

    if not args.video:
        p.error("video path required unless --test is used")

    convert_video_to_gif_cli(
        video_path=args.video,
        output_path=args.output,
        resize_percentage=args.resize,
        fps=args.fps,
        start=args.start,
        end=args.end,
        program=args.program,
        loop_forever=args.loop,
    )

if __name__ == "__main__":
    main()

