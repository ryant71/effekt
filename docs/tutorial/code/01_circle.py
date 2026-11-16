import math

import cairo

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 300)
context = cairo.Context(surface)

context.set_source_rgb(1.0, 1.0, 1.0)
context.paint()

context.set_source_rgb(0.9, 0.3, 0.2)
context.arc(200, 150, 100, 0, math.tau)
context.fill()

surface.write_to_png("circle.png")
