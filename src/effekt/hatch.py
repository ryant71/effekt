"""Hatch: short pen strokes follow the image's contours, denser where it is darker."""

import math
import random
from dataclasses import dataclass

import cairo
import numpy as np

from ._common import ProgressCallback, Reference, new_canvas, no_progress, option

PROGRESS_STEPS = 10_000
#: The edge strength that counts as "strong" when weighing it against ``bias``.
STRONG_EDGE_PERCENTILE = 99.0


@dataclass(frozen=True, slots=True, kw_only=True)
class HatchParams:
    scale: int = option(2, "output size as a multiple of the input size")
    density: float = option(0.2, "strokes started per input pixel in a pure black area")
    length: float = option(16.0, "longest stroke, in input pixels")
    width: float = option(0.8, "line width, in output pixels")
    opacity: float = option(0.8, "ink opacity per stroke (1.0 = solid)")
    smoothing: float = option(2.0, "blur radius, in input pixels, of the contours strokes follow")
    angle: float = option(45.0, "hatching angle, in degrees, where the image has no contours")
    bias: float = option(0.05, "pull towards --angle; 0 follows the image everywhere")
    colour: float = option(0.0, "how much of the image colour the ink takes (0 = black)")
    seed: int | None = option(None, "random seed, for a reproducible render")


def blur(values: np.ndarray, sigma: float) -> np.ndarray:
    """Gaussian blur of a 2D array, repeating the edge pixels outwards."""
    if sigma <= 0.0:
        return values
    radius = max(int(3.0 * sigma + 0.5), 1)
    kernel = np.exp(-0.5 * (np.arange(-radius, radius + 1) / sigma) ** 2)
    kernel /= kernel.sum()
    for axis in (0, 1):
        pad = [(radius, radius) if a == axis else (0, 0) for a in (0, 1)]
        padded = np.pad(values, pad, mode="edge")
        values = np.apply_along_axis(np.convolve, axis, padded, kernel, mode="valid")
    return values


def flow_field(luma: np.ndarray, smoothing: float, angle: float, bias: float) -> np.ndarray:
    """The angle, in radians, a stroke should take at each pixel.

    Strokes run along contours, at right angles to the brightness gradient. The
    gradient only has an orientation, not a direction, so it is averaged as a
    doubled angle, where opposite gradients reinforce instead of cancelling.
    ``bias`` adds a constant pull towards ``angle`` that wins wherever the
    image is flat.
    """
    dy, dx = np.gradient(blur(luma.astype(np.float64), smoothing))
    across = blur(dx * dx - dy * dy, smoothing)
    along = blur(2.0 * dx * dy, smoothing)
    strong = float(np.percentile(np.hypot(across, along), STRONG_EDGE_PERCENTILE)) or 1.0
    # Negated: the contour is perpendicular to the gradient.
    across = -across / strong + bias * math.cos(2.0 * angle)
    along = -along / strong + bias * math.sin(2.0 * angle)
    return 0.5 * np.arctan2(along, across)


def render(
    reference: Reference,
    params: HatchParams = HatchParams(),
    progress: ProgressCallback = no_progress,
) -> cairo.ImageSurface:
    scale = params.scale
    columns, rows = reference.width, reference.height
    field = flow_field(reference.luma, params.smoothing, math.radians(params.angle), params.bias)
    step_x, step_y = np.cos(field).tolist(), np.sin(field).tolist()
    darkness = (1.0 - reference.luma / 255.0).tolist()
    rgb = (reference.rgb * params.colour).tolist()
    half_steps = max(int(params.length / 2.0), 1)
    rng = random.Random(params.seed)
    rand = rng.random

    surface, context = new_canvas(columns * scale, rows * scale)
    context.set_source_rgb(1.0, 1.0, 1.0)
    context.paint()
    context.set_line_width(params.width)
    context.set_line_cap(cairo.LINE_CAP_ROUND)
    context.set_line_join(cairo.LINE_JOIN_ROUND)

    def trace(x: float, y: float, heading: float, ink: float) -> list[tuple[float, float]]:
        """Walk from a point along the field for as long as the image stays dark enough."""
        points = []
        last_x, last_y = step_x[int(y)][int(x)] * heading, step_y[int(y)][int(x)] * heading
        for _ in range(half_steps):
            column, row = int(x), int(y)
            move_x, move_y = step_x[row][column], step_y[row][column]
            # The field has no direction of its own; keep going the way we were.
            if move_x * last_x + move_y * last_y < 0.0:
                move_x, move_y = -move_x, -move_y
            x += move_x
            y += move_y
            if not (0.0 <= x < columns and 0.0 <= y < rows) or darkness[int(y)][int(x)] < ink:
                break
            points.append((x * scale, y * scale))
            last_x, last_y = move_x, move_y
        return points

    total = math.ceil(columns * rows * params.density)
    report_every = max(total // PROGRESS_STEPS, 1)

    for count in range(total):
        x = rand() * columns
        y = rand() * rows
        # A stroke only covers pixels darker than its own ink level, so the
        # share of strokes crossing any pixel matches how dark that pixel is.
        ink = rand()
        if darkness[int(y)][int(x)] >= ink:
            points = [
                *reversed(trace(x, y, -1.0, ink)),
                (x * scale, y * scale),
                *trace(x, y, 1.0, ink),
            ]
            context.set_source_rgba(*rgb[int(y)][int(x)], params.opacity)
            context.move_to(*points[0])
            for point in points[1:]:
                context.line_to(*point)
            # A stroke that could not move still leaves a dot.
            if len(points) == 1:
                context.close_path()
            context.stroke()

        if count % report_every == 0:
            progress(count, total)

    progress(total, total)
    return surface
