#!/usr/bin/env python3
"""Extract battle command icons from /workspace/Combat interface.png.

Outputs four 32x32 transparent PNGs:
  - fight_icon.png
  - act_icon.png
  - item_icon.png
  - mercy_icon.png
"""

import argparse
from pathlib import Path

from PIL import Image


DEFAULT_INPUT = Path("/workspace/Combat interface.png")
DEFAULT_OUTPUT_DIR = Path("/workspace")
OUT_SIZE = 32

# Crop boxes tuned to the current source image (1536x1024).
# Format: (left, top, right, bottom), right/bottom are exclusive.
SYMBOL_BOXES = {
    "fight": (133, 405, 321, 600),
    "act": (493, 403, 682, 603),
    "item": (873, 408, 1029, 600),
    "mercy": (1231, 428, 1394, 589),
}


def _black_to_alpha(img: Image.Image, threshold: int = 20) -> Image.Image:
    rgba = img.convert("RGBA")
    data = []
    for r, g, b, _ in rgba.getdata():
        if r <= threshold and g <= threshold and b <= threshold:
            data.append((0, 0, 0, 0))
        else:
            data.append((r, g, b, 255))
    rgba.putdata(data)
    return rgba


def _fit_to_canvas(img: Image.Image, size: int) -> Image.Image:
    bbox = img.getbbox()
    if not bbox:
        raise ValueError("empty symbol after black removal")
    trimmed = img.crop(bbox)
    tw, th = trimmed.size
    scale = min(float(size) / float(tw), float(size) / float(th))
    new_w = max(1, int(round(tw * scale)))
    new_h = max(1, int(round(th * scale)))
    resized = trimmed.resize((new_w, new_h), Image.NEAREST)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    x = (size - new_w) // 2
    y = (size - new_h) // 2
    canvas.paste(resized, (x, y), resized)
    return canvas


def extract_icons(input_path: Path, output_dir: Path) -> None:
    src = Image.open(input_path).convert("RGBA")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, box in SYMBOL_BOXES.items():
        cropped = src.crop(box)
        rgba = _black_to_alpha(cropped)
        icon = _fit_to_canvas(rgba, OUT_SIZE)
        out_path = output_dir / f"{name}_icon.png"
        icon.save(out_path)
        print(f"wrote: {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract battle command icons.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"input not found: {args.input}")

    extract_icons(args.input, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
