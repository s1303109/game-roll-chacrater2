#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("/workspace")
FONT_PATH = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
TEXT_FILL = (255, 255, 255, 255)
BLACK = (0, 0, 0)
PADDING_X = 0
PADDING_Y = 0
CANVAS_W = 214
CANVAS_H = 27
TC_FONT_INDICES = (3, 0, 1, 2, 4)
MAX_FONT_SIZE = 28
MIN_FONT_SIZE = 8

ASSETS = (
    ("wood_up_bed_dialog.png", "看起來是使用很久的床了"),
    ("wood_up_mirror_dialog.png", "這個鏡子雖然舊但擦得很乾淨"),
    ("wood_up_bookshelf_dialog.png", "幾本書好像特別的老舊"),
)


def load_font(size: int) -> ImageFont.FreeTypeFont:
    last_exc = None
    for index in TC_FONT_INDICES:
        try:
            return ImageFont.truetype(str(FONT_PATH), size, index=index)
        except OSError as exc:
            last_exc = exc
    raise SystemExit(f"failed to load font from {FONT_PATH}: {last_exc}")


def text_bbox(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont):
    return draw.textbbox((0, 0), text, font=font, stroke_width=0)


def fit_single_line_font(text: str, max_size: int = MAX_FONT_SIZE, min_size: int = MIN_FONT_SIZE) -> tuple[ImageFont.FreeTypeFont, tuple[int, int, int, int]]:
    scratch = Image.new("RGB", (CANVAS_W, CANVAS_H), BLACK)
    draw = ImageDraw.Draw(scratch)
    max_width = CANVAS_W - (PADDING_X * 2)
    max_height = CANVAS_H - (PADDING_Y * 2)
    selected_font = None
    selected_bbox = None
    for size in range(max_size, min_size - 1, -1):
        font = load_font(size)
        bbox = text_bbox(draw, text, font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        if width <= max_width and height <= max_height:
            return font, bbox
        selected_font = font
        selected_bbox = bbox
    return selected_font, selected_bbox


def render_dialogue_asset(filename: str, text: str) -> None:
    image = Image.new("RGB", (CANVAS_W, CANVAS_H), BLACK)
    draw = ImageDraw.Draw(image)
    font, bbox = fit_single_line_font(text, max_size=MAX_FONT_SIZE, min_size=MIN_FONT_SIZE)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = ((CANVAS_W - text_w) // 2) - bbox[0]
    y = ((CANVAS_H - text_h) // 2) - bbox[1]
    draw.text((x, y), text, font=font, fill=TEXT_FILL, stroke_width=0)

    image.save(ROOT / filename)


def main() -> None:
    for filename, text in ASSETS:
        render_dialogue_asset(filename, text)
    print("generated", len(ASSETS), "assets")


if __name__ == "__main__":
    main()
