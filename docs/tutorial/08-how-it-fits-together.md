# How it fits together

<!-- nav -->
[← Hatch](07-hatch.md) · [Contents](README.md) · [Glossary and further reading →](09-glossary.md)
<!-- /nav -->

You have written two effects as scripts. This page is a tour of the project around them: how it turns scripts like yours into one tool with ten effects, and why it is arranged the way it is.

## The libraries

| Library | Its job | In the kitchen |
| --- | --- | --- |
| [pycairo](https://pycairo.readthedocs.io/en/latest/) | draws shapes onto a surface | the chef's hands |
| [Pillow](https://pillow.readthedocs.io/en/stable/) | opens image files of any format | the delivery at the back door |
| [NumPy](https://numpy.org/doc/stable/) | does arithmetic on whole grids of numbers | the food processor |
| [`math`](https://docs.python.org/3/library/math.html) and [`random`](https://docs.python.org/3/library/random.html) | angles, square roots, chance | salt and pepper |

`math` and `random` come with Python. So do two more that the project leans on: [`dataclasses`](https://docs.python.org/3/library/dataclasses.html) and [`argparse`](https://docs.python.org/3/library/argparse.html), both described below.

A few tools are only used while working on the project, and are not needed to run it:

- [uv](https://docs.astral.sh/uv/) installs the libraries and runs commands.
- [pytest](https://docs.pytest.org/en/stable/) runs the tests.
- [ruff](https://docs.astral.sh/ruff/) tidies the layout of the code and points out likely mistakes.

## The folders

```text
effekt/
├── pyproject.toml         what the project is called and which libraries it needs
├── README.md
├── src/effekt/            the code that gets installed
│   ├── _common.py         helpers that every effect shares
│   ├── cli.py             the "effekt" command
│   ├── halftone.py        one file per effect
│   ├── hatch.py
│   └── ...
├── tests/                 checks that the effects still work
├── docs/                  the examples page and this tutorial
└── test-images/           photos for the tests and the documentation
```

The rule is **one effect, one file**. To see how `stipple` works, open `stipple.py`. Nothing in one effect's file depends on another's. Anything two effects both need goes in [`_common.py`](../../src/effekt/_common.py).

[`pyproject.toml`](../../pyproject.toml) is the project's label. It lists the libraries to install, and it is where the name of the `effekt` command is tied to the function that runs it. The [Python Packaging User Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) explains the file.

## The shape of an effect

Your `07_hatch.py` reads a fixed file, uses settings written at the top, and saves a fixed file. Every effect in the project does the same work, rearranged into a function:

```python
def render(reference, params, progress):
    ...
    return surface
```

- `reference` is the photo, **already loaded**. The effect never opens a file.
- `params` holds the settings.
- `progress` is a function the effect calls now and then to report how far it has got.
- The surface is handed back, **not saved**.

An effect is a cook who is handed ingredients and hands back a dish. Shopping (opening the file) and serving (saving the PNG) are someone else's job. That is what lets the same `render` be called by the command line, by the tests with a tiny made-up photo, and by your own code.

### The photo: `Reference`

`Reference.load` is the photo-loading from page 3, done once and kept. It holds the two arrays every effect needs: `luma`, the grey levels from 0 to 255, and `rgb`, the colours from 0 to 1.

<details>
<summary>Show the <code>Reference</code> class</summary>

<!-- code: ../../src/effekt/_common.py : Reference -->
```python
@dataclass(frozen=True, slots=True, eq=False)
class Reference:
    """A source image prepared for per-pixel lookups.

    ``luma`` is ``(height, width)`` uint8 and ``rgb`` is ``(height, width, 3)``
    float64 in the range 0..1, which is what cairo expects.
    """

    luma: np.ndarray
    rgb: np.ndarray

    @classmethod
    def from_image(cls, image: Image.Image) -> Self:
        rgb = image.convert("RGB")
        if min(rgb.size) < MIN_SIDE:
            raise ValueError(
                f"reference image must be at least {MIN_SIDE}x{MIN_SIDE} pixels, got "
                f"{rgb.width}x{rgb.height}"
            )
        return cls(
            luma=np.asarray(rgb.convert("L")),
            rgb=np.asarray(rgb, dtype=np.float64) / 255.0,
        )

    @classmethod
    def load(cls, path: Path) -> Self:
        with Image.open(path) as image:
            return cls.from_image(image)

    @property
    def width(self) -> int:
        return self.luma.shape[1]

    @property
    def height(self) -> int:
        return self.luma.shape[0]

    def interior_pixel(self, u: float, v: float) -> tuple[int, int]:
        """Map normalised coordinates to a pixel with a neighbour on every side."""
        return (
            int(clamp(u * self.width, 1, self.width - 3)),
            int(clamp(v * self.height, 1, self.height - 3)),
        )
```

It is itself a dataclass, which the next section explains. `from_image` and `load` are two ways to make one, and `width` and `height` read the size off the array's shape.

</details>

### The settings: a dataclass

The constants at the top of your scripts (`CELL`, `SCALE`, `ANGLE`) become a small class:

<!-- code: ../../src/effekt/halftone.py : HalftoneParams -->
```python
@dataclass(frozen=True, slots=True, kw_only=True)
class HalftoneParams:
    scale: int = option(2, "output size as a multiple of the input size")
    cell: float = option(8.0, "distance between dots, in output pixels")
    angle: float = option(45.0, "angle of the grid of black dots, in degrees")
    cmyk: bool = option(False, "print cyan, magenta, yellow and black screens instead of black")
```

A [dataclass](09-glossary.md#dataclass "A class whose only job is to hold named values. You list the names, types and defaults, and Python writes the rest.") is a class whose only job is to hold named values. You write the names, their types and their defaults, and Python writes the rest of the class for you. Think of it as a **form with the boxes already filled in**: each box has a label and a usual answer, and you change only the ones you care about.

```python
params = HalftoneParams(cell=12.0)  # everything else keeps its default
params.cell  # 12.0
params.angle  # 45.0
```

The words in the brackets after `@dataclass` each switch something on:

- `frozen=True` means the form cannot be altered once filled in. An effect can trust that its settings will not change halfway through a drawing.
- `kw_only=True` means you must write `cell=12.0`, never a bare `12.0`. With several numbers in a row, names prevent mix-ups.
- `slots=True` is a small saving of memory, and it makes a misspelt name an error.

### One description, used twice

Each setting is declared with `option(default, help)` instead of a plain default. `option` is three lines in `_common.py`:

<!-- code: ../../src/effekt/_common.py : option -->
```python
def option(default: Any, help: str) -> Any:
    """Declare a parameter dataclass field that the CLI exposes as ``--name``."""
    return field(default=default, metadata={"help": help})
```

It stores the default as usual and tucks the help text in beside it. That pays off in the command line, which is built **by reading the dataclass**:

<!-- code: ../../src/effekt/cli.py : _add_params -->
```python
def _add_params(parser: argparse.ArgumentParser, params_type: type) -> None:
    """Add one ``--option`` per field of an effect's parameter dataclass."""
    for field in dataclasses.fields(params_type):
        flag = f"--{field.name.replace('_', '-')}"
        if isinstance(field.default, bool):
            parser.add_argument(
                flag,
                action=argparse.BooleanOptionalAction,
                default=field.default,
                help=field.metadata["help"],
            )
            continue
        # Optional fields default to None; the only one so far is an int seed.
        value_type = int if field.default is None else type(field.default)
        parser.add_argument(
            flag,
            type=value_type,
            default=field.default,
            help=field.metadata["help"],
        )
```

For every field in the form, this adds one `--option` to the command: named after the field, converting what you type to the field's type, defaulting to the field's default, and described by its help text. A true-or-false field becomes a pair of switches, such as `--cmyk` and `--no-cmyk`.

So a setting is written down **once**. Add a line to an effect's dataclass and it appears as a command-line option, in `--help`, and in shell completion, with nothing else to edit. Compare that with keeping three lists in step by hand.

## The command line

[`cli.py`](../../src/effekt/cli.py) is the shopping and serving. It uses [`argparse`](https://docs.python.org/3/library/argparse.html), Python's library for reading what was typed after a command. When you run:

```sh
effekt halftone photo.png out.png --cell 12
```

1. `argparse` works out that the effect is `halftone` and collects the file names and options.
2. The options are packed into a `HalftoneParams`.
3. `Reference.load` opens `photo.png`.
4. `halftone.render` is called and hands back a surface.
5. The surface is saved to `out.png`.

Only steps 2 and 4 differ between effects.

## Making it fast

Your hatch script spends nearly all of its time looking up single cells of arrays inside loops. On a small photo that is quick, but the time grows with the number of pixels and strokes. Two habits in the project's code keep it down.

**Do whole-array work in NumPy.** `1 - luma / 255` handles every pixel in one line, and runs at the speed of compiled code. A Python loop over the same pixels would be many times slower. The same goes for `np.gradient` and `np.where` on page 6.

**Turn arrays into lists before a loop that reads one cell at a time.** This looks backwards, but it is real: fetching a single number from a NumPy array is slower than fetching it from a list of lists. So effects that must loop often begin like this, from `hatch.py`:

```python
step_x, step_y = np.cos(field).tolist(), np.sin(field).tolist()
darkness = (1.0 - reference.luma / 255.0).tolist()
```

All the arithmetic is done on the whole array first, then `.tolist()` converts the result for the loop. Lookups change from `darkness[row, column]` to `darkness[row][column]`.

## The maths, in one table

| You want | You use | Seen on |
| --- | --- | --- |
| a radius from an area | `math.sqrt` | page 4 |
| a step from an angle | `math.cos`, `math.sin` | page 6 |
| an angle from a step | `math.atan2`, `np.arctan2` | page 6 |
| the length of a step | `math.hypot`, `np.hypot` | page 6 |
| degrees as radians | `math.radians` | page 6 |
| a full turn, a quarter turn | `math.tau`, `math.pi / 2` | pages 1 and 6 |
| the slope of a photo | `np.gradient` | page 6 |
| whether two steps agree | multiply the parts and add (the dot product) | page 7 |
| something that happens some share of the time | `random.random() < share` | page 5 |
| a point turned about a centre | the rotation formula | page 4 |

That is all of it. There is no calculus to do yourself and nothing beyond school trigonometry.

## The tests

[`tests/test_effects.py`](../../tests/test_effects.py) runs every effect on a tiny made-up photo and checks things that should always be true:

- the drawing is the expected size;
- the same seed gives the same drawing twice;
- dark areas really do get more ink than light ones;
- a pure white photo gives blank paper.

None of them checks that a picture looks **good**. A test cannot judge that. What they catch is the day a change to one file quietly breaks another. Run them with `uv run pytest`.

## Adding an effect of your own

1. Copy an effect that is close to your idea. `halftone.py` is the shortest.
2. Rename the dataclass and give it your settings.
3. Write `render`. Start from a script that works, as on the earlier pages, then move its constants into the dataclass.
4. In `cli.py`, add your module to the imports, add a small function that calls your `render`, and add a `command(...)` block beside the others.
5. Add your effect to the lists at the top of `tests/test_effects.py`, and write one test for the thing that makes your effect itself.
6. Add a few examples to [`docs/make_examples.py`](../make_examples.py) and run it.

<!-- nav -->
[← Hatch](07-hatch.md) · [Contents](README.md) · [Glossary and further reading →](09-glossary.md)
<!-- /nav -->
