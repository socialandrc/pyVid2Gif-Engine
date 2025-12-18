import math
import os
from pathlib import Path

import pytest

# Generate a small input GIF using ColorClip (no ffmpeg required)
from moviepy import ColorClip

# Import logic from the app
from localvideo import GifConverterLogic


@pytest.fixture()
def tmp_paths(tmp_path: Path):
    input_gif = tmp_path / "input.gif"
    output_gif = tmp_path / "output.gif"

    # Create 1-second red square GIF at 100x100, fps=10
    clip = ColorClip(size=(100, 100), color=(255, 0, 0), duration=1)
    # Use only supported args; loop optional depending on version
    clip.write_gif(str(input_gif), fps=10)
    return str(input_gif), str(output_gif)


def test_trim_and_resize_conversion(tmp_paths):
    input_gif, output_gif = tmp_paths
    logic = GifConverterLogic()

    # Validate we have metadata for the input
    meta_in = logic.get_video_metadata(input_gif)
    assert meta_in.get("resolution") == [100, 100] or tuple(meta_in.get("resolution", ())) == (100, 100)
    assert math.isclose(meta_in.get("duration", 0), 1.0, rel_tol=0.2, abs_tol=0.3)

    # Convert with trimming 0.2s -> 0.8s and 50% resize
    result_path = logic.convert_video_to_gif(
        video_path=input_gif,
        output_path=output_gif,
        resize_val=0.5,
        fps_val=10,
        progress_callback=None,
        logger=None,
        start_time=0.2,
        end_time=0.8,
        program="imageio",
        loop=0,
    )

    assert os.path.exists(result_path)

    # Check metadata of output
    meta_out = logic.get_video_metadata(result_path)
    res_out = meta_out.get("resolution")
    # Resolution may be list or tuple depending on version
    if isinstance(res_out, list):
        res_out = tuple(res_out)
    assert res_out == (50, 50)

    # Duration should be ~0.6s
    dur_out = meta_out.get("duration", 0)
    assert 0.4 <= dur_out <= 0.9

