#!/usr/bin/env python3
"""Generate the subtle animated GIF used by the GitHub Profile README."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw


FRAME_COUNT = 72
FRAME_DURATION_MS = 80
FULL_WIDTH = 2172
FULL_HEIGHT = 724


def _wave_y(x: float, phase: float, offset: float = 0.0) -> float:
    amplitude = 64 + 10 * math.sin(phase * 2)
    y = 510 + offset + amplitude * math.sin(x * 0.0085 + phase)
    return max(y, 455) if x > 560 else y


def _signal_position(progress: float, phase: float) -> tuple[float, float]:
    """Follow the banner's visual flow without crossing the fixed title."""
    if progress < 0.44:
        local = progress / 0.44
        x = 70 + 850 * local
        return x, _wave_y(x, phase, 8)

    if progress < 0.72:
        local = (progress - 0.44) / 0.28
        x = 920 + 600 * local
        return x, 585 + 22 * math.sin(math.pi * local)

    local = (progress - 0.72) / 0.28
    eased = local * local * (3 - 2 * local)
    x = 1520 + 520 * local
    return x, 605 - 150 * eased


def _draw_animation_overlay(size: tuple[int, int], frame_index: int) -> Image.Image:
    width, height = size
    scale_x = width / FULL_WIDTH
    scale_y = height / FULL_HEIGHT
    phase = 2 * math.pi * frame_index / FRAME_COUNT
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")

    # Fine contour lines move across the existing lower-left waveform.
    for offset, color in (
        (-22, (53, 91, 75, 34)),
        (0, (168, 117, 79, 40)),
        (22, (53, 91, 75, 30)),
    ):
        points = []
        for original_x in range(0, 930, 9):
            original_y = _wave_y(original_x, phase, offset)
            points.append((round(original_x * scale_x), round(original_y * scale_y)))
        draw.line(points, fill=color, width=max(1, round(2 * scale_x)))

    # Two nodes carry the signal from the waveform through the technical field.
    for progress_offset, color in ((0.0, (168, 117, 79)), (0.47, (53, 91, 75))):
        progress = (frame_index / FRAME_COUNT + progress_offset) % 1.0
        original_x, original_y = _signal_position(progress, phase)
        alpha = round(150 * math.sin(math.pi * progress) ** 0.8)
        x = round(original_x * scale_x)
        y = round(original_y * scale_y)
        radius = max(3, round(6 * scale_x))
        ring = radius + max(2, round(3 * scale_x))
        draw.ellipse((x - ring, y - ring, x + ring, y + ring), outline=(*color, alpha // 3), width=max(1, round(scale_x)))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, alpha))

    # Three rotating arc accents make the engineering gear visibly active.
    gear_center = (215 * scale_x, 225 * scale_y)
    gear_radius = 120
    gear_angle = math.degrees(phase / 3)
    gear_box = (
        round(gear_center[0] - gear_radius * scale_x),
        round(gear_center[1] - gear_radius * scale_y),
        round(gear_center[0] + gear_radius * scale_x),
        round(gear_center[1] + gear_radius * scale_y),
    )
    for angle_offset in (0, 120, 240):
        draw.arc(
            gear_box,
            start=gear_angle + angle_offset,
            end=gear_angle + angle_offset + 26,
            fill=(168, 117, 79, 76),
            width=max(2, round(3 * scale_x)),
        )
        angle = math.radians(gear_angle + angle_offset + 13)
        x = round(gear_center[0] + gear_radius * scale_x * math.cos(angle))
        y = round(gear_center[1] + gear_radius * scale_y * math.sin(angle))
        radius = max(2, round(4 * scale_x))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(53, 91, 75, 105))

    # The staff stays fixed while the note heads receive a restrained rhythm pulse.
    music_alpha = round(16 + 28 * (0.5 + 0.5 * math.sin(phase)))
    draw.line(
        [(1685 * scale_x, 180 * scale_y), (2040 * scale_x, 180 * scale_y)],
        fill=(168, 117, 79, music_alpha),
        width=max(1, round(2 * scale_x)),
    )
    for note_index, (note_x, note_y) in enumerate(((1720, 210), (1815, 198), (1910, 181), (1995, 201))):
        note_phase = phase + note_index * 0.7
        note_alpha = round(28 + 58 * (0.5 + 0.5 * math.sin(note_phase)))
        vertical_shift = round(3 * math.sin(note_phase) * scale_y)
        x = round(note_x * scale_x)
        y = round(note_y * scale_y) + vertical_shift
        radius_x = max(4, round(7 * scale_x))
        radius_y = max(3, round(5 * scale_y))
        draw.ellipse((x - radius_x, y - radius_y, x + radius_x, y + radius_y), fill=(168, 117, 79, note_alpha))

    # A cursor blink and left-to-right data scan activate the software region.
    cursor_alpha = round(24 + 70 * (0.5 + 0.5 * math.sin(phase * 5)) ** 3)
    cursor_box = (
        round(1990 * scale_x),
        round(439 * scale_y),
        round(1993 * scale_x),
        round(459 * scale_y),
    )
    draw.rounded_rectangle(cursor_box, radius=max(1, round(scale_x)), fill=(53, 91, 75, cursor_alpha))

    scan_progress = (frame_index / FRAME_COUNT * 2) % 1.0
    scan_alpha = round(90 * math.sin(math.pi * scan_progress) ** 0.8)
    scan_start_x = round(1640 * scale_x)
    scan_end_x = round((1640 + 350 * scan_progress) * scale_x)
    scan_y = round(432 * scale_y)
    draw.line(
        [(scan_start_x, scan_y), (scan_end_x, scan_y)],
        fill=(53, 91, 75, scan_alpha // 2),
        width=max(1, round(2 * scale_x)),
    )
    scan_radius = max(2, round(4 * scale_x))
    draw.ellipse(
        (scan_end_x - scan_radius, scan_y - scan_radius, scan_end_x + scan_radius, scan_y + scan_radius),
        fill=(168, 117, 79, scan_alpha),
    )

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
