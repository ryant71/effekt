# Copyright Lasse Nielsen 2011 (CC-BY-NC, http://www.creativecommons.org/licenses/by-nc/3.0/)
# Web: http://www.effekts.dk
"""Quant: subdivide the image wherever it has detail and stroke each cell."""

from dataclasses import dataclass

import cairo
import numpy as np

from ._common import ProgressCallback, Reference, new_canvas, no_progress, option


@dataclass(frozen=True, slots=True, kw_only=True)
class QuantParams:
    scale: int = option(4, "output size as a multiple of the input size")
    threshold: float = option(0.0, "mean detail (0..1) a cell needs before it is subdivided")


def difference_map(luma: np.ndarray) -> np.ndarray:
    """Local contrast per pixel, 0..255: how much it differs from its right and lower neighbours.

    The last row and column have no such neighbours and stay zero.
    """
    levels = luma.astype(np.int32)
    here = levels[:-1, :-1]
    contrast = (np.abs(here - levels[:-1, 1:]) + np.abs(here - levels[1:, :-1])) >> 1
    result = np.zeros_like(levels)
    result[:-1, :-1] = np.minimum(contrast * 10, 255)
    return result


def render(
    reference: Reference,
    params: QuantParams = QuantParams(),
    progress: ProgressCallback = no_progress,
) -> cairo.ImageSurface:
    scale = params.scale
    rgb = reference.rgb.tolist()
    # Summed-area table: any rectangle's total detail in four lookups.
    detail = np.pad(
        difference_map(reference.luma).cumsum(axis=0).cumsum(axis=1), ((1, 0), (1, 0))
    ).tolist()

    surface, context = new_canvas(reference.width * scale, reference.height * scale)
    context.set_operator(cairo.OPERATOR_SOURCE)
    context.set_line_join(cairo.LINE_JOIN_ROUND)
    context.set_line_cap(cairo.LINE_CAP_ROUND)

    def mean_detail(x: int, y: int, w: int, h: int) -> float:
        total = detail[y + h][x + w] - detail[y][x + w] - detail[y + h][x] + detail[y][x]
        return total / 255.0 / (w * h)

    def subdivide(x: int, y: int, w: int, h: int) -> None:
        if w < 2 or h < 2 or mean_detail(x, y, w, h) <= params.threshold:
            return

        half_w, half_h = w >> 1, h >> 1
        # Stroke from the cell's corner to the centre of its first quadrant,
        # in the colour found there.
        centre_x, centre_y = x + (w >> 2), y + (h >> 2)
        context.set_source_rgb(*rgb[centre_y][centre_x])
        context.set_line_width(half_w * scale)
        context.move_to(x * scale, y * scale)
        context.line_to(centre_x * scale, centre_y * scale)
        context.stroke()

        subdivide(x, y, half_w, half_h)
        subdivide(x + half_w, y + half_h, half_w, half_h)
        subdivide(x, y + half_h, half_w, half_h)
        subdivide(x + half_w, y, half_w, half_h)

    subdivide(0, 0, reference.width - 1, reference.height - 1)
    progress(1, 1)
    return surface
