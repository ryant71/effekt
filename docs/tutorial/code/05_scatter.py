import math
import random

import cairo
import numpy as np
from PIL import Image

SCALE = 2  # the drawing is this many times the size of the photo

photo = Image.open("photo.png").convert("L")
darkness = 1 - np.asarray(photo) / 255
height, width = darkness.shape

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width * SCALE, height * SCALE)
context = cairo.Context(surface)
context.scale(SCALE, SCALE)

context.set_source_rgb(1.0, 1.0, 1.0)
context.paint()

random.seed(1)
context.set_source_rgb(0.0, 0.0, 0.0)
for _ in range(width * height // 2):
    x = random.random() * width
    y = random.random() * height
    # Dark places keep most of the dots that land on them, light places few.
    if random.random() < darkness[int(y), int(x)]:
        context.arc(x, y, 0.5, 0, math.tau)
        context.fill()

surface.write_to_png("scatter.png")
