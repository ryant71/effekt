import math

import cairo

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 300)
context = cairo.Context(surface)

context.set_source_rgb(1.0, 1.0, 1.0)
context.paint()

# The fourth number is alpha: 0.0 is invisible, 1.0 is solid.
context.set_source_rgba(0.9, 0.2, 0.2, 0.5)
context.arc(160, 120, 90, 0, math.tau)
context.fill()

context.set_source_rgba(0.2, 0.7, 0.3, 0.5)
context.arc(240, 120, 90, 0, math.tau)
context.fill()

context.set_source_rgba(0.2, 0.3, 0.9, 0.5)
context.arc(200, 190, 90, 0, math.tau)
context.fill()

surface.write_to_png("transparency.png")
