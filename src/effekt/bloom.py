# Copyright Lasse Nielsen 2011 (CC-BY-NC, http://www.creativecommons.org/licenses/by-nc/3.0/)
# Web: http://www.effekts.dk
"""Bloom: every output pixel emits an additive disc sized by its brightness."""

import math
from dataclasses import dataclass

import cairo

from ._common import ProgressCallback, Reference, new_canvas, no_progress, option

#: The entropy source is read as (x, y) byte pairs and must hold at least two.
MIN_ENTROPY_BYTES = 4


@dataclass(frozen=True, slots=True, kw_only=True)
class BloomParams:
    scale: int = option(2, "output size as a multiple of the input size")
    exposure: float = option(10.0, "disc radius, in output pixels, of a pure white pixel")
    min_exposure: float = option(0.0, "smallest disc radius, in output pixels")
    blur: float = option(15.0, "range of the entropy-driven jitter")


def render(
    reference: Reference,
    entropy: bytes,
    params: BloomParams = BloomParams(),
    progress: ProgressCallback = no_progress,
) -> cairo.ImageSurface:
    if len(entropy) < MIN_ENTROPY_BYTES:
        raise ValueError(f"the entropy source must hold at least {MIN_ENTROPY_BYTES} bytes")
    if params.exposure <= 0:
        raise ValueError("exposure must be positive")

    scale = params.scale
    width, height = reference.width * scale, reference.height * scale
    luma = reference.luma.tolist()
    rgb = reference.rgb.tolist()
    exposure, min_exposure = params.exposure, params.min_exposure
    blur_coef = 255 / (params.blur + 1.0)
    # Samples are consumed as whole pairs, wrapping around at the end.
    entropy_span = len(entropy) - len(entropy) % 2

    surface, context = new_canvas(width, height)
    context.set_operator(cairo.OPERATOR_SOURCE)
    context.set_source_rgb(0.0, 0.0, 0.0)
    context.paint()
    context.set_operator(cairo.OPERATOR_ADD)

    offset = 0
    for y in range(height):
        luma_row = luma[y // scale]
        rgb_row = rgb[y // scale]
        for x in range(width):
            jitter_x = (entropy[offset] - 128) / blur_coef
            jitter_y = (entropy[offset + 1] - 128) / blur_coef
            offset = (offset + 2) % entropy_span

            level = luma_row[x // scale]
            red, green, blue = rgb_row[x // scale]
            radius = max(level / 255.0 * exposure, min_exposure)

            # The jittered start point only adds a zero-area spur to the disc,
            # so it does not change the filled result.
            context.move_to(x + jitter_x, y + jitter_y)
            context.set_source_rgba(red, green, blue, level / 128.0 / exposure)
            context.arc(x, y, radius, 0.0, math.tau)
            context.fill()
        progress(y + 1, height)

    return surface
