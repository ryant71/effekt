import cairo

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 300)
context = cairo.Context(surface)

context.set_source_rgb(1.0, 1.0, 1.0)
context.paint()

# Sketch a triangle: three corners, then back to the start.
context.move_to(200, 30)
context.line_to(340, 220)
context.line_to(60, 220)
context.close_path()

# Colour it in, but keep the sketch so that it can be outlined too.
context.set_source_rgb(1.0, 0.8, 0.2)
context.fill_preserve()

context.set_source_rgb(0.2, 0.2, 0.2)
context.set_line_width(8)
context.stroke()

# A zigzag is a path that is never closed, so it can only be stroked.
context.move_to(40, 270)
for corner in range(1, 9):
    context.line_to(40 + corner * 40, 270 if corner % 2 == 0 else 250)
context.set_source_rgb(0.1, 0.3, 0.6)
context.set_line_width(4)
context.set_line_cap(cairo.LINE_CAP_ROUND)
context.set_line_join(cairo.LINE_JOIN_ROUND)
context.stroke()

surface.write_to_png("paths.png")
