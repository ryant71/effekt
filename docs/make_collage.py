"""Regenerate docs/collage.jpg, the picture at the top of the README.

Run from the repository root, after docs/make_examples.py::

    uv run python docs/make_collage.py

It arranges the two test photos and a sample of the example results into a
grid of labelled square tiles.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DOCS = Path(__file__).parent
IMAGES = DOCS / "images"
PHOTOS = DOCS.parent / "test-images"
TILE = 240
LABEL = 30
GAP = 6
COLUMNS = 5

#: Each tile's label and picture, row by row. A row starts with the photo its effects used.
TILES = (
    ("photo", PHOTOS / "lena-test.png"),
    ("halftone --cmyk", IMAGES / "halftone-cmyk.jpg"),
    ("hatch", IMAGES / "hatch-default.jpg"),
    ("colours-spiral", IMAGES / "spiral-default.jpg"),
    ("stipple", IMAGES / "stipple-default.jpg"),
    ("regrain", IMAGES / "regrain-default.jpg"),
    ("quant", IMAGES / "quant-default.jpg"),
    ("colours-natural", IMAGES / "colours-default.jpg"),
    ("ebs", IMAGES / "ebs-20000.jpg"),
    ("bloom", IMAGES / "bloom-exposure-1.jpg"),
    ("photo", PHOTOS / "lena-old.jpg"),
    ("string-art", IMAGES / "string-portrait.jpg"),
    ("hatch", IMAGES / "hatch-portrait.jpg"),
    ("colours-spiral", IMAGES / "spiral-portrait.jpg"),
    ("stipple", IMAGES / "stipple-portrait.jpg"),
)


def tile(path: Path) -> Image.Image:
    """The picture cut to a square and reduced. Tall pictures keep their upper part."""
    with Image.open(path) as picture:
        picture = picture.convert("RGB")
    side = min(picture.size)
    left = (picture.width - side) // 2
    top = (picture.height - side) // 4
    square = picture.crop((left, top, left + side, top + side))
    return square.resize((TILE, TILE), Image.Resampling.LANCZOS)


def build() -> None:
    rows = -(-len(TILES) // COLUMNS)
    width = COLUMNS * TILE + (COLUMNS + 1) * GAP
    height = rows * (TILE + LABEL) + (rows + 1) * GAP
    collage = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(collage)
    font = ImageFont.load_default(16)

    for index, (label, path) in enumerate(TILES):
        x = GAP + (index % COLUMNS) * (TILE + GAP)
        y = GAP + (index // COLUMNS) * (TILE + LABEL + GAP)
        collage.paste(tile(path), (x, y))
        draw.rectangle((x, y, x + TILE - 1, y + TILE - 1), outline=(200, 200, 200))
        colour = (150, 60, 40) if label == "photo" else (60, 60, 60)
        draw.text((x + TILE / 2, y + TILE + LABEL / 2), label, fill=colour, font=font, anchor="mm")

    collage.save(DOCS / "collage.jpg", quality=85, optimize=True)
    print(f"Wrote {DOCS / 'collage.jpg'} ({width}x{height})")


if __name__ == "__main__":
    build()
