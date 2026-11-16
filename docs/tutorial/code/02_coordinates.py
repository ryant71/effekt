import math

import cairo

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 300)
context = cairo.Context(surface)

context.set_source_rgb(1.0, 1.0, 1.0)
context.paint()

# Six dots. Each one is 60 pixels further right and 40 pixels further down.
context.set_source_rgb(0.1, 0.3, 0.6)
for step in range(6):
    x = 50 + step * 60
    y = 50 + step * 40
    context.arc(x, y, 5 + step * 3, 0, math.tau)
    context.fill()

surface.write_to_png("coordinates.png")
