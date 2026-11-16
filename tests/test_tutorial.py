"""The tutorial's scripts run, and its pages match its code and link to things that exist."""

import importlib.util
import re
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

DOCS = Path(__file__).parent.parent / "docs"
TUTORIAL = DOCS / "tutorial"

spec = importlib.util.spec_from_file_location("make_tutorial", DOCS / "make_tutorial.py")
make_tutorial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(make_tutorial)

PAGES = sorted(TUTORIAL.glob("*.md"))
SCRIPTS = sorted((TUTORIAL / "code").glob("*.py"))
LINK = re.compile(r"\]\(([^)\s]+)(?: \"[^\"]*\")?\)")
IMAGE = re.compile(r'<img src="([^"]+)"')
CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)


def anchors(page: Path) -> set[str]:
    """The link anchors GitHub gives the headings of a page."""
    headings = re.findall(r"^#+ (.+)$", CODE_FENCE.sub("", page.read_text()), re.MULTILINE)
    return {re.sub(r"[^a-z0-9 -]", "", heading.lower()).replace(" ", "-") for heading in headings}


@pytest.fixture(scope="module")
def photo(tmp_path_factory) -> Path:
    """A small photo with an edge in it, so that every script has something to draw."""
    rng = np.random.default_rng(0)
    pixels = rng.integers(150, 256, (40, 56, 3))
    pixels[10:30, 8:30] = rng.integers(0, 90, (20, 22, 3))
    path = tmp_path_factory.mktemp("photo") / "photo.png"
    Image.fromarray(pixels.astype(np.uint8), "RGB").save(path)
    return path


def test_there_is_something_to_check():
    assert len(PAGES) == 10
    assert len(SCRIPTS) == 13


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda script: script.stem)
def test_script_runs(script, photo, tmp_path):
    printed, pictures = make_tutorial.run_script(script, photo, tmp_path)

    assert printed or pictures
    for picture in pictures:
        with Image.open(picture) as drawn:
            assert np.asarray(drawn.convert("RGBA")).any()


def test_pages_match_the_code():
    stale = make_tutorial.sync_pages(check=True)

    assert stale == [], "run `uv run python docs/make_tutorial.py`"


@pytest.mark.parametrize("page", PAGES, ids=lambda page: page.name)
def test_links_and_pictures_exist(page):
    text = CODE_FENCE.sub("", page.read_text())
    targets = [*LINK.findall(text), *IMAGE.findall(text)]
    assert targets

    for target in targets:
        if target.startswith("https://"):
            continue
        path, _, anchor = target.partition("#")
        linked = (page.parent / path).resolve() if path else page
        assert linked.exists(), f"{page.name} links to {target}"
        if anchor:
            assert anchor in anchors(linked), f"{page.name} links to {target}"


@pytest.mark.parametrize("page", PAGES, ids=lambda page: page.name)
def test_glossary_links_have_hover_text(page):
    if page.name == make_tutorial.GLOSSARY:
        return
    text = CODE_FENCE.sub("", page.read_text())

    for anchor, hover in re.findall(r'\]\(09-glossary\.md#([a-z0-9-]+)( "[^"]+")?\)', text):
        assert hover, f"{page.name} links to {anchor} without hover text"


def test_every_script_and_picture_is_used():
    text = "".join(page.read_text() for page in PAGES)

    for script in SCRIPTS:
        assert f"code/{script.name}" in text
    for picture in (TUTORIAL / "images").iterdir():
        assert f"images/{picture.name}" in text
