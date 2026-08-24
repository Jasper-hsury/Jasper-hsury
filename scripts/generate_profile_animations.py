#!/usr/bin/env python3
"""Generate the subtle animated GIF used by the GitHub Profile README."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw


FRAME_COUNT = 100
FRAME_DURATION_MS = 80
FULL_WIDTH = 2172
FULL_HEIGHT = 724


def _wave_y(x: float, phase: float, offset: float = 0.0) -> float:
    return 510 + offset + 58 * math.sin(x * 0.0085 + phase)


def _draw_animation_overlay(size: tuple[int, int], frame_index: int) -> Image.Image:
    width, height = size
    scale_x = width / FULL_WIDTH
    scale_y = height / FULL_HEIGHT
    phase = 2 * math.pi * frame_index / FRAME_COUNT
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")

    # Fine contour lines move across the existing lower-left waveform.
    for offset, color in (
        (-18, (53, 91, 75, 18)),
        (0, (168, 117, 79, 17)),
        (18, (53, 91, 75, 14)),
    ):
        points = []
        for original_x in range(0, 930, 9):
            original_y = _wave_y(original_x, phase, offset)
            points.append((round(original_x * scale_x), round(original_y * scale_y)))
        draw.line(points, fill=color, width=max(1, round(2 * scale_x)))

    # Two nodes travel along the contour, fading near their seamless wrap point.
    for progress_offset, color in ((0.0, (168, 117, 79)), (0.47, (53, 91, 75))):
        progress = (frame_index / FRAME_COUNT + progress_offset) % 1.0
        original_x = 70 + 790 * progress
        original_y = _wave_y(original_x, phase, -4 if progress_offset else 10)
        alpha = round(86 * math.sin(math.pi * progress) ** 2)
        x = round(original_x * scale_x)
        y = round(original_y * scale_y)
        radius = max(3, round(5 * scale_x))
        ring = radius + max(2, round(3 * scale_x))
        draw.ellipse((x - ring, y - ring, x + ring, y + ring), outline=(*color, alpha // 3), width=max(1, round(scale_x)))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, alpha))

    # Small orbiting nodes suggest the engineering gear's slow rotation.
    gear_center = (215 * scale_x, 225 * scale_y)
    gear_radius = 120
    for angle_offset in (0.0, math.pi):
        angle = phase + angle_offset
        x = round(gear_center[0] + gear_radius * scale_x * math.cos(angle))
        y = round(gear_center[1] + gear_radius * scale_y * math.sin(angle))
        radius = max(2, round(3 * scale_x))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(168, 117, 79, 42))

    # The music staff breathes almost imperceptibly; the notation remains fixed.
    music_alpha = round(6 + 10 * (0.5 + 0.5 * math.sin(phase)))
    draw.line(
        [(1685 * scale_x, 180 * scale_y), (2040 * scale_x, 180 * scale_y)],
        fill=(168, 117, 79, music_alpha),
        width=max(1, round(2 * scale_x)),
    )

    # A restrained cursor pulse sits beside the existing software detail.
    cursor_alpha = round(8 + 24 * (0.5 + 0.5 * math.sin(phase * 5)) ** 3)
    cursor_box = (
        round(1990 * scale_x),
        round(439 * scale_y),
        round(1993 * scale_x),
        round(459 * scale_y),
    )
    draw.rounded_rectangle(cursor_box, radius=max(1, round(scale_x)), fill=(53, 91, 75, cursor_alpha))

    return overlay


def generate_banner(source: Path, output: Path, width: int) -> None:
    source_image = Image.open(source).convert("RGB")
    if source_image.size != (FULL_WIDTH, FULL_HEIGHT):
        raise ValueError(f"Expected {FULL_WIDTH}x{FULL_HEIGHT} source, got {source_image.size}")

    height = round(width * FULL_HEIGHT / FULL_WIDTH)
    if width == FULL_WIDTH:
        base = source_image
    else:
        base = source_image.resize((width, height), Image.Resampling.LANCZOS)

    palette = base.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
    frames: list[Image.Image] = []
    rgba_base = base.convert("RGBA")

    for frame_index in range(FRAME_COUNT):
        overlay = _draw_animation_overlay(base.size, frame_index)
        composed = Image.alpha_composite(rgba_base, overlay).convert("RGB")
        frames.append(composed.quantize(palette=palette, dither=Image.Dither.NONE))

    output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        disposal=1,
        optimize=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("assets/banner.png"))
    parser.add_argument("--output", type=Path, default=Path("assets/banner-animated.gif"))
    parser.add_argument("--width", type=int, default=FULL_WIDTH)
    args = parser.parse_args()
    generate_banner(args.source, args.output, args.width)


if __name__ == "__main__":
    main()
