import math

import cairo
import numpy as np
from PIL import Image, ImageFilter

SCALE = 2  # the drawing is this many times the size of the photo
SPACING = 10  # distance between needles, in photo pixels
FLAT = 0.01  # slopes gentler than this count as flat

photo = Image.open("photo.png").convert("L")
height, width = photo.height, photo.width

# Blur first, so that single noisy pixels do not send the needles spinning.
smooth = np.asarray(photo.filter(ImageFilter.GaussianBlur(3))) / 255
# How fast the brightness changes at each pixel, going down and going across.
down, across = np.gradient(smooth)
steepness = np.hypot(across, down)
uphill = np.arctan2(down, across)
# Contours run across the slope: a quarter turn from uphill.
contour = uphill + math.pi / 2
# Where the photo is flat there is no contour, so fall back to 45 degrees.
angle = np.where(steepness > FLAT, contour, math.radians(45))

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width * SCALE, height * SCALE)
context = cairo.Context(surface)
context.scale(SCALE, SCALE)

context.set_source_rgb(1.0, 1.0, 1.0)
context.paint()

context.set_source_rgb(0.0, 0.0, 0.0)
context.set_line_width(1.0)
context.set_line_cap(cairo.LINE_CAP_ROUND)
reach = SPACING * 0.45
for y in range(SPACING // 2, height, SPACING):
    for x in range(SPACING // 2, width, SPACING):
        step_x, step_y = math.cos(angle[y, x]), math.sin(angle[y, x])
        context.move_to(x - step_x * reach, y - step_y * reach)
        context.line_to(x + step_x * reach, y + step_y * reach)
        context.stroke()

surface.write_to_png("field.png")
