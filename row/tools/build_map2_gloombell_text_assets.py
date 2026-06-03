#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("/workspace")
FONT_PATH = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
FONT_SIZE = 16
LINE_SPACING = 4
OPENING_FONT_SIZE = 18
OPENING_LINE_SPACING = 5
TEXT_FILL = (255, 255, 255, 255)
BLACK = (0, 0, 0)
TRANSPARENT = (0, 0, 0, 0)
PADDING_X = 6
PADDING_Y = 4
TC_FONT_INDICES = (3, 0, 1, 2, 4)

OPENING_LINES = (
    "你……看得見我嗎？",
    "不要走太快。",
    "這裡已經很久沒有人停下來了。",
)
ACT_OPTIONS = (
    "查看",
    "呼喚",
    "等待",
)
LOOK_LINES = (
    "你仔細看著幽鈴燈的光。",
    "它不是在威脅你，而是在發抖。",
)
CALL_LINES = (
    "你輕聲呼喚幽鈴燈。",
    "幽鈴燈的光稍微穩定了一點。",
    "你真的……不是要丟下我嗎？",
)
WAIT_LINES = (
    "你停下腳步，陪著幽鈴燈待了一會。",
    "幽鈴燈的光變得柔和。",
    "原來……有人停下來的時候，是這種感覺。",
)
MERCY_LINES = (
    "謝謝你……",
    "前面的路很暗，但你應該不會害怕了。",
    "因為你願意停下來看見別人。",
)

DIALOGUE_ASSETS = (
    ("map2_gloombell_opening_01.png", OPENING_LINES[0], "opening"),
    ("map2_gloombell_opening_02.png", OPENING_LINES[1], "opening"),
    ("map2_gloombell_opening_03.png", OPENING_LINES[2], "opening"),
    ("map2_gloombell_look_01.png", LOOK_LINES[0], "normal"),
    ("map2_gloombell_look_02.png", LOOK_LINES[1], "normal"),
    ("map2_gloombell_call_01.png", CALL_LINES[0], "normal"),
    ("map2_gloombell_call_02.png", CALL_LINES[1], "normal"),
    ("map2_gloombell_call_03.png", CALL_LINES[2], "normal"),
    ("map2_gloombell_wait_01.png", WAIT_LINES[0], "normal"),
    ("map2_gloombell_wait_02.png", WAIT_LINES[1], "normal"),
    ("map2_gloombell_wait_03.png", WAIT_LINES[2], "normal"),
    ("map2_gloombell_mercy_01.png", MERCY_LINES[0], "normal"),
    ("map2_gloombell_mercy_02.png", MERCY_LINES[1], "normal"),
    ("map2_gloombell_mercy_03.png", MERCY_LINES[2], "normal"),
)
ACT_ASSETS = (
    ("map2_gloombell_act_watch.png", ACT_OPTIONS[0]),
    ("map2_gloombell_act_call.png", ACT_OPTIONS[1]),
    ("map2_gloombell_act_wait.png", ACT_OPTIONS[2]),
)
ACT_CANVAS_W = 46
ACT_CANVAS_H = 18
ACT_TEXT_BASELINE_Y = 14
ACT_LEFT_PAD = 5


def load_font() -> ImageFont.FreeTypeFont:
    last_exc = None
    for index in TC_FONT_INDICES:
        try:
            return ImageFont.truetype(str(FONT_PATH), FONT_SIZE, index=index)
        except OSError as exc:
            last_exc = exc
    raise SystemExit(f"failed to load font from {FONT_PATH}: {last_exc}")


def load_font_with_size(size: int) -> ImageFont.FreeTypeFont:
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


def render_dialogue_asset(filename: str, text: str, font: ImageFont.FreeTypeFont, line_spacing: int) -> None:
    canvas_w = 200
    canvas_h = 72
    content_w = canvas_w - (PADDING_X * 2)
    image = Image.new("RGB", (canvas_w, canvas_h), BLACK)
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
        block_h += line_spacing * (len(line_metrics) - 1)
    y = (canvas_h - block_h) // 2
    if y < PADDING_Y:
        y = PADDING_Y
    for line, bbox in line_metrics:
        x = PADDING_X - bbox[0]
        draw.text((x, y - bbox[1]), line, font=font, fill=TEXT_FILL, stroke_width=0)
        y += (bbox[3] - bbox[1]) + line_spacing
    image.save(ROOT / filename)


def render_act_asset(filename: str, text: str, font: ImageFont.FreeTypeFont) -> None:
    image = Image.new("RGBA", (ACT_CANVAS_W, ACT_CANVAS_H), TRANSPARENT)
    draw = ImageDraw.Draw(image)
    bbox = text_bbox(draw, text, font)
    x = ACT_LEFT_PAD - bbox[0]
    y = ACT_TEXT_BASELINE_Y - bbox[3]
    draw.text((x, y), text, font=font, fill=TEXT_FILL, stroke_width=0)
    image.save(ROOT / filename)


def main() -> None:
    font = load_font()
    opening_font = load_font_with_size(OPENING_FONT_SIZE)
    for filename, text, kind in DIALOGUE_ASSETS:
        if kind == "opening":
            render_dialogue_asset(filename, text, opening_font, OPENING_LINE_SPACING)
        else:
            render_dialogue_asset(filename, text, font, LINE_SPACING)
    for filename, text in ACT_ASSETS:
        render_act_asset(filename, text, font)
    print("generated", len(DIALOGUE_ASSETS) + len(ACT_ASSETS), "assets")


if __name__ == "__main__":
    main()
