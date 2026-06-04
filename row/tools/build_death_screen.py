#!/usr/bin/env python3
"""Build a 320x240 deployable death screen from the source art."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageFilter


ROOT = Path("/workspace")
DEFAULT_INPUT = ROOT / "death.png"
DEFAULT_OUTPUT = ROOT / "death_320x240.png"
TARGET_SIZE = (320, 240)


def build_death_screen(src: Path, dst: Path) -> None:
    image = Image.open(src).convert("RGB")
    image = image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
    image = image.filter(ImageFilter.UnsharpMask(radius=1.2, percent=130, threshold=2))
    image.save(dst)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Source image path.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output PNG path.")
    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)
    build_death_screen(src, dst)
    print("wrote", dst)


if __name__ == "__main__":
    main()
