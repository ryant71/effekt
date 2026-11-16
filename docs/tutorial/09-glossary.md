# Glossary and further reading

<!-- nav -->
[← How it fits together](08-how-it-fits-together.md) · [Contents](README.md)
<!-- /nav -->

Every term the tutorial links to. The first paragraph of each entry is what you see when you hover over a link to it.

## Glossary

### Alpha

How solid a colour is, from 0.0 (invisible) to 1.0 (hides everything beneath it).

It is the fourth number given to `set_source_rgba`. Marks drawn with a low alpha build up where they overlap, which is how most of the effects make dark areas. See [alpha compositing](https://en.wikipedia.org/wiki/Alpha_compositing). Introduced on [page 2](02-drawing.md#see-through-colour).

### Array

A grid of numbers held by NumPy, like a spreadsheet with one cell per pixel.

Arithmetic on an array applies to every cell at once. A cell is read with `array[row, column]`, which is `array[y, x]`. See NumPy's [guide for absolute beginners](https://numpy.org/doc/stable/user/absolute_beginners.html). Introduced on [page 3](03-reading-a-photo.md).

### Blur

Smoothing a photo by mixing each pixel with its neighbours, so that small details and noise fade and large shapes remain.

The tutorial uses Pillow's [`GaussianBlur`](https://pillow.readthedocs.io/en/stable/reference/ImageFilter.html#PIL.ImageFilter.GaussianBlur). See also [Gaussian blur](https://en.wikipedia.org/wiki/Gaussian_blur). Introduced on [page 6](06-direction.md#two-problems-two-fixes).

### Context

The hand that draws on a surface. It carries out your drawing instructions and remembers the current colour, pen width and path.

Created with `cairo.Context(surface)`. See the [pycairo Context reference](https://pycairo.readthedocs.io/en/latest/reference/context.html). Introduced on [page 1](01-first-picture.md#the-paper-and-the-hand).

### Contour

A line joining places of equal brightness, like the height lines on a walker's map. Strokes that follow contours show the form of what they draw.

It runs at a right angle to the gradient. See [contour line](https://en.wikipedia.org/wiki/Contour_line). Introduced on [page 6](06-direction.md#brightness-as-a-landscape).

### Darkness

How much ink a pixel needs, from 0 (white paper) to 1 (solid black). It is brightness turned upside down.

Calculated as `1 - luma / 255`. Introduced on [page 4](04-halftone.md#darkness).

### Dataclass

A class whose only job is to hold named values. You list the names, types and defaults, and Python writes the rest.

The project uses one per effect to hold its settings. See Python's [`dataclasses` documentation](https://docs.python.org/3/library/dataclasses.html). Introduced on [page 8](08-how-it-fits-together.md#the-settings-a-dataclass).

### Fill

Colouring in the inside of a path with the current colour. The path is erased afterwards.

`fill_preserve` does the same and keeps the path. Introduced on [page 1](01-first-picture.md#pick-sketch-commit).

### Flow field

A direction for every point of a picture, like a map of wind or the pattern of iron filings around a magnet.

In the tutorial it is an array holding one angle per pixel. See [vector field](https://en.wikipedia.org/wiki/Vector_field). Introduced on [page 6](06-direction.md#seeing-the-directions).

### Gradient

The direction in which a photo gets brighter fastest at a given pixel, and how fast. On a landscape where brightness is height, it points uphill.

`np.gradient` returns it as two arrays: the change going down and the change going across. See [image gradient](https://en.wikipedia.org/wiki/Image_gradient) and the [`numpy.gradient` reference](https://numpy.org/doc/stable/reference/generated/numpy.gradient.html). Introduced on [page 6](06-direction.md#brightness-as-a-landscape).

### Halftone

Printing shades of grey with dots of a single ink: large dots for dark areas, small ones for light.

See [halftone](https://en.wikipedia.org/wiki/Halftone). Built on [page 4](04-halftone.md).

### Hatching

Shading with many roughly parallel pen strokes, closer together or more numerous where the drawing is darker.

See [hatching](https://en.wikipedia.org/wiki/Hatching). Built on [page 5](05-chance.md#from-dots-to-strokes) and [page 7](07-hatch.md).

### Luma

How bright a pixel looks, as one number from 0 (black) to 255 (white). It is what a colour photo becomes when turned grey.

Pillow calculates it with `.convert("L")`, weighting green most and blue least. See [luma](https://en.wikipedia.org/wiki/Luma_%28video%29). Introduced on [page 3](03-reading-a-photo.md).

### Path

The shape the context has sketched so far but not yet drawn, like a faint pencil line. It becomes visible only when filled or stroked.

Built with `move_to`, `line_to`, `arc`, `rectangle` and `close_path`. See the [cairo tutorial](https://www.cairographics.org/tutorial/). Introduced on [page 1](01-first-picture.md#pick-sketch-commit) and [page 2](02-drawing.md#shapes-from-lines).

### Pixel

One of the tiny squares of colour that a photo, a screen or an image surface is made of.

### Radian

A unit for angles in which a full turn is 2π (about 6.28) instead of 360 degrees. Python's maths functions use it.

Convert with `math.radians(degrees)`. `math.tau` is a full turn and `math.pi / 2` a quarter turn. See [radian](https://en.wikipedia.org/wiki/Radian). Introduced on [page 6](06-direction.md#an-angle-is-a-direction).

### RGB

A colour described as amounts of red, green and blue light. Cairo wants each amount from 0.0 to 1.0; image files store each from 0 to 255.

See [RGB color model](https://en.wikipedia.org/wiki/RGB_color_model). Introduced on [page 1](01-first-picture.md#pick-sketch-commit).

### Seed

The starting point for a run of random numbers. The same seed gives the same numbers in the same order, and so the same picture.

Set with `random.seed(1)`. See [random seed](https://en.wikipedia.org/wiki/Random_seed). Introduced on [page 5](05-chance.md#the-same-luck-every-time).

### Stroke

Going over a path with a pen of the current colour and line width. The path is erased afterwards.

Introduced on [page 2](02-drawing.md#fill-and-stroke).

### Surface

The sheet of paper that cairo draws on. An image surface is a grid of pixels held in memory, which can be saved as a PNG file.

Created with `cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)`. See the [pycairo surfaces reference](https://pycairo.readthedocs.io/en/latest/reference/surfaces.html). Introduced on [page 1](01-first-picture.md#the-paper-and-the-hand).

### Vector graphics

Pictures described as shapes (a circle here, a line there) and not as pixels, so they can be drawn sharply at any size.

Cairo is a vector graphics library: it turns shapes into pixels only at the last moment. See [vector graphics](https://en.wikipedia.org/wiki/Vector_graphics). Introduced on [page 4](04-halftone.md#a-bigger-drawing).

## Further reading

**Cairo**

- [An Introduction to Cairo with Python](https://pycairo.readthedocs.io/en/latest/tutorial/introduction.html), pycairo's own tutorial.
- [The cairo tutorial](https://www.cairographics.org/tutorial/), which explains the drawing model with diagrams. Its examples are in C, but the function names match.
- [Cairo's compositing operators](https://www.cairographics.org/operators/), for what happens when one colour is drawn over another. `bloom`, `regrain` and `halftone` each use an operator other than the default.

**Pillow and NumPy**

- [The Pillow tutorial](https://pillow.readthedocs.io/en/stable/handbook/tutorial.html).
- [NumPy: the absolute basics for beginners](https://numpy.org/doc/stable/user/absolute_beginners.html).
- [Indexing on NumPy arrays](https://numpy.org/doc/stable/user/basics.indexing.html), for slicing in full.

**The ideas**

- [Halftone](https://en.wikipedia.org/wiki/Halftone) and [hatching](https://en.wikipedia.org/wiki/Hatching) on Wikipedia.
- [Generative art](https://en.wikipedia.org/wiki/Generative_art), the wider field this project belongs to.

**This project**

- [The examples page](../examples.md) shows every effect and what each option does.
- [The source](../../src/effekt/) has one file per effect. After this tutorial, `halftone.py`, `hatch.py` and `colours_spiral.py` are the easiest to read.

<!-- nav -->
[← How it fits together](08-how-it-fits-together.md) · [Contents](README.md)
<!-- /nav -->
