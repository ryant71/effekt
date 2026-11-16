"""Regenerate the tutorial's images and keep its pages in step with its code.

Run from the repository root::

    uv run python docs/make_tutorial.py

The pages in docs/tutorial are written by hand, but four things in them are
filled in by this script, so that they cannot drift from the real code:

* A code block after ``<!-- code: PATH -->`` holds that file. Add ``: NAME`` to
  show only the top-level function or class of that name.
* A text block after ``<!-- output: SCRIPT -->`` holds what that script printed.
* Every link to the glossary gets the entry's first paragraph as its hover text.
* The lines between ``<!-- nav -->`` and ``<!-- /nav -->`` link the pages together.

Every script in docs/tutorial/code is run with the test photo beside it as
``photo.png``, and the picture it writes is reduced into docs/tutorial/images.
"""

import ast
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

DOCS = Path(__file__).parent
TUTORIAL = DOCS / "tutorial"
CODE = TUTORIAL / "code"
IMAGES = TUTORIAL / "images"
OUTPUT = TUTORIAL / "output"
PHOTO = DOCS.parent / "test-images" / "lena-test.png"
GLOSSARY = "09-glossary.md"
CONTENTS = "README.md"
#: Longest side of a stored picture.
STORED_SIDE = 600

CODE_BLOCK = re.compile(r"(<!-- code: (\S+?)(?: : (\w+))? -->\n```python\n).*?(```)", re.DOTALL)
OUTPUT_BLOCK = re.compile(r"(<!-- output: (\w+) -->\n```text\n).*?(```)", re.DOTALL)
GLOSSARY_LINK = re.compile(rf'\]\({re.escape(GLOSSARY)}#([a-z0-9-]+)(?: "[^"]*")?\)')
NAV_BLOCK = re.compile(r"(<!-- nav -->\n).*?(<!-- /nav -->)", re.DOTALL)
MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")


def pages() -> list[Path]:
    """The numbered pages, in reading order."""
    return sorted(TUTORIAL.glob("[0-9][0-9]-*.md"))


def title(page: Path) -> str:
    return page.read_text().splitlines()[0].removeprefix("# ")


def run_script(script: Path, photo: Path, workdir: Path) -> tuple[str, list[Path]]:
    """Run one tutorial script beside ``photo.png``. Returns its output and its pictures."""
    shutil.copy(photo, workdir / "photo.png")
    result = subprocess.run(
        [sys.executable, str(script)], cwd=workdir, capture_output=True, text=True, check=True
    )
    pictures = sorted(path for path in workdir.glob("*.png") if path.name != "photo.png")
    return result.stdout, pictures


def run_scripts() -> None:
    """Run every script and store what it drew or printed."""
    IMAGES.mkdir(exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)
    for script in sorted(CODE.glob("*.py")):
        with tempfile.TemporaryDirectory() as scratch:
            printed, pictures = run_script(script, PHOTO, Path(scratch))
            if printed:
                (OUTPUT / f"{script.stem}.txt").write_text(printed)
            for picture in pictures:
                with Image.open(picture) as drawn:
                    flat = Image.new("RGBA", drawn.size, "white")
                    flat.alpha_composite(drawn.convert("RGBA"))
                reduced = flat.convert("RGB")
                reduced.thumbnail((STORED_SIDE, STORED_SIDE), Image.Resampling.LANCZOS)
                # Drawings made from the photo are photographic; the rest are flat colour.
                if "photo.png" in script.read_text():
                    reduced.save(IMAGES / f"{script.stem}.jpg", quality=85, optimize=True)
                else:
                    reduced.save(IMAGES / f"{script.stem}.png", optimize=True)
        print(f"ran {script.name}")


def excerpt(path: Path, name: str | None) -> str:
    """A whole file, or the source of one of its top-level functions or classes."""
    source = path.read_text()
    if name is None:
        return source
    for node in ast.parse(source).body:
        if isinstance(node, ast.FunctionDef | ast.ClassDef) and node.name == name:
            first = min([node.lineno, *(d.lineno for d in node.decorator_list)])
            return "\n".join(source.splitlines()[first - 1 : node.end_lineno]) + "\n"
    raise LookupError(f"{path} has no top-level function or class called {name}")


def definitions() -> dict[str, str]:
    """Each glossary entry's first paragraph as plain text, keyed by its link anchor."""
    found = {}
    for entry in re.split(r"^### ", (TUTORIAL / GLOSSARY).read_text(), flags=re.MULTILINE)[1:]:
        heading, _, body = entry.partition("\n")
        anchor = re.sub(r"[^a-z0-9 -]", "", heading.lower()).replace(" ", "-")
        paragraph = " ".join(body.strip().split("\n\n")[0].split())
        plain = MARKDOWN_LINK.sub(r"\1", paragraph).replace("`", "").replace('"', "'")
        found[anchor] = plain
    return found


def navigation(page: Path, order: list[Path]) -> str:
    """Links to the pages before and after this one."""
    index = order.index(page)
    links = []
    if index > 0:
        links.append(f"[← {title(order[index - 1])}]({order[index - 1].name})")
    links.append(f"[Contents]({CONTENTS})")
    if index + 1 < len(order):
        links.append(f"[{title(order[index + 1])} →]({order[index + 1].name})")
    return " · ".join(links) + "\n"


def synced(page: Path, order: list[Path], glossary: dict[str, str]) -> str:
    """The page's text with its generated parts brought up to date."""
    text = page.read_text()

    def code(match: re.Match) -> str:
        return match[1] + excerpt((TUTORIAL / match[2]).resolve(), match[3]) + match[4]

    def output(match: re.Match) -> str:
        return match[1] + (OUTPUT / f"{match[2]}.txt").read_text() + match[3]

    def hover(match: re.Match) -> str:
        return f'](09-glossary.md#{match[1]} "{glossary[match[1]]}")'

    text = CODE_BLOCK.sub(code, text)
    text = OUTPUT_BLOCK.sub(output, text)
    if page.name != GLOSSARY:
        text = GLOSSARY_LINK.sub(hover, text)
    if page in order:
        text = NAV_BLOCK.sub(lambda match: match[1] + navigation(page, order) + match[2], text)
    return text


def sync_pages(check: bool = False) -> list[str]:
    """Bring every page up to date. Returns the names of the pages that were stale.

    With ``check`` the pages are left as they are.
    """
    order = pages()
    glossary = definitions()
    stale = []
    for page in [TUTORIAL / CONTENTS, *order]:
        text = synced(page, order, glossary)
        if text != page.read_text():
            stale.append(page.name)
            if not check:
                page.write_text(text)
    return stale


if __name__ == "__main__":
    run_scripts()
    changed = sync_pages()
    print(f"updated {len(changed)} pages: {', '.join(changed) or 'none'}")
