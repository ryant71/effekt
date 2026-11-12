# effekt

Generative image effects rendered with cairo. Each effect reads a reference
image and writes a PNG.

| Effect            | What it does                                                        |
| ----------------- | ------------------------------------------------------------------- |
| `bloom`           | Every pixel emits an additive disc sized by its brightness.         |
| `regrain`         | Rebuilds the image from random red, green and blue film grains.     |
| `colours-natural` | A pen wanders over the image, steered by the bytes of a file.       |
| `ebs`             | Swarms of entities flock across the image and leave coloured trails. |
| `quant`           | Subdivides the image wherever it has detail and strokes each cell.  |

## Install

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/) and the cairo development
files (`libcairo2-dev` on Debian/Ubuntu, `brew install cairo pkg-config` on macOS).

```sh
uv sync
```

## Usage

```sh
uv run effekt bloom entropy.bin photo.png out.png
uv run effekt regrain photo.png out.png --seed 1
uv run effekt colours-natural strokes.bin photo.png out.png
uv run effekt ebs photo.png out.png 5000
uv run effekt quant photo.png out.png
```

`entropy.bin` and `strokes.bin` can be any file; `colours-natural` draws one
stroke per byte. Every effect has tuning options, listed by
`uv run effekt <effect> --help`.

The effects are also importable:

```python
from pathlib import Path

from effekt import Reference, quant

surface = quant.render(Reference.load(Path("photo.png")))
surface.write_to_png("out.png")
```

## Development

```sh
uv run pytest
uv run ruff check
uv run ruff format
```

## Licence

The effects are Copyright Lasse Nielsen 2011 (<http://www.effekts.dk>),
licensed [CC BY-NC 3.0](http://www.creativecommons.org/licenses/by-nc/3.0/).
