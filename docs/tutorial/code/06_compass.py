import math

import cairo

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 400)
context = cairo.Context(surface)

context.set_source_rgb(1.0, 1.0, 1.0)
context.paint()

context.set_line_width(3)
context.set_line_cap(cairo.LINE_CAP_ROUND)
context.set_font_size(16)
for degrees in range(0, 360, 30):
    angle = math.radians(degrees)
    # One step in this direction: cos gives the sideways part, sin the downwards part.
    step_x, step_y = math.cos(angle), math.sin(angle)

    # The first three lines are red, to show which way the angles turn.
    if degrees <= 60:
        context.set_source_rgb(0.9, 0.3, 0.2)
    else:
        context.set_source_rgb(0.6, 0.6, 0.6)
    context.move_to(200 + step_x * 30, 200 + step_y * 30)
    context.line_to(200 + step_x * 130, 200 + step_y * 130)
    context.stroke()

    context.set_source_rgb(0.2, 0.2, 0.2)
    context.move_to(200 + step_x * 165 - 14, 200 + step_y * 165 + 6)
    context.show_text(f"{degrees}°")

surface.write_to_png("compass.png")
