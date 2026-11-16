"""Hatch a photo: short pen strokes that follow its contours."""

import math
import random

import cairo
import numpy as np
from PIL import Image, ImageFilter

SCALE = 2  # the drawing is this many times the size of the photo
LENGTH = 16  # longest stroke, in photo pixels
FLAT = 0.01  # slopes gentler than this count as flat
SEED = 1


def load(path):
    """Return how dark the photo is at each pixel, and which way a stroke should go there."""
    photo = Image.open(path).convert("L")
    darkness = 1 - np.asarray(photo) / 255

    smooth = np.asarray(photo.filter(ImageFilter.GaussianBlur(3))) / 255
    down, across = np.gradient(smooth)
    contour = np.arctan2(down, across) + math.pi / 2
    angle = np.where(np.hypot(across, down) > FLAT, contour, math.radians(45))
    return darkness, angle


def trace(x, y, darkness, angle, ink):
    """Walk from (x, y) along the angles for as long as the photo is darker than ``ink``."""
    height, width = darkness.shape
    points = [(x, y)]
    last_x, last_y = 0.0, 0.0
    for _ in range(LENGTH):
        direction = angle[int(y), int(x)]
        step_x, step_y = math.cos(direction), math.sin(direction)
        # A contour runs both ways. Keep going the way we were already heading.
        if step_x * last_x + step_y * last_y < 0:
            step_x, step_y = -step_x, -step_y
        x, y = x + step_x, y + step_y
        if not (0 <= x < width and 0 <= y < height):
            break
        if darkness[int(y), int(x)] < ink:
            break
        points.append((x, y))
        last_x, last_y = step_x, step_y
    return points


def main():
    random.seed(SEED)
    darkness, angle = load("photo.png")
    height, width = darkness.shape

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width * SCALE, height * SCALE)
    context = cairo.Context(surface)
    context.scale(SCALE, SCALE)

    context.set_source_rgb(1.0, 1.0, 1.0)
    context.paint()

    context.set_source_rgba(0.0, 0.0, 0.0, 0.8)
    context.set_line_width(0.4)
    context.set_line_cap(cairo.LINE_CAP_ROUND)
    context.set_line_join(cairo.LINE_JOIN_ROUND)
    for _ in range(width * height // 5):
        x = random.random() * width
        y = random.random() * height
        # Each stroke gets its own ink level and only crosses pixels darker than that.
        ink = random.random()
        if darkness[int(y), int(x)] > ink:
            for point_x, point_y in trace(x, y, darkness, angle, ink):
                context.line_to(point_x, point_y)
            context.stroke()

    surface.write_to_png("hatch.png")


if __name__ == "__main__":
    main()
