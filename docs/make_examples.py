"""Regenerate docs/examples.md and the images it shows.

Run from the repository root (takes about a minute)::

    uv run python docs/make_examples.py

Every example really runs the command printed next to it; the result is then
flattened onto white and reduced to fit the page.
"""

import shlex
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from effekt.cli import main

DOCS = Path(__file__).parent
IMAGES = DOCS / "images"
SQUARE = "test-images/lena-test.png"
PORTRAIT = "test-images/lena-old.jpg"
#: Longest side of the stored result, and the width it is displayed at.
STORED_SIDE = 600
DISPLAY_WIDTH = 360


@dataclass(frozen=True)
class Example:
    slug: str
    title: str
    #: Arguments after ``effekt <effect>``; ``{image}`` is the reference image.
    arguments: str
    caption: str
    image: str = SQUARE

    def command(self, effect: str) -> str:
        return f"effekt {effect} {self.arguments.format(image=self.image)}"


@dataclass(frozen=True)
class Section:
    effect: str
    intro: str
    examples: tuple[Example, ...]


SECTIONS = (
    Section(
        "bloom",
        "Every output pixel emits an additive disc of light. Brighter pixels emit bigger discs, "
        "so light areas spread and burn out.",
        (
            Example(
                "bloom-default",
                "Defaults",
                "{image} out.png",
                "`--exposure 10` on a canvas twice the size of the input (`--scale 2`). Each "
                "pixel's disc reaches up to 10 pixels, so all but the darkest areas clip to "
                "white.",
            ),
            Example(
                "bloom-exposure-3",
                "`--exposure 3`",
                "{image} out.png --exposure 3",
                "Overall brightness follows the exposure. At 3 the highlights still clip but "
                "the midtones come back.",
            ),
            Example(
                "bloom-exposure-1",
                "`--exposure 1`",
                "{image} out.png --exposure 1",
                "Close to the source, with harder contrast and a slight glow around highlights.",
            ),
            Example(
                "bloom-exposure-half",
                "`--exposure 0.5`",
                "{image} out.png --exposure 0.5",
                "Underexposed: only the brightest areas register.",
            ),
            Example(
                "bloom-min-exposure",
                "`--min-exposure 1.5`",
                "{image} out.png --exposure 1 --min-exposure 1.5",
                "`--min-exposure` is a floor on the disc radius. Set above the exposure, it "
                "makes every pixel emit a full-size disc, which washes the picture out.",
            ),
            Example(
                "bloom-portrait",
                "A bright portrait at its own size",
                "{image} out.png --scale 1 --exposure 0.5",
                "`--scale 1` keeps the output the size of the input. A low exposure holds the "
                "detail of a light photo, at the cost of a dim, grey result.",
                PORTRAIT,
            ),
        ),
    ),
    Section(
        "regrain",
        "Rebuilds the image from randomly placed red, green and blue grains, like the dye "
        "clouds of colour film. The examples pass `--seed` so they can be reproduced; without "
        "it every run is different.",
        (
            Example(
                "regrain-default",
                "Defaults",
                "{image} out.png --seed 1",
                "A canvas four times the size of the input, one sample per output pixel. The "
                "grain is fine at this size and the colours shift towards red.",
            ),
            Example(
                "regrain-grain-2",
                "`--grain 2`",
                "{image} out.png --seed 1 --grain 2",
                "Bigger grains overlap more, so the picture gets brighter and flatter.",
            ),
            Example(
                "regrain-grain-small",
                "`--grain 0.3`",
                "{image} out.png --seed 1 --grain 0.3",
                "Small grains leave most of the black canvas uncovered.",
            ),
            Example(
                "regrain-iso",
                "`--iso 0.2`",
                "{image} out.png --seed 1 --iso 0.2",
                "`--iso` is how much light each grain holds. Lower values darken the picture "
                "without changing the grain size.",
            ),
            Example(
                "regrain-exposure",
                "`--exposure 0.25`",
                "{image} out.png --seed 1 --exposure 0.25",
                "A quarter of the samples: darker, more speckled, and four times quicker to "
                "render.",
            ),
            Example(
                "regrain-portrait",
                "Coarse grain with `--scale 1`",
                "{image} out.png --seed 1 --scale 1",
                "Grain size is measured in output pixels, so on a canvas the size of the "
                "input the grains are four times coarser relative to the picture.",
                PORTRAIT,
            ),
        ),
    ),
    Section(
        "colours-natural",
        "A pen wanders over the canvas, pulled towards darker areas, and strokes in the colour "
        "underneath. The first argument is a file of stroke data: any file works, and each "
        "byte steers one stroke, so a bigger file means more strokes. Here the image file "
        "doubles as its own stroke data. The background stays transparent.",
        (
            Example(
                "colours-default",
                "Defaults",
                "{image} {image} out.png",
                "473,831 strokes on a canvas four times the size of the input. Strokes are "
                "widest where the image changes fastest, so edges come out and flat areas "
                "stay empty.",
            ),
            Example(
                "colours-island",
                "`--island 400`",
                "{image} {image} out.png --island 400",
                "The pen jumps to a new random spot every 400 steps instead of every 4000, "
                "which spreads the strokes more evenly.",
            ),
            Example(
                "colours-damp",
                "`--damp 0.6`",
                "{image} {image} out.png --damp 0.6",
                "The pen keeps more of its speed between strokes, so it travels further and "
                "the marks become longer and looser.",
            ),
            Example(
                "colours-scale-1",
                "`--scale 1`",
                "{image} {image} out.png --scale 1",
                "On a canvas the size of the input the strokes are thinner and cover much less.",
            ),
            Example(
                "colours-portrait",
                "A bright, low-contrast portrait",
                "test-images/lena-test.png {image} out.png --scale 2",
                "This effect needs contrast: stroke width follows the local gradient, and a "
                "pale image gives it little to work with, so very little is drawn.",
                PORTRAIT,
            ),
        ),
    ),
    Section(
        "ebs",
        "A swarm of entities flocks across the canvas leaving coloured trails, then respawns "
        "somewhere else. The last argument is the density: the number of steps the swarm "
        "takes. The output is the size of the input.",
        (
            Example(
                "ebs-5000",
                "Density 5000",
                "{image} out.png 5000",
                "5000 steps of the default 20 entities: a loose, spiky sketch.",
            ),
            Example(
                "ebs-20000",
                "Density 20000",
                "{image} out.png 20000",
                "More steps fill the canvas and smooth the result.",
            ),
            Example(
                "ebs-entities",
                "`--entities 5`",
                "{image} out.png 20000 --entities 5",
                "A smaller swarm draws fewer, thinner trails and leaves gaps, even at the "
                "same density.",
            ),
            Example(
                "ebs-island",
                "`--island 200`",
                "{image} out.png 5000 --island 200",
                "The swarm travels 200 steps before respawning instead of 25, so the trails "
                "become long streaks that wander off the subject.",
            ),
            Example(
                "ebs-portrait",
                "A larger portrait",
                "{image} out.png 20000",
                "A bigger image needs more steps for the same coverage; 20000 is enough for "
                "this 1000x1500 photo.",
                PORTRAIT,
            ),
        ),
    ),
    Section(
        "quant",
        "Splits the image into quarters wherever it finds detail and strokes each cell in the "
        "colour found there, so busy areas get small marks and calm areas large ones. The "
        "background stays transparent.",
        (
            Example(
                "quant-default",
                "Defaults",
                "{image} out.png",
                "`--threshold 0` subdivides anywhere there is any detail at all, on a canvas "
                "four times the size of the input.",
            ),
            Example(
                "quant-threshold-low",
                "`--threshold 0.1`",
                "{image} out.png --threshold 0.1",
                "A cell is now only split when its average detail exceeds the threshold, so "
                "smooth regions stop early and stay as large strokes or gaps.",
            ),
            Example(
                "quant-threshold-high",
                "`--threshold 0.15`",
                "{image} out.png --threshold 0.15",
                "Higher still, and only the busiest areas are drawn. Much above 0.2 nothing "
                "is drawn for this image.",
            ),
            Example(
                "quant-portrait",
                "A portrait with `--scale 1`",
                "{image} out.png --scale 1",
                "The same pattern on a canvas the size of the input.",
                PORTRAIT,
            ),
        ),
    ),
)


def render(job: tuple[str, Example]) -> tuple[str, tuple[int, int]]:
    """Run one example and store its reduced result. Returns the full output size."""
    effect, example = job
    with tempfile.TemporaryDirectory() as scratch:
        output = Path(scratch) / "out.png"
        arguments = shlex.split(example.command(effect))[1:]
        arguments[arguments.index("out.png")] = str(output)
        sys.stderr = Path("/dev/null").open("w")  # noqa: SIM115 - silence progress output
        if main(arguments) != 0:
            raise RuntimeError(f"failed: {example.command(effect)}")
        with Image.open(output) as result:
            size = result.size
            flat = Image.new("RGBA", size, "white")
            flat.alpha_composite(result.convert("RGBA"))
    reduced = flat.convert("RGB")
    reduced.thumbnail((STORED_SIDE, STORED_SIDE), Image.Resampling.LANCZOS)
    reduced.save(IMAGES / f"{example.slug}.jpg", quality=85, optimize=True)
    return example.slug, size


def picture(source: str, alt: str) -> str:
    return f'<img src="{source}" width="{DISPLAY_WIDTH}" alt="{alt}">'


def page(sizes: dict[str, tuple[int, int]]) -> str:
    lines = [
        "# Examples",
        "",
        "What each effect does and how its options change the result. Every example shows "
        "the input image, the command, and what the command produced.",
        "",
        "The results are reduced to fit the page, and transparent areas are shown as white. "
        "The real size of each output is given above it. Commands assume `effekt` is "
        "installed; from a checkout, put `uv run` in front.",
        "",
        "This page and its images are generated by `uv run python docs/make_examples.py`.",
        "",
        *(f"- [{section.effect}](#{section.effect})" for section in SECTIONS),
    ]
    for section in SECTIONS:
        lines += ["", f"## {section.effect}", "", section.intro]
        for example in section.examples:
            width, height = sizes[example.slug]
            lines += [
                "",
                f"### {example.title}",
                "",
                example.caption,
                "",
                "```sh",
                example.command(section.effect),
                "```",
                "",
                f"| Input | Output ({width}x{height}) |",
                "| --- | --- |",
                f"| {picture(f'../{example.image}', 'input image')} "
                f"| {picture(f'images/{example.slug}.jpg', example.command(section.effect))} |",
            ]
    return "\n".join(lines) + "\n"


def build() -> None:
    IMAGES.mkdir(exist_ok=True)
    jobs = [(section.effect, example) for section in SECTIONS for example in section.examples]
    with ProcessPoolExecutor() as pool:
        sizes = dict(pool.map(render, jobs))
    (DOCS / "examples.md").write_text(page(sizes))
    print(f"Wrote {len(jobs)} examples to {DOCS / 'examples.md'}")


if __name__ == "__main__":
    build()
