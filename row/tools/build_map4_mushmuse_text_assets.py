#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("/workspace")
FONT_PATH = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
TEXT_FILL = (255, 255, 255, 255)
BLACK = (0, 0, 0)
TRANSPARENT = (0, 0, 0, 0)
PADDING_X = 6
PADDING_Y = 4
TC_FONT_INDICES = (3, 0, 1, 2, 4)

DIALOGUE_FONT_SIZE = 19
DIALOGUE_LINE_SPACING = 6
DIALOGUE_CANVAS_W = 200
DIALOGUE_CANVAS_H = 72

ACT_CANVAS_W = 46
ACT_CANVAS_H = 18
ACT_TEXT_BASELINE_Y = 14
ACT_LEFT_PAD = 5
ACT_MAX_FONT_SIZE = 19
ACT_MIN_FONT_SIZE = 10
ACT_TEXT_MAX_W = ACT_CANVAS_W - ACT_LEFT_PAD - 1
ACT_TEXT_MAX_H = ACT_CANVAS_H - 2

OPENING_LINES = (
    "你走路的聲音……好輕。",
    "可是你的心跳，好吵。",
    "你是不是……在害怕？",
)
ACT_OPTIONS = (
    "哼歌",
    "呼吸",
    "分享",
)
HUM_LINES = (
    "這不是悲傷……這是歌嗎？",
)
BREATH_LINES = (
    "你的心變安靜了。",
)
SHARE_LINES = (
    "原來情緒不是食物。",
    "是要被聽見的東西。",
)
MERCY_LINES = (
    "你的聲音，我會記得。",
    "但是我不會再把它困住了。",
    "去吧，孩子。你的心還要往前走。",
)

DIALOGUE_ASSETS = (
    ("map4_mushmuse_opening_01.png", OPENING_LINES[0]),
    ("map4_mushmuse_opening_02.png", OPENING_LINES[1]),
    ("map4_mushmuse_opening_03.png", OPENING_LINES[2]),
    ("map4_mushmuse_hum_01.png", HUM_LINES[0]),
    ("map4_mushmuse_breath_01.png", BREATH_LINES[0]),
    ("map4_mushmuse_share_01.png", SHARE_LINES[0]),
    ("map4_mushmuse_share_02.png", SHARE_LINES[1]),
    ("map4_mushmuse_mercy_01.png", MERCY_LINES[0]),
    ("map4_mushmuse_mercy_02.png", MERCY_LINES[1]),
    ("map4_mushmuse_mercy_03.png", MERCY_LINES[2]),
)

ACT_ASSETS = (
    ("map4_mushmuse_act_hum.png", ACT_OPTIONS[0]),
    ("map4_mushmuse_act_breath.png", ACT_OPTIONS[1]),
    ("map4_mushmuse_act_share.png", ACT_OPTIONS[2]),
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


def wrap_cjk_lines(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    scratch = Image.new("RGBA", (512, 128), TRANSPARENT)
    draw = ImageDraw.Draw(scratch)
    lines = []
    current = ""
    for ch in text:
        trial = current + ch
        bbox = text_bbox(draw, trial, font)
        width = bbox[2] - bbox[0]
        if current and width > max_width:
            lines.append(current)
            current = ch
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def render_dialogue_asset(filename: str, text: str, font: ImageFont.FreeTypeFont) -> None:
    content_w = DIALOGUE_CANVAS_W - (PADDING_X * 2)
    image = Image.new("RGB", (DIALOGUE_CANVAS_W, DIALOGUE_CANVAS_H), BLACK)
    draw = ImageDraw.Draw(image)
    lines = wrap_cjk_lines(text, font, content_w)
    line_metrics = []
    for line in lines:
        bbox = text_bbox(draw, line, font)
        line_metrics.append((line, bbox))
    block_h = 0
    for _, bbox in line_metrics:
        block_h += bbox[3] - bbox[1]
    if line_metrics:
        block_h += DIALOGUE_LINE_SPACING * (len(line_metrics) - 1)
    y = (DIALOGUE_CANVAS_H - block_h) // 2
    if y < PADDING_Y:
        y = PADDING_Y
    for line, bbox in line_metrics:
        x = PADDING_X - bbox[0]
        draw.text((x, y - bbox[1]), line, font=font, fill=TEXT_FILL, stroke_width=0)
        y += (bbox[3] - bbox[1]) + DIALOGUE_LINE_SPACING
    image.save(ROOT / filename)


def pick_act_font(text: str) -> ImageFont.FreeTypeFont:
    scratch = Image.new("RGBA", (ACT_CANVAS_W, ACT_CANVAS_H), TRANSPARENT)
    draw = ImageDraw.Draw(scratch)
    for size in range(ACT_MAX_FONT_SIZE, ACT_MIN_FONT_SIZE - 1, -1):
        font = load_font(size)
        bbox = text_bbox(draw, text, font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        if width <= ACT_TEXT_MAX_W and height <= ACT_TEXT_MAX_H:
            return font
    return load_font(ACT_MIN_FONT_SIZE)


def render_act_asset(filename: str, text: str) -> None:
    font = pick_act_font(text)
    image = Image.new("RGBA", (ACT_CANVAS_W, ACT_CANVAS_H), TRANSPARENT)
    draw = ImageDraw.Draw(image)
    bbox = text_bbox(draw, text, font)
    x = ACT_LEFT_PAD - bbox[0]
    y = ACT_TEXT_BASELINE_Y - bbox[3]
    draw.text((x, y), text, font=font, fill=TEXT_FILL, stroke_width=0)
    image.save(ROOT / filename)


def main() -> None:
    dialogue_font = load_font(DIALOGUE_FONT_SIZE)
    for filename, text in DIALOGUE_ASSETS:
        render_dialogue_asset(filename, text, dialogue_font)
    for filename, text in ACT_ASSETS:
        render_act_asset(filename, text)
    print("generated", len(DIALOGUE_ASSETS) + len(ACT_ASSETS), "assets")


if __name__ == "__main__":
    main()
