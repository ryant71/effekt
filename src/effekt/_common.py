"""Helpers shared by the effect renderers."""

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Self

import cairo
import numpy as np
from PIL import Image

#: Called as ``progress(done, total)`` while an effect renders.
type ProgressCallback = Callable[[int, int], None]

#: Smallest reference image side; the gradient lookups need interior pixels.
MIN_SIDE = 4


def option(default: Any, help: str) -> Any:
    """Declare a parameter dataclass field that the CLI exposes as ``--name``."""
    return field(default=default, metadata={"help": help})


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def blur(values: np.ndarray, sigma: float) -> np.ndarray:
    """Gaussian blur of a 2D array, repeating the edge pixels outwards."""
    if sigma <= 0.0:
        return values
    radius = max(int(3.0 * sigma + 0.5), 1)
    kernel = np.exp(-0.5 * (np.arange(-radius, radius + 1) / sigma) ** 2)
    kernel /= kernel.sum()
    for axis in (0, 1):
        pad = [(radius, radius) if a == axis else (0, 0) for a in (0, 1)]
        padded = np.pad(values, pad, mode="edge")
        values = np.apply_along_axis(np.convolve, axis, padded, kernel, mode="valid")
    return values


def no_progress(done: int, total: int) -> None:
    """Default progress callback: report nothing."""


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


def new_canvas(width: int, height: int) -> tuple[cairo.ImageSurface, cairo.Context]:
    """Create a transparent ARGB surface and a context that draws on it."""
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    return surface, cairo.Context(surface)
