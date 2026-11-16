import math

import cairo
import numpy as np
from PIL import Image

CELL = 6  # each dot stands for a square of this many photo pixels
SCALE = 2  # the drawing is this many times the size of the photo

photo = Image.open("photo.png").convert("L")
darkness = 1 - np.asarray(photo) / 255
height, width = darkness.shape

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width * SCALE, height * SCALE)
context = cairo.Context(surface)
context.scale(SCALE, SCALE)

context.set_source_rgb(1.0, 1.0, 1.0)
context.paint()

context.set_source_rgb(0.0, 0.0, 0.0)
for y in range(0, height, CELL):
    for x in range(0, width, CELL):
        average = darkness[y : y + CELL, x : x + CELL].mean()
        # The dot's area, as a share of its square, matches the darkness.
        radius = CELL * math.sqrt(average / math.pi)
        context.arc(x + CELL / 2, y + CELL / 2, radius, 0, math.tau)
        context.fill()

surface.write_to_png("halftone.png")
