"""Colours (spiral): one line spirals out from the centre, bent and thickened by the image.

A new effect that borrows the name and the pen of the original
``colours_spiral`` script, of which only an unusable fragment survives. The
pen is pulled towards darker areas as in ``colours_natural``, draws thicker
where the image is darker, and takes the colour underneath.
"""

import math
from dataclasses import dataclass

import cairo

from ._common import ProgressCallback, Reference, new_canvas, no_progress, option

PROGRESS_STEPS = 10_000
#: Distance the pen travels per stroke, in output pixels.
STEP = 2.0


@dataclass(frozen=True, slots=True, kw_only=True)
class SpiralParams:
    scale: int = option(2, "output size as a multiple of the input size")
    spacing: float = option(8.0, "distance between turns of the spiral, in output pixels")
    width: float = option(1.0, "line width in a pure black area, as a multiple of --spacing")
    min_width: float = option(0.08, "line width in a pure white area, as a multiple of --spacing")
    bend: float = option(1.0, "how hard the image pulls the line towards darker areas")
    damp: float = option(0.8, "fraction of the pull kept from one stroke to the next")
    colour: float = option(1.0, "how much of the image colour the line takes (0 = black)")


def render(
    reference: Reference,
    params: SpiralParams = SpiralParams(),
    progress: ProgressCallback = no_progress,
) -> cairo.ImageSurface:
    if params.spacing <= 0.0:
        raise ValueError("spacing must be greater than 0")

    scale = params.scale
    width, height = reference.width * scale, reference.height * scale
    centre_x, centre_y = width / 2, height / 2
    luma = reference.luma.tolist()
    rgb = (reference.rgb * params.colour).tolist()
    spacing, damp = params.spacing, params.damp
    thin = params.min_width * spacing
    thicken = (params.width - params.min_width) * spacing / 255.0
    impulse_amp = params.bend * spacing / 255.0
    # The radius grows by one spacing per turn.
    growth = spacing / math.tau
    # The line may wander this far from the spiral before it is reined in.
    reach = spacing * 0.5

    surface, context = new_canvas(width, height)
    context.set_operator(cairo.OPERATOR_SOURCE)
    context.set_line_join(cairo.LINE_JOIN_ROUND)
    context.set_line_cap(cairo.LINE_CAP_ROUND)

    # Far enough out to cover the corners.
    last_radius = math.hypot(centre_x, centre_y) + spacing
    # Length of an Archimedean spiral, to a good approximation.
    total = max(int(math.pi * last_radius**2 / spacing / STEP), 1)
    report_every = max(total // PROGRESS_STEPS, 1)

    angle = radius = 0.0
    offset_x = offset_y = 0.0
    x, y = centre_x, centre_y
    count = 0

    while radius < last_radius:
        angle += STEP / max(radius, STEP)
        radius = growth * angle
        on_spiral_x = centre_x + radius * math.cos(angle)
        on_spiral_y = centre_y + radius * math.sin(angle)

        # Impulse from the luminosity gradient, towards darker areas.
        px, py = reference.interior_pixel(x / width, y / height)
        offset_x = offset_x * damp + (luma[py][px - 1] - luma[py][px + 1]) * impulse_amp
        offset_y = offset_y * damp + (luma[py - 1][px] - luma[py + 1][px]) * impulse_amp
        stray = math.hypot(offset_x, offset_y)
        if stray > reach:
            offset_x *= reach / stray
            offset_y *= reach / stray

        last_x, last_y = x, y
        x, y = on_spiral_x + offset_x, on_spiral_y + offset_y

        # Most of the last turns lie outside the canvas.
        if -spacing < x < width + spacing and -spacing < y < height + spacing:
            context.set_line_width(thin + (255 - luma[py][px]) * thicken)
            context.set_source_rgb(*rgb[py][px])
            context.move_to(last_x, last_y)
            context.line_to(x, y)
            context.stroke()

        count += 1
        if count % report_every == 0:
            progress(min(count, total), total)

    progress(total, total)
    return surface
