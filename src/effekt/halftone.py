"""Halftone: a rotated grid of dots, each sized by how dark the image is beneath it."""

import math
from dataclasses import dataclass

import cairo
import numpy as np

from ._common import ProgressCallback, Reference, blur, new_canvas, no_progress, option

#: Ink colour and screen angle, in degrees relative to black's, of each CMYK plate.
PLATES = (
    ((0.0, 1.0, 1.0), -30.0),
    ((1.0, 0.0, 1.0), 30.0),
    ((1.0, 1.0, 0.0), -45.0),
    ((0.0, 0.0, 0.0), 0.0),
)


@dataclass(frozen=True, slots=True, kw_only=True)
class HalftoneParams:
    scale: int = option(2, "output size as a multiple of the input size")
    cell: float = option(8.0, "distance between dots, in output pixels")
    angle: float = option(45.0, "angle of the grid of black dots, in degrees")
    cmyk: bool = option(False, "print cyan, magenta, yellow and black screens instead of black")


def separate(rgb: np.ndarray) -> np.ndarray:
    """Split ``(height, width, 3)`` RGB into ``(4, height, width)`` CMYK ink levels, 0..1.

    Black replaces as much of the other three inks as it can.
    """
    black = 1.0 - rgb.max(axis=2)
    room = np.maximum(1.0 - black, 1e-9)
    return np.stack([*((1.0 - rgb[..., c] - black) / room for c in range(3)), black])


def lattice(width: int, height: int, cell: float, angle: float) -> np.ndarray:
    """Points of a square grid, turned about the canvas centre, that cover the canvas.

    Returns ``(count, 2)`` x, y positions, including a margin of one cell.
    """
    reach = math.ceil(math.hypot(width, height) / 2.0 / cell) + 1
    steps = np.arange(-reach, reach + 1) * cell
    along, across = np.meshgrid(steps, steps)
    x = width / 2.0 + along * math.cos(angle) - across * math.sin(angle)
    y = height / 2.0 + along * math.sin(angle) + across * math.cos(angle)
    inside = (x > -cell) & (x < width + cell) & (y > -cell) & (y < height + cell)
    return np.column_stack([x[inside], y[inside]])


def render(
    reference: Reference,
    params: HalftoneParams = HalftoneParams(),
    progress: ProgressCallback = no_progress,
) -> cairo.ImageSurface:
    if params.cell <= 0.0:
        raise ValueError("cell must be greater than 0")

    scale, cell = params.scale, params.cell
    width, height = reference.width * scale, reference.height * scale
    # Each dot stands for the average of the image under its cell.
    sigma = cell / scale / 2.0
    if params.cmyk:
        rgb = np.dstack([blur(reference.rgb[..., c], sigma) for c in range(3)])
        plates = list(zip(separate(rgb), PLATES, strict=True))
    else:
        darkness = 1.0 - blur(reference.luma / 255.0, sigma)
        plates = [(darkness, PLATES[3])]

    surface, context = new_canvas(width, height)
    context.set_source_rgb(1.0, 1.0, 1.0)
    context.paint()
    # Inks darken whatever is already printed, as on paper.
    context.set_operator(cairo.OPERATOR_MULTIPLY)

    for done, (levels, (ink, turn)) in enumerate(plates):
        points = lattice(width, height, cell, math.radians(params.angle + turn))
        columns = np.clip(points[:, 0] / scale, 0, reference.width - 1).astype(int)
        rows = np.clip(points[:, 1] / scale, 0, reference.height - 1).astype(int)
        # A dot's area, as a share of its cell, is the ink level.
        radii = cell * np.sqrt(np.clip(levels[rows, columns], 0.0, 1.0) / math.pi)

        context.set_source_rgb(*ink)
        for (x, y), radius in zip(points.tolist(), radii.tolist(), strict=True):
            if radius > 0.0:
                context.arc(x, y, radius, 0.0, math.tau)
                context.fill()
        progress(done + 1, len(plates))

    return surface
