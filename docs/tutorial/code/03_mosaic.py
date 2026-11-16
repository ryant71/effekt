import cairo
import numpy as np
from PIL import Image

TILE = 16  # each tile covers this many pixels in each direction

photo = Image.open("photo.png").convert("RGB")
colour = np.asarray(photo) / 255
height, width, channels = colour.shape

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
context = cairo.Context(surface)

for y in range(0, height, TILE):
    for x in range(0, width, TILE):
        red, green, blue = colour[y, x]
        context.set_source_rgb(red, green, blue)
        context.rectangle(x, y, TILE, TILE)
        context.fill()

surface.write_to_png("mosaic.png")
