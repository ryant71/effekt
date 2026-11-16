import math

import cairo
import numpy as np
from PIL import Image

CELL = 6  # each dot stands for a square of this many photo pixels
SCALE = 2  # the drawing is this many times the size of the photo
ANGLE = 30  # how far the grid is turned, in degrees

photo = Image.open("photo.png").convert("L")
darkness = 1 - np.asarray(photo) / 255
height, width = darkness.shape

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width * SCALE, height * SCALE)
context = cairo.Context(surface)
context.scale(SCALE, SCALE)

context.set_source_rgb(1.0, 1.0, 1.0)
context.paint()

turn = math.radians(ANGLE)
along_x, along_y = math.cos(turn), math.sin(turn)
centre_x, centre_y = width / 2, height / 2
# Enough cells, counted from the centre, to reach the corners at any angle.
reach = int(math.hypot(width, height) / 2 / CELL) + 1

context.set_source_rgb(0.0, 0.0, 0.0)
for row in range(-reach, reach + 1):
    for column in range(-reach, reach + 1):
        # Go "column" cells along the turned grid, then "row" cells across it.
        x = centre_x + (column * along_x - row * along_y) * CELL
        y = centre_y + (column * along_y + row * along_x) * CELL
        if not (0 <= x < width and 0 <= y < height):
            continue
        left, top = max(int(x - CELL / 2), 0), max(int(y - CELL / 2), 0)
        average = darkness[top : top + CELL, left : left + CELL].mean()
        radius = CELL * math.sqrt(average / math.pi)
        context.arc(x, y, radius, 0, math.tau)
        context.fill()

surface.write_to_png("halftone_turned.png")
