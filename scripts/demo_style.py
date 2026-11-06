"""Small, self-contained Pillow/FFmpeg presentation helpers (optional demo extra)."""

import json
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT, FPS = 1920, 1080, 30
BG = "#0b1422"
PANEL = "#111f30"
INK = "#edf3fa"
MUTED = "#9caec2"
GRID = "#293b50"
TEAL = "#56dcc4"
BLUE = "#78adff"
AMBER = "#f3ba70"


@lru_cache(maxsize=64)
def font(size: int, bold: bool = False, mono: bool = False):
    """Load the documented DejaVu fonts or fail rather than silently substitute."""
    name = "DejaVuSansMono" if mono else "DejaVuSans"
    name += "-Bold.ttf" if bold else ".ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError as error:
        raise RuntimeError(
            "Install DejaVu fonts (Ubuntu: fonts-dejavu-core)"
        ) from error


def text(draw, xy, value, size=28, fill=INK, *, bold=False, mono=False, anchor="lt"):
    """Draw text at its top edge, checking the frame boundary for clipping."""
    face = font(size, bold, mono)
    box = draw.textbbox(xy, str(value), font=face, anchor=anchor)
    if box[0] < 0 or box[1] < 0 or box[2] > WIDTH or box[3] > HEIGHT:
        raise ValueError(f"Text outside frame: {value!r}, {box}")
    draw.text(xy, str(value), font=face, fill=fill, anchor=anchor)


def ease(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def panel(draw, box, fill=PANEL):
    draw.rounded_rectangle(box, radius=20, fill=fill, outline=GRID, width=2)


def label(draw, x, y, value, fill=MUTED):
    text(draw, (x, y), value.upper(), 22, fill, bold=True)


def metric(draw, x, y, value, caption, fill=TEAL, size=54):
    text(draw, (x, y), value, size, fill, bold=True)
    text(draw, (x, y + size + 16), caption, 24, MUTED)


def base(project, number, title, subtitle, chapters, t, duration, accent, note):
    """Create a consistent portfolio frame with a timed chapter rail."""
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((80, 41, 92, 63), radius=4, fill=accent)
    text(draw, (110, 40), f"OJOPS  /  {project.upper()}", 22, MUTED, bold=True)
    text(
        draw,
        (1840, 40),
        f"COMPUTATIONAL PORTFOLIO   {number:02d} / 03",
        20,
        MUTED,
        anchor="rt",
        mono=True,
    )
    text(draw, (80, 94), title, 54, bold=True)
    text(draw, (80, 170), subtitle, 27, MUTED)
    draw.line((80, 215, 1840, 215), fill=GRID, width=2)
    for i, (start, caption) in enumerate(chapters):
        end = chapters[i + 1][0] if i + 1 < len(chapters) else duration
        x = 80 + i * 446
        draw.line((x, 958, x + 420, 958), fill=GRID, width=4)
        if t >= start:
            amount = min(1, (t - start) / (end - start))
            draw.line((x, 958, x + 420 * amount, 958), fill=accent, width=4)
        text(
            draw,
            (x, 977),
            f"{i + 1:02d}  {caption}",
            21,
            accent if start <= t < end else MUTED,
        )
    text(draw, (80, 1030), note, 20, MUTED)
    return image, draw


def chart(draw, box, series, limits, *, progress=1.0, percent=False, ticks=4):
    """Plot observed values with straight segments and a shared numerical axis."""
    x0, y0, x1, y1 = box
    low, high = limits
    for i in range(ticks + 1):
        value = low + (high - low) * i / ticks
        y = y1 - (y1 - y0) * i / ticks
        draw.line((x0, y, x1, y), fill=GRID, width=1)
        formatted = f"{value:.1%}" if percent else f"{value:.2f}"
        text(draw, (x0 - 16, y), formatted, 20, MUTED, mono=True, anchor="rm")
    for _, values, colour in series:
        points = [
            (
                x0 + i / (len(values) - 1) * (x1 - x0),
                y1 - (value - low) / (high - low) * (y1 - y0),
            )
            for i, value in enumerate(values)
        ]
        at = max(0.0, min(1.0, progress)) * (len(points) - 1)
        last = int(at)
        shown = points[: last + 1]
        if last + 1 < len(points):
            weight = at - last
            shown.append(
                tuple(
                    a + weight * (b - a) for a, b in zip(points[last], points[last + 1])
                )
            )
        if len(shown) > 1:
            draw.line(shown, fill=colour, width=5, joint="curve")
        x, y = shown[-1]
        draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=colour)


def legend(draw, x, y, items, gap=300):
    for i, (caption, colour) in enumerate(items):
        at = x + i * gap
        draw.line((at, y + 12, at + 28, y + 12), fill=colour, width=5)
        text(draw, (at + 40, y), caption, 23, MUTED)


def save_data(path: Path, data: dict) -> None:
    """Serialize Decimal values as exact strings, never rounded float inputs."""
    path.write_text(json.dumps(data, indent=2, default=str, allow_nan=False) + "\n")


def encode(frame, output: Path, duration: int) -> None:
    """Stream full-HD RGB frames to an H.264 MP4 without intermediate images."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("Install FFmpeg with the libx264 encoder")
    command = [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{WIDTH}x{HEIGHT}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-crf",
        "21",
        "-preset",
        "medium",
        "-threads",
        "2",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]
    with subprocess.Popen(command, stdin=subprocess.PIPE) as process:
        try:
            for index in range(duration * FPS):
                process.stdin.write(frame(index / FPS).tobytes())
                if index % (FPS * 6) == 0:
                    print(f"Rendered {index // FPS}/{duration} seconds", flush=True)
        finally:
            process.stdin.close()
        if process.wait() != 0:
            raise RuntimeError("FFmpeg encoding failed")


def preview(video: Path, output: Path, start: float, duration: float) -> None:
    """Make a small looping preview with a palette derived from the real video."""
    filters = (
        "fps=10,scale=768:-1:flags=lanczos,split[a][b];"
        "[a]palettegen=stats_mode=full:reserve_transparent=0[p];"
        "[b][p]paletteuse=dither=bayer:bayer_scale=3"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-ss",
            str(start),
            "-t",
            str(duration),
            "-i",
            str(video),
            "-filter_complex",
            filters,
            "-loop",
            "0",
            str(output),
        ],
        check=True,
    )
