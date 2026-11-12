# Copyright Lasse Nielsen 2011 (CC-BY-NC, http://www.creativecommons.org/licenses/by-nc/3.0/)
# Web: http://www.effekts.dk
"""EBS: swarms of entities flock across the image and leave coloured trails."""

import math
import random
from dataclasses import dataclass

import cairo

from ._common import ProgressCallback, Reference, new_canvas, no_progress, option

IMPULSE_AMP = 5.0 / 256.0
VELOCITY_SCALE = 0.5
MIN_DISTANCE = 0.01

type Colour = tuple[float, float, float]


@dataclass(frozen=True, slots=True, kw_only=True)
class EbsParams:
    scale: int = option(1, "output size as a multiple of the input size")
    entities: int = option(20, "entities in the swarm")
    island: int = option(25, "steps before the swarm respawns at a new random position")
    seed: int = option(986473288, "random seed for the swarm positions")


@dataclass(slots=True)
class Entity:
    x: float = 0.0
    y: float = 0.0
    last_x: float = 0.0
    last_y: float = 0.0
    vel_x: float = 0.0
    vel_y: float = 0.0
    width: float = 0.0
    colour: Colour = (0.0, 0.0, 0.0)
    last_colour: Colour = (0.0, 0.0, 0.0)


def _spawn(swarm: list[Entity], x: float, y: float, scatter: float, rng: random.Random) -> None:
    def bias() -> float:
        return (rng.random() * scatter) - (scatter * 0.5)

    for entity in swarm:
        entity.colour = entity.last_colour = (0.0, 0.0, 0.0)
        entity.width = 0.0
        entity.last_x = entity.x = x + bias()
        entity.last_y = entity.y = y + bias()
        entity.vel_x = bias()
        entity.vel_y = bias()


def _update(
    swarm: list[Entity],
    reference: Reference,
    luma: list[list[int]],
    rgb: list[list[list[float]]],
    scale: int,
) -> None:
    """Advance the swarm one step. Entities move in turn and see earlier moves."""
    width, height = reference.width * scale, reference.height * scale
    line_width = 0.25 * scale
    share = 1.0 / len(swarm)
    centroid_x = centroid_y = 0.0
    for entity in swarm:
        centroid_x += entity.x * share
        centroid_y += entity.y * share

    for entity in swarm:
        entity.vel_x += (entity.x - centroid_x) * 0.001
        entity.vel_y += (entity.y - centroid_y) * 0.001

        # Steer towards the others' positions and away from their velocities.
        steer_x = steer_y = match_x = match_y = 0.0
        for other in swarm:
            if other is entity:
                continue
            dx, dy = other.x - entity.x, other.y - entity.y
            inverse = 1.0 / max(math.sqrt(dx * dx + dy * dy), MIN_DISTANCE)
            steer_x += dx * inverse
            steer_y += dy * inverse

            dx, dy = entity.vel_x - other.vel_x, entity.vel_y - other.vel_y
            inverse = 1.0 / max(math.sqrt(dx * dx + dy * dy), MIN_DISTANCE)
            match_x += dx * inverse
            match_y += dy * inverse

        entity.vel_x += steer_x + match_x
        entity.vel_y += steer_y + match_y
        entity.last_x, entity.last_y = entity.x, entity.y
        entity.x += entity.vel_x * float(scale) * VELOCITY_SCALE
        entity.y += entity.vel_y * float(scale) * VELOCITY_SCALE
        entity.vel_x *= 0.95
        entity.vel_y *= 0.95

        # Impulse from the luminosity gradient, towards lighter areas.
        px, py = reference.interior_pixel(entity.x / width, entity.y / height)
        impulse_x = (luma[py][px + 1] - luma[py][px - 1]) * IMPULSE_AMP
        impulse_y = (luma[py + 1][px] - luma[py - 1][px]) * IMPULSE_AMP
        weight = impulse_x + impulse_y + 32.0

        target_width = math.hypot(impulse_x, impulse_y) * line_width * weight
        entity.width = (entity.width * 0.9) + (target_width * 0.1)
        entity.last_colour = entity.colour
        red, green, blue = rgb[py][px]
        entity.colour = (red, green, blue)
        entity.vel_x += impulse_x
        entity.vel_y += impulse_y


def _draw(swarm: list[Entity], context: cairo.Context) -> None:
    for entity in swarm:
        gradient = cairo.LinearGradient(entity.last_x, entity.last_y, entity.x, entity.y)
        gradient.add_color_stop_rgb(0.0, *entity.last_colour)
        gradient.add_color_stop_rgb(1.0, *entity.colour)
        context.set_source(gradient)
        context.set_line_width(entity.width)
        context.move_to(entity.last_x, entity.last_y)
        context.line_to(entity.x, entity.y)
        context.stroke()


def render(
    reference: Reference,
    density: int,
    params: EbsParams = EbsParams(),
    progress: ProgressCallback = no_progress,
) -> cairo.ImageSurface:
    """Run the swarm for ``density`` steps; each step strokes every entity once."""
    if params.entities < 1:
        raise ValueError("entities must be at least 1")
    if params.island < 2:
        raise ValueError("island must be at least 2")

    scale = params.scale
    width, height = reference.width * scale, reference.height * scale
    luma = reference.luma.tolist()
    rgb = reference.rgb.tolist()

    surface, context = new_canvas(width, height)
    context.set_operator(cairo.OPERATOR_SOURCE)
    context.set_line_join(cairo.LINE_JOIN_ROUND)
    context.set_line_cap(cairo.LINE_CAP_SQUARE)

    rng = random.Random(params.seed)
    swarm = [Entity() for _ in range(params.entities)]
    pos = 0

    while pos < density:
        x = rng.randint(0, width - 1)
        y = rng.randint(0, height - 1)
        _spawn(swarm, x, y, rng.random() * 10.0, rng)

        for _ in range(min(params.island - 1, density - pos)):
            _update(swarm, reference, luma, rgb, scale)
            _draw(swarm, context)
            pos += 1

        progress(pos, density)

    return surface
