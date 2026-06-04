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
    "掃描完成。",
    "偵測到未知孩童。",
    "指令：阻止進入。",
)
ACT_OPTIONS = (
    "揮手",
    "解釋",
    "重置",
)
WAVE_LINES = (
    "偵測到友善動作。",
    "威脅等級……無法判定。",
)
EXPLAIN_LINES = (
    "迷路的孩子……",
    "資料分類不存在",
)
RESET_LINES = (
    "偵測到管理人權限。",
    "敵對指令暫停。",
)
MERCY_LINES = (
    "進入狀態已更新。",
    "孩童：非入侵者。",
    "請安全通行。",
)

DIALOGUE_ASSETS = (
    ("map5_cyclobot_opening_01.png", OPENING_LINES[0]),
    ("map5_cyclobot_opening_02.png", OPENING_LINES[1]),
    ("map5_cyclobot_opening_03.png", OPENING_LINES[2]),
    ("map5_cyclobot_wave_01.png", WAVE_LINES[0]),
    ("map5_cyclobot_wave_02.png", WAVE_LINES[1]),
    ("map5_cyclobot_explain_01.png", EXPLAIN_LINES[0]),
    ("map5_cyclobot_explain_02.png", EXPLAIN_LINES[1]),
    ("map5_cyclobot_reset_01.png", RESET_LINES[0]),
    ("map5_cyclobot_reset_02.png", RESET_LINES[1]),
    ("map5_cyclobot_mercy_01.png", MERCY_LINES[0]),
    ("map5_cyclobot_mercy_02.png", MERCY_LINES[1]),
    ("map5_cyclobot_mercy_03.png", MERCY_LINES[2]),
)

ACT_ASSETS = (
    ("map5_cyclobot_act_wave.png", ACT_OPTIONS[0]),
    ("map5_cyclobot_act_explain.png", ACT_OPTIONS[1]),
    ("map5_cyclobot_act_reset.png", ACT_OPTIONS[2]),
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
