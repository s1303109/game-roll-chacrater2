#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("/workspace")
FONT_PATH = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
DEFAULT_CANVAS_W = 214
CANVAS_H = 27
BG_FILL = (0, 0, 0)
TEXT_FONT_SIZE = 20
TEXT_TARGET_H = 21
TEXT_PAD_X = 2
TEXT_PAD_Y = 3
TC_FONT_INDICES = (3, 0, 1, 2, 4)

ASSETS = (
    ("map5_map6_door_locked_dialog.png", "沒有鑰匙，無法打開"),
)


def load_font(size: int) -> ImageFont.FreeTypeFont:
    last_exc = None
    for index in TC_FONT_INDICES:
        try:
            return ImageFont.truetype(str(FONT_PATH), size, index=index)
        except OSError as exc:
            last_exc = exc
    raise SystemExit(f"failed to load font from {FONT_PATH}: {last_exc}")


def char_metrics(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont):
    metrics = []
    for char in text:
        bbox = draw.textbbox((0, 0), char, font=font, anchor="ls", stroke_width=0)
        metrics.append((char, bbox, bbox[2] - bbox[0], bbox[3] - bbox[1]))
    return metrics


def tracking_for_width(metrics, max_width: int, target_h: int) -> int:
    if len(metrics) <= 1:
        return 0
    total_width = sum(item[2] for item in metrics)
    source_h = max(item[3] for item in metrics)
    for tracking in (0, -1, -2, -3, -4):
        width = total_width + (tracking * (len(metrics) - 1))
        scaled_width = (width * target_h + source_h - 1) // source_h
        if scaled_width <= max_width:
            return tracking
    return -4


def required_canvas_width(metrics, target_h: int, pad_x: int) -> int:
    if not metrics:
        return DEFAULT_CANVAS_W
    source_h = max(item[3] for item in metrics)
    tracking = tracking_for_width(metrics, 4096, target_h)
    total_width = sum(item[2] for item in metrics) + (tracking * (len(metrics) - 1))
    scaled_width = (total_width * target_h + source_h - 1) // source_h
    return max(DEFAULT_CANVAS_W, scaled_width + (pad_x * 2))


def render_dialogue_asset(filename: str, text: str, font: ImageFont.FreeTypeFont) -> None:
    temp = Image.new("L", (DEFAULT_CANVAS_W * 3, CANVAS_H * 4), 0)
    draw = ImageDraw.Draw(temp)
    metrics = char_metrics(draw, text, font)
    canvas_w = required_canvas_width(metrics, TEXT_TARGET_H, TEXT_PAD_X)
    tracking = tracking_for_width(metrics, canvas_w - (TEXT_PAD_X * 2), TEXT_TARGET_H)
    total_width = sum(item[2] for item in metrics) + (tracking * (len(metrics) - 1))
    top = min(item[1][1] for item in metrics)
    bottom = max(item[1][3] for item in metrics)
    text_height = bottom - top
    x = (temp.width - total_width) // 2
    baseline_y = (temp.height - text_height) // 2 - top

    cursor_x = x
    for char, _, width, _ in metrics:
        draw.text((cursor_x, baseline_y), char, font=font, fill=255, anchor="ls", stroke_width=0)
        cursor_x += width + tracking

    cropped = temp.crop(temp.getbbox())
    scaled_w = max(1, (cropped.width * TEXT_TARGET_H + cropped.height - 1) // cropped.height)
    scaled = cropped.resize((scaled_w, TEXT_TARGET_H), Image.BICUBIC)

    image = Image.new("RGB", (canvas_w, CANVAS_H), BG_FILL)
    paste_x = (canvas_w - scaled.width) // 2
    paste_y = max(0, (CANVAS_H - TEXT_TARGET_H) // 2 - TEXT_PAD_Y + 1)
    image.paste(Image.merge("RGB", (scaled, scaled, scaled)), (paste_x, paste_y), scaled)
    image.save(ROOT / filename)


def main() -> None:
    font = load_font(TEXT_FONT_SIZE)
    for filename, text in ASSETS:
        render_dialogue_asset(filename, text, font)
    print("generated", len(ASSETS), "assets")


if __name__ == "__main__":
    main()
