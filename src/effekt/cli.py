"""Command line interface: ``effekt <effect> ...``."""

import argparse
import dataclasses
import sys
import time
from collections.abc import Sequence
from datetime import timedelta
from pathlib import Path
from typing import Any

from . import bloom, colours_natural, ebs, quant, regrain
from ._common import ProgressCallback, Reference

REDRAW_INTERVAL = 0.1


class Progress:
    """Prints a live percentage to stderr when it is a terminal."""

    def __init__(self, label: str) -> None:
        self.label = label
        self.live = sys.stderr.isatty()
        self.start = time.perf_counter()
        self._last_draw = 0.0

    def elapsed(self) -> timedelta:
        return timedelta(seconds=int(time.perf_counter() - self.start))

    def __call__(self, done: int, total: int) -> None:
        now = time.perf_counter()
        if not self.live or now - self._last_draw < REDRAW_INTERVAL:
            return
        self._last_draw = now
        fraction = done / total if total else 1.0
        sys.stderr.write(f"\r{self.label}: {fraction:6.1%} in {self.elapsed()}")
        sys.stderr.flush()

    def finish(self) -> None:
        if self.live:
            sys.stderr.write("\r\x1b[K")
        print(f"{self.label}: done in {self.elapsed()}", file=sys.stderr)


def _add_params(parser: argparse.ArgumentParser, params_type: type) -> None:
    """Add one ``--option`` per field of an effect's parameter dataclass."""
    for field in dataclasses.fields(params_type):
        # Optional fields default to None; the only one so far is an int seed.
        value_type = int if field.default is None else type(field.default)
        parser.add_argument(
            f"--{field.name.replace('_', '-')}",
            type=value_type,
            default=field.default,
            help=field.metadata["help"],
        )


def _params[T](params_type: type[T], args: argparse.Namespace) -> T:
    names = [field.name for field in dataclasses.fields(params_type)]  # type: ignore[arg-type]
    return params_type(**{name: getattr(args, name) for name in names})


def _bloom(args: argparse.Namespace, progress: ProgressCallback) -> Any:
    return bloom.render(
        Reference.load(args.input),
        args.entropy.read_bytes(),
        _params(bloom.BloomParams, args),
        progress,
    )


def _colours(args: argparse.Namespace, progress: ProgressCallback) -> Any:
    return colours_natural.render(
        Reference.load(args.input),
        args.strokes.read_bytes(),
        _params(colours_natural.ColoursParams, args),
        progress,
    )


def _ebs(args: argparse.Namespace, progress: ProgressCallback) -> Any:
    return ebs.render(
        Reference.load(args.input), args.density, _params(ebs.EbsParams, args), progress
    )


def _quant(args: argparse.Namespace, progress: ProgressCallback) -> Any:
    return quant.render(Reference.load(args.input), _params(quant.QuantParams, args), progress)


def _regrain(args: argparse.Namespace, progress: ProgressCallback) -> Any:
    return regrain.render(
        Reference.load(args.input), _params(regrain.RegrainParams, args), progress
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="effekt", description="Generative image effects rendered with cairo."
    )
    commands = parser.add_subparsers(dest="effect", required=True, metavar="EFFECT")

    def command(name: str, module: Any, run: Any, params_type: type) -> argparse.ArgumentParser:
        sub = commands.add_parser(
            name,
            help=module.__doc__.splitlines()[0],
            description=module.__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        sub.set_defaults(run=run, params_type=params_type)
        return sub

    image_help = "reference image to read"
    output_help = "PNG file to write"

    sub = command("bloom", bloom, _bloom, bloom.BloomParams)
    sub.add_argument("entropy", type=Path, help="file whose bytes jitter each sample")
    sub.add_argument("input", type=Path, help=image_help)
    sub.add_argument("output", type=Path, help=output_help)

    sub = command("colours-natural", colours_natural, _colours, colours_natural.ColoursParams)
    sub.add_argument("strokes", type=Path, help="any file; each byte steers one stroke")
    sub.add_argument("input", type=Path, help=image_help)
    sub.add_argument("output", type=Path, help=output_help)

    sub = command("ebs", ebs, _ebs, ebs.EbsParams)
    sub.add_argument("input", type=Path, help=image_help)
    sub.add_argument("output", type=Path, help=output_help)
    sub.add_argument("density", type=int, help="number of swarm steps to draw")

    sub = command("quant", quant, _quant, quant.QuantParams)
    sub.add_argument("input", type=Path, help=image_help)
    sub.add_argument("output", type=Path, help=output_help)

    sub = command("regrain", regrain, _regrain, regrain.RegrainParams)
    sub.add_argument("input", type=Path, help=image_help)
    sub.add_argument("output", type=Path, help=output_help)

    for sub in commands.choices.values():
        _add_params(sub, sub.get_default("params_type"))

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    progress = Progress(args.effect)
    try:
        surface = args.run(args, progress)
        surface.write_to_png(str(args.output))
    except (OSError, ValueError) as error:
        print(f"effekt: error: {error}", file=sys.stderr)
        return 1
    progress.finish()
    print(f"Wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
