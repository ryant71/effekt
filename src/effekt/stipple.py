"""Stipple: evenly spaced dots, packed closer together where the image is darker.

Dots start at random, more of them in dark areas, and are then relaxed: each
moves to the centre of the darkness nearest to it, over and over, until they
stop crowding each other (weighted Voronoi stippling).
"""

import math
from dataclasses import dataclass

import cairo
import numpy as np
from PIL import Image

from ._common import ProgressCallback, Reference, new_canvas, no_progress, option

#: Relaxation runs on a reduced image of about this many cells, or enough for the dots.
TARGET_CELLS = 300_000
CELLS_PER_DOT = 16
NEIGHBOURS = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]


@dataclass(frozen=True, slots=True, kw_only=True)
class StippleParams:
    scale: int = option(2, "output size as a multiple of the input size")
    dots: int = option(20_000, "number of dots")
    size: float = option(1.6, "dot radius, in output pixels")
    contrast: float = option(3.0, "power applied to darkness; higher empties the light areas")
    iterations: int = option(30, "relaxation passes; 0 leaves the dots where they first land")
    colour: float = option(0.0, "how much of the image colour the dots take (0 = black)")
    seed: int | None = option(None, "random seed, for a reproducible render")


def nearest(x: np.ndarray, y: np.ndarray, rows: int, columns: int) -> np.ndarray:
    """For each cell of a grid, the index of the point nearest to its centre.

    Uses jump flooding: every cell repeatedly asks neighbours at halving
    distances which point they know of. It is fast and very nearly exact.
    """
    cell_y, cell_x = np.mgrid[0:rows, 0:columns] + 0.5
    # Index -1 means "no point yet" and reads this far-away placeholder.
    far_x, far_y = np.append(x, 1e9), np.append(y, 1e9)

    owner = np.full((rows, columns), -1, dtype=np.int64)
    owner[np.clip(y.astype(int), 0, rows - 1), np.clip(x.astype(int), 0, columns - 1)] = np.arange(
        len(x)
    )
    distance = (cell_x - far_x[owner]) ** 2 + (cell_y - far_y[owner]) ** 2

    jump = 1 << max(max(rows, columns) - 1, 1).bit_length() - 1
    # A final pass at distance 1 mops up the few cells flooding gets wrong.
    jumps = [jump >> shift for shift in range(jump.bit_length())] + [1]
    for jump in jumps:
        padded = np.pad(owner, jump, constant_values=-1)
        for dy, dx in NEIGHBOURS:
            top, left = jump + dy * jump, jump + dx * jump
            candidate = padded[top : top + rows, left : left + columns]
            reach = (cell_x - far_x[candidate]) ** 2 + (cell_y - far_y[candidate]) ** 2
            closer = reach < distance
            owner = np.where(closer, candidate, owner)
            distance = np.where(closer, reach, distance)
    return owner


def relax(
    x: np.ndarray, y: np.ndarray, weight: np.ndarray, iterations: int, progress: ProgressCallback
) -> tuple[np.ndarray, np.ndarray]:
    """Move each point to the weighted centre of the cells nearest to it, repeatedly."""
    rows, columns = weight.shape
    cell_y, cell_x = np.mgrid[0:rows, 0:columns] + 0.5
    flat = weight.ravel()
    flat_x, flat_y = (cell_x * weight).ravel(), (cell_y * weight).ravel()

    for done in range(iterations):
        owner = nearest(x, y, rows, columns).ravel()
        total = np.bincount(owner, flat, minlength=len(x))
        # A point that owns no darkness has nowhere better to go.
        moved = total > 0.0
        safe = np.where(moved, total, 1.0)
        x = np.where(moved, np.bincount(owner, flat_x, minlength=len(x)) / safe, x)
        y = np.where(moved, np.bincount(owner, flat_y, minlength=len(y)) / safe, y)
        progress(done + 1, iterations + 1)
    return x, y


def render(
    reference: Reference,
    params: StippleParams = StippleParams(),
    progress: ProgressCallback = no_progress,
) -> cairo.ImageSurface:
    if params.dots < 0 or params.iterations < 0:
        raise ValueError("dots and iterations must not be negative")

    scale = params.scale
    surface, context = new_canvas(reference.width * scale, reference.height * scale)
    context.set_source_rgb(1.0, 1.0, 1.0)
    context.paint()

    # Large images are reduced first; dot positions stay fractional, so little is lost.
    cells = max(TARGET_CELLS, CELLS_PER_DOT * params.dots)
    reduce = max(math.isqrt(reference.width * reference.height // cells), 1)
    weight = 1.0 - np.asarray(Image.fromarray(reference.luma).reduce(reduce)) / 255.0
    weight = weight**params.contrast
    columns = weight.shape[1]
    darkness = weight.sum()
    if params.dots == 0 or darkness <= 0.0:
        progress(1, 1)
        return surface

    # Start with dots scattered in proportion to darkness.
    rng = np.random.default_rng(params.seed)
    start = rng.choice(weight.size, size=params.dots, p=weight.ravel() / darkness)
    x = start % columns + rng.random(params.dots)
    y = start // columns + rng.random(params.dots)
    x, y = relax(x, y, weight, params.iterations, progress)

    to_output = reduce * scale
    pixel_x = np.clip(x * reduce, 0, reference.width - 1).astype(int)
    pixel_y = np.clip(y * reduce, 0, reference.height - 1).astype(int)
    colours = (reference.rgb[pixel_y, pixel_x] * params.colour).tolist()
    for dot_x, dot_y, colour in zip(
        (x * to_output).tolist(), (y * to_output).tolist(), colours, strict=True
    ):
        context.set_source_rgb(*colour)
        context.arc(dot_x, dot_y, params.size, 0.0, math.tau)
        context.fill()

    progress(1, 1)
    return surface
