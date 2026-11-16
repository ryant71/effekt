from pathlib import Path

import numpy as np
import pytest
import shtab
from PIL import Image

from effekt import Reference, bloom, colours_natural, colours_spiral, ebs, hatch, quant, regrain
from effekt.cli import build_parser, main

ENTROPY = bytes(range(256)) * 2


def pixels(surface) -> np.ndarray:
    """The surface as a (height, width, 4) uint8 array."""
    surface.flush()
    data = np.frombuffer(surface.get_data(), dtype=np.uint8)
    return data.reshape(surface.get_height(), surface.get_width(), 4).copy()


def make_image(width: int, height: int) -> Image.Image:
    """A deterministic test card: colour gradients with noise on top."""
    rng = np.random.default_rng(0)
    x = np.linspace(0, 255, width)[None, :].repeat(height, axis=0)
    y = np.linspace(0, 255, height)[:, None].repeat(width, axis=1)
    card = np.stack([x, y, 255 - x], axis=2) + rng.integers(-30, 30, (height, width, 3))
    return Image.fromarray(card.clip(0, 255).astype(np.uint8), "RGB")


@pytest.fixture
def reference() -> Reference:
    return Reference.from_image(make_image(24, 16))


RENDERERS = {
    "bloom": lambda ref: bloom.render(ref, ENTROPY),
    "colours-natural": lambda ref: colours_natural.render(ref, ENTROPY),
    "colours-spiral": lambda ref: colours_spiral.render(ref),
    "ebs": lambda ref: ebs.render(ref, 60),
    "hatch": lambda ref: hatch.render(ref, hatch.HatchParams(seed=1)),
    "quant": lambda ref: quant.render(ref),
    "regrain": lambda ref: regrain.render(ref, regrain.RegrainParams(seed=1)),
}
SCALES = {
    "bloom": 2,
    "colours-natural": 4,
    "colours-spiral": 2,
    "ebs": 1,
    "hatch": 2,
    "quant": 4,
    "regrain": 4,
}


@pytest.mark.parametrize("effect", RENDERERS)
def test_render_draws_at_the_scaled_size(effect, reference):
    result = pixels(RENDERERS[effect](reference))

    assert result.shape == (16 * SCALES[effect], 24 * SCALES[effect], 4)
    assert result[..., :3].any()


@pytest.mark.parametrize("effect", RENDERERS)
def test_render_is_reproducible(effect, reference):
    first = pixels(RENDERERS[effect](reference))
    second = pixels(RENDERERS[effect](reference))

    assert np.array_equal(first, second)


def test_reference_converts_any_image_mode():
    paletted = make_image(8, 6).convert("P")

    reference = Reference.from_image(paletted)

    assert (reference.width, reference.height) == (8, 6)
    assert reference.rgb.shape == (6, 8, 3)
    assert 0.0 <= reference.rgb.min() <= reference.rgb.max() <= 1.0


def test_reference_rejects_tiny_images():
    with pytest.raises(ValueError, match="at least 4x4"):
        Reference.from_image(Image.new("RGB", (3, 10)))


def test_bloom_rejects_too_little_entropy(reference):
    with pytest.raises(ValueError, match="at least 4 bytes"):
        bloom.render(reference, b"abc")


def test_bloom_entropy_is_optional(reference):
    assert pixels(bloom.render(reference)).any()


def test_bloom_brightens_light_areas_more():
    half = np.zeros((8, 16, 3), dtype=np.uint8)
    half[:, 8:] = 200
    result = pixels(bloom.render(Reference.from_image(Image.fromarray(half, "RGB")), ENTROPY))

    assert result[:, 24:, :3].mean() > result[:, :8, :3].mean()
    assert not result[:, :8, :3].any()


def test_regrain_seed_changes_the_grain(reference):
    one = pixels(regrain.render(reference, regrain.RegrainParams(seed=1)))
    two = pixels(regrain.render(reference, regrain.RegrainParams(seed=2)))

    assert not np.array_equal(one, two)


def test_colours_draws_one_stroke_per_byte(reference):
    calls = []
    colours_natural.render(
        reference,
        ENTROPY,
        colours_natural.ColoursParams(island=101),
        lambda done, total: calls.append((done, total)),
    )

    assert calls == [(100, 512), (200, 512), (300, 512), (400, 512), (500, 512), (512, 512)]


def test_spiral_starts_at_the_centre_and_reaches_the_corners():
    reference = Reference.from_image(Image.new("RGB", (32, 32), "black"))

    alpha = pixels(colours_spiral.render(reference))[..., 3]

    assert alpha[32, 32] == 255
    assert alpha[0, 0] and alpha[0, -1] and alpha[-1, 0] and alpha[-1, -1]


def test_spiral_draws_thicker_where_the_image_is_darker():
    halves = np.full((32, 64, 3), 230, dtype=np.uint8)
    halves[:, :32] = 40
    reference = Reference.from_image(Image.fromarray(halves, "RGB"))

    alpha = pixels(colours_spiral.render(reference, colours_spiral.SpiralParams(scale=1)))[..., 3]

    assert alpha[:, :28].mean() > alpha[:, 36:].mean() * 2


def test_spiral_takes_the_image_colour(reference):
    black = pixels(colours_spiral.render(reference, colours_spiral.SpiralParams(colour=0.0)))

    assert black[..., 3].any()
    assert not black[..., :3].any()


def test_spiral_rejects_zero_spacing(reference):
    with pytest.raises(ValueError, match="spacing"):
        colours_spiral.render(reference, colours_spiral.SpiralParams(spacing=0.0))


def test_ebs_stops_at_density(reference):
    calls = []
    ebs.render(reference, 60, progress=lambda done, total: calls.append((done, total)))

    assert calls == [(24, 60), (48, 60), (60, 60)]


def test_hatch_follows_contours():
    # Brightness changes only from left to right, so the contours are vertical.
    luma = np.linspace(0, 255, 32)[None, :].repeat(32, axis=0)

    field = hatch.flow_field(luma, smoothing=1.0, angle=0.0, bias=0.0)

    assert np.allclose(np.abs(np.sin(field)), 1.0)


def test_hatch_falls_back_to_the_angle_on_flat_images():
    field = hatch.flow_field(np.full((16, 16), 128.0), 1.0, np.radians(30.0), 0.05)

    assert np.allclose(field, np.radians(30.0))


def test_hatch_is_denser_where_the_image_is_darker():
    luma = np.full((32, 64, 3), 230, dtype=np.uint8)
    luma[:, :32] = 40
    reference = Reference.from_image(Image.fromarray(luma, "RGB"))

    result = pixels(hatch.render(reference, hatch.HatchParams(scale=1, seed=1)))[..., 0]

    assert result[:, :28].mean() < result[:, 36:].mean() - 50


def test_hatch_leaves_white_images_blank():
    reference = Reference.from_image(Image.new("RGB", (16, 16), "white"))

    result = pixels(hatch.render(reference, hatch.HatchParams(seed=1)))

    assert (result == 255).all()


def test_quant_difference_map():
    luma = np.array([[10, 10, 10], [10, 14, 10], [10, 10, 200]], dtype=np.uint8)

    result = quant.difference_map(luma)

    # (|centre - right| + |centre - below|) // 2 * 10, capped at 255; edges stay 0.
    assert result.tolist() == [[0, 20, 0], [20, 40, 0], [0, 0, 0]]


def test_quant_leaves_flat_images_blank():
    flat = Reference.from_image(Image.new("RGB", (16, 16), (90, 120, 150)))

    assert not pixels(quant.render(flat)).any()


def test_quant_handles_portrait_images():
    portrait = Reference.from_image(make_image(8, 40))

    assert pixels(quant.render(portrait)).any()


def test_quant_threshold_limits_subdivision(reference):
    detailed = pixels(quant.render(reference))
    coarse = pixels(quant.render(reference, quant.QuantParams(threshold=1.0)))

    assert detailed.any()
    assert not coarse.any()


@pytest.mark.parametrize(
    "arguments",
    [
        ["bloom", "{image}", "{output}", "--scale", "1"],
        ["bloom", "{image}", "{output}", "--scale", "1", "--entropy", "{entropy}"],
        ["colours-natural", "{entropy}", "{image}", "{output}", "--scale", "2"],
        ["colours-spiral", "{image}", "{output}", "--scale", "1"],
        ["ebs", "{image}", "{output}", "30"],
        ["hatch", "{image}", "{output}", "--scale", "1", "--seed", "3"],
        ["quant", "{image}", "{output}"],
        ["regrain", "{image}", "{output}", "--scale", "1", "--seed", "3"],
    ],
    ids=lambda arguments: arguments[0],
)
def test_cli_writes_a_png(arguments, tmp_path):
    paths = {
        "entropy": tmp_path / "entropy.bin",
        "image": tmp_path / "in.png",
        "output": tmp_path / "out.png",
    }
    paths["entropy"].write_bytes(ENTROPY)
    make_image(24, 16).save(paths["image"])

    exit_code = main([argument.format(**paths) for argument in arguments])

    assert exit_code == 0
    with Image.open(paths["output"]) as written:
        scale = int(arguments[arguments.index("--scale") + 1]) if "--scale" in arguments else None
        assert written.size == (
            24 * (scale or SCALES[arguments[0]]),
            16 * (scale or SCALES[arguments[0]]),
        )


def test_cli_reports_a_missing_input(tmp_path, capsys):
    exit_code = main(["quant", str(tmp_path / "missing.png"), str(tmp_path / "out.png")])

    assert exit_code == 1
    assert "missing.png" in capsys.readouterr().err


@pytest.mark.parametrize("shell", ["bash", "zsh", "tcsh", "fish", "powershell"])
def test_cli_prints_a_completion_script(shell, capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--print-completion", shell])
    assert exit_info.value.code == 0
    script = capsys.readouterr().out
    for effect in (
        "bloom",
        "colours-natural",
        "colours-spiral",
        "ebs",
        "hatch",
        "quant",
        "regrain",
    ):
        assert effect in script
    assert "--entropy" in script


def test_cli_completes_paths_as_files():
    commands = build_parser()._subparsers._group_actions[0].choices
    paths = [a for sub in commands.values() for a in sub._actions if a.type is Path]
    assert len(paths) == 16
    assert all(a.complete == shtab.FILE for a in paths)
