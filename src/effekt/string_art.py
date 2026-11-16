"""String art: one thread wound between pins around the image's edge until the picture appears.

The pins sit on the ellipse that fits the image. From each pin the thread goes
to whichever other pin has the most darkness still to cover along the way.
"""

import math
from dataclasses import dataclass
from itertools import pairwise

import cairo
import numpy as np
from PIL import Image

from ._common import ProgressCallback, Reference, new_canvas, no_progress, option

#: Longest side of the reduced image the thread's path is planned on.
PLAN_SIDE = 256
#: The thread never goes to a pin closer than this share of the way round.
NEAR_PINS = 1 / 12


@dataclass(frozen=True, slots=True, kw_only=True)
class StringArtParams:
    scale: int = option(2, "output size as a multiple of the input size")
    pins: int = option(300, "number of pins around the edge")
    lines: int = option(5000, "most lines to wind; fewer if the image is covered sooner")
    width: float = option(0.4, "thread width, in output pixels")
    opacity: float = option(0.3, "thread opacity (1.0 = solid)")


def plan(darkness: np.ndarray, pins: int, lines: int, cover: float) -> list[int]:
    """Choose the pins the thread visits, in order, starting at pin 0.

    ``darkness`` is the image as 0..1 values; ``cover`` is how much of a cell's
    darkness one pass of the thread accounts for.
    """
    rows, columns = darkness.shape
    turn = np.arange(pins) * math.tau / pins
    pin_x = columns / 2.0 + (columns / 2.0 - 0.5) * np.cos(turn)
    pin_y = rows / 2.0 + (rows / 2.0 - 0.5) * np.sin(turn)
    # Every line is sampled at the same number of evenly spaced points.
    along = np.linspace(0.0, 1.0, max(rows, columns))[None, :]
    near = max(int(pins * NEAR_PINS), 1)
    wanted = darkness.ravel().copy()
    routes: dict[int, np.ndarray] = {}

    def routes_from(pin: int) -> np.ndarray:
        """Cell indices along the line from one pin to each of the others."""
        if pin not in routes:
            x = pin_x[pin] + (pin_x[:, None] - pin_x[pin]) * along
            y = pin_y[pin] + (pin_y[:, None] - pin_y[pin]) * along
            routes[pin] = y.astype(np.int32) * columns + x.astype(np.int32)
        return routes[pin]

    path = [0]
    previous = -1
    while len(path) <= lines:
        pin = path[-1]
        cells = routes_from(pin)
        gain = wanted[cells].mean(axis=1)
        # Neighbouring pins give lines too short to matter; going straight back adds nothing.
        gain[(np.arange(pins) - pin + near) % pins <= 2 * near] = -np.inf
        if previous >= 0:
            gain[previous] = -np.inf
        best = int(gain.argmax())
        if gain[best] <= 0.0:
            break
        wanted[cells[best]] -= cover
        previous = pin
        path.append(best)
    return path


def render(
    reference: Reference,
    params: StringArtParams = StringArtParams(),
    progress: ProgressCallback = no_progress,
) -> cairo.ImageSurface:
    if params.pins < 3:
        raise ValueError("pins must be at least 3")

    scale = params.scale
    width, height = reference.width * scale, reference.height * scale
    surface, context = new_canvas(width, height)
    context.set_source_rgb(1.0, 1.0, 1.0)
    context.paint()

    shrink = min(PLAN_SIDE / max(reference.width, reference.height), 1.0)
    plan_size = (max(round(reference.width * shrink), 2), max(round(reference.height * shrink), 2))
    small = Image.fromarray(reference.luma).resize(plan_size, Image.Resampling.BOX)
    darkness = 1.0 - np.asarray(small) / 255.0
    # One thread darkens a planning cell by its opacity times the share of the cell it covers.
    cell = width / plan_size[0]
    cover = params.opacity * min(params.width / cell, 1.0)
    path = plan(darkness, params.pins, params.lines, cover) if cover > 0.0 else [0]
    progress(1, 2)

    turn = np.arange(params.pins) * math.tau / params.pins
    pin_x = (width / 2.0 + (width / 2.0 - cell / 2.0) * np.cos(turn)).tolist()
    pin_y = (height / 2.0 + (height / 2.0 - cell / 2.0) * np.sin(turn)).tolist()
    context.set_source_rgba(0.0, 0.0, 0.0, params.opacity)
    context.set_line_width(params.width)
    # Stroked one by one so that crossing threads darken each other.
    for start, end in pairwise(path):
        context.move_to(pin_x[start], pin_y[start])
        context.line_to(pin_x[end], pin_y[end])
        context.stroke()

    progress(2, 2)
    return surface
