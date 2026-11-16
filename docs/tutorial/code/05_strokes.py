import math
import random

import cairo
import numpy as np
from PIL import Image

SCALE = 2  # the drawing is this many times the size of the photo
LENGTH = 12  # length of each stroke, in photo pixels
ANGLE = 45  # direction of every stroke, in degrees

photo = Image.open("photo.png").convert("L")
darkness = 1 - np.asarray(photo) / 255
height, width = darkness.shape

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width * SCALE, height * SCALE)
context = cairo.Context(surface)
context.scale(SCALE, SCALE)

context.set_source_rgb(1.0, 1.0, 1.0)
context.paint()

# How far a stroke reaches from its middle, sideways and downwards.
reach_x = math.cos(math.radians(ANGLE)) * LENGTH / 2
reach_y = math.sin(math.radians(ANGLE)) * LENGTH / 2

random.seed(1)
context.set_source_rgba(0.0, 0.0, 0.0, 0.7)
context.set_line_width(0.4)
context.set_line_cap(cairo.LINE_CAP_ROUND)
for _ in range(width * height // 6):
    x = random.random() * width
    y = random.random() * height
    if random.random() < darkness[int(y), int(x)]:
        context.move_to(x - reach_x, y - reach_y)
        context.line_to(x + reach_x, y + reach_y)
        context.stroke()

surface.write_to_png("strokes.png")
