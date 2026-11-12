# Copyright Lasse Nielsen 2011 (CC-BY-NC, http://www.creativecommons.org/licenses/by-nc/3.0/)
# Web: http://www.effekts.dk
"""Regrain: rebuild an image from randomly placed red, green and blue film grains."""

import math
import random
from dataclasses import dataclass

import cairo

from ._common import ProgressCallback, Reference, new_canvas, no_progress, option

PROGRESS_STEPS = 10_000


@dataclass(frozen=True, slots=True, kw_only=True)
class RegrainParams:
    scale: int = option(4, "output size as a multiple of the input size")
    grain: float = option(0.7, "grain size; the largest grain is twice this, in output pixels")
    iso: float = option(0.7, "light absorption per grain (1.0 = perfect)")
    exposure: float = option(1.0, "samples per output pixel")
    seed: int | None = option(None, "random seed, for a reproducible render")


def render(
    reference: Reference,
    params: RegrainParams = RegrainParams(),
    progress: ProgressCallback = no_progress,
) -> cairo.ImageSurface:
    scale = params.scale
    width, height = reference.width * scale, reference.height * scale
    rgb = reference.rgb.tolist()
    grain, iso = params.grain, params.iso
    rng = random.Random(params.seed)
    rand = rng.random

    surface, context = new_canvas(width, height)
    context.set_operator(cairo.OPERATOR_SOURCE)
    context.set_source_rgb(0.0, 0.0, 0.0)
    context.paint()
    context.set_operator(cairo.OPERATOR_ADD)

    total = math.ceil(width * height * params.exposure)
    report_every = max(total // PROGRESS_STEPS, 1)

    for count in range(total):
        x = rand() * width
        y = rand() * height
        red, green, blue = rgb[int(y / scale)][int(x / scale)]
        radius = (rand() + 1.0) * grain

        # One grain per colour channel, offset slightly like a dye triad.
        context.move_to(x, y)
        context.set_source_rgba(red, 0.0, 0.0, iso * rand())
        context.arc(x, y - 0.5, radius * red, 0.0, math.tau)
        context.fill()
        context.set_source_rgba(0.0, green, 0.0, iso * rand())
        context.arc(x - 0.5, y + 0.5, radius * green, 0.0, math.tau)
        context.fill()
        context.set_source_rgba(0.0, 0.0, blue, iso * rand())
        context.arc(x + 0.5, y + 0.5, radius * blue, 0.0, math.tau)
        context.fill()

        if count % report_every == 0:
            progress(count, total)

    progress(total, total)
    return surface
