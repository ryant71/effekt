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

To work on the code, or to run it from a checkout with `uv run effekt`:

```sh
uv sync
```

To install the `effekt` command for your user (uv puts it in `~/.local/bin`):

```sh
uv tool install .                      # from a checkout
uv tool install git+https://github.com/ryant71/effekt   # or straight from GitHub
```

If `effekt` is not found afterwards, run `uv tool update-shell` to add that
directory to your `PATH`. After pulling new changes, reinstall with
`uv tool install --reinstall .`; `uv tool uninstall effekt` removes it. With the
command installed, drop the `uv run` prefix from the examples below.

## Usage

```sh
uv run effekt bloom photo.png out.png
uv run effekt regrain photo.png out.png --seed 1
uv run effekt colours-natural strokes.bin photo.png out.png
uv run effekt ebs photo.png out.png 5000
uv run effekt quant photo.png out.png
```

`strokes.bin` can be any file; `colours-natural` draws one stroke per byte.
Every effect has tuning options, listed by `uv run effekt <effect> --help`.
[docs/examples.md](docs/examples.md) shows what each effect and option does to
a test image.

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

## History and Source

I found this code in, I think, a Reddit post many many years ago and later on
saw it mentioned here <https://www.juhuu.nu/pixelache/2003/hki/artists.php?name=effekt>
and on the site mentioned above.

I make no claim to this code. Please let me know if you want this repo removed
or transferred or whatever.
