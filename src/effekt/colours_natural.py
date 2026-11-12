# Copyright Lasse Nielsen 2011 (CC-BY-NC, http://www.creativecommons.org/licenses/by-nc/3.0/)
# Web: http://www.effekts.dk
"""Colours (natural): a pen wanders over the image, steered by a byte stream.

Each byte of the stroke source nudges the pen, the reference image pulls it
towards darker areas, and every step is stroked in the colour underneath.
"""

import math
import random
from dataclasses import dataclass

import cairo

from ._common import ProgressCallback, Reference, new_canvas, no_progress, option


@dataclass(frozen=True, slots=True, kw_only=True)
class ColoursParams:
    scale: int = option(4, "output size as a multiple of the input size")
    damp: float = option(0.1, "fraction of the pen velocity kept after each stroke")
    cohesion: float = option(5e-9, "strength of the pull towards the image centre")
    island: int = option(4000, "steps before the pen jumps to a new random position")
    seed: int = option(1234, "random seed for the pen positions")


def render(
    reference: Reference,
    strokes: bytes,
    params: ColoursParams = ColoursParams(),
    progress: ProgressCallback = no_progress,
) -> cairo.ImageSurface:
    """Draw one stroke per byte of ``strokes``."""
    if params.island < 2:
        raise ValueError("island must be at least 2")

    scale = params.scale
    width, height = reference.width * scale, reference.height * scale
    aspect = height / width
    centre_x, centre_y = width / 2, height / 2
    luma = reference.luma.tolist()
    rgb = reference.rgb.tolist()
    damp, cohesion = params.damp, params.cohesion
    step_size = (2.5 * scale) / 65536.0
    line_width = (0.01 * scale) * 0.02
    impulse_amp = (15.0 * scale) / 256.0

    surface, context = new_canvas(width, height)
    context.set_operator(cairo.OPERATOR_SOURCE)
    context.set_line_join(cairo.LINE_JOIN_ROUND)
    context.set_line_cap(cairo.LINE_CAP_ROUND)

    rng = random.Random(params.seed)
    total = len(strokes)
    # Strokes thin out from 1.5x to 0.5x of their width over the run.
    size_offset = total + total // 2
    vel_x = vel_y = 0.0
    pos = 0
    # Islands alternate between widening strokes in light and in dark areas.
    widen_in_light = False

    while pos < total:
        x: float = rng.randint(0, width - 1)
        y: float = rng.randint(0, height - 1)
        widen_in_light = not widen_in_light
        context.move_to(x, y)

        for byte in strokes[pos : pos + params.island - 1]:
            x_dir = -1.0 if byte & 1 else 1.0
            y_dir = -1.0 if byte & 2 else 1.0
            to_centre_x = centre_x - x
            to_centre_y = centre_y - y
            pull = math.hypot(to_centre_x, to_centre_y) * cohesion
            push = byte**2 * step_size

            # Impulse from the luminosity gradient, towards darker areas.
            px, py = reference.interior_pixel(x / width, y / height)
            impulse_x = (luma[py][px - 1] - luma[py][px + 1]) * impulse_amp
            impulse_y = (luma[py - 1][px] - luma[py + 1][px]) * impulse_amp

            vel_x = vel_x + (x_dir * push) + (to_centre_x * pull) + impulse_x
            vel_y = vel_y + (y_dir * push) + (to_centre_y * pull) + (impulse_y * aspect)
            x += vel_x
            y += vel_y
            vel_x *= damp
            vel_y *= damp

            level = luma[py][px]
            tone = level if widen_in_light else 255 - level
            width_amp = (size_offset - pos) / total
            context.set_line_width(math.hypot(impulse_x, impulse_y) * line_width * tone * width_amp)
            context.set_source_rgb(*rgb[py][px])
            context.line_to(x, y)
            context.stroke()
            context.move_to(x, y)
            pos += 1

        progress(pos, total)

    return surface
