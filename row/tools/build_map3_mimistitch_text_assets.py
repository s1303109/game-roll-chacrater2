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

DEFAULT_DIALOGUE_FONT_SIZE = 19
DEFAULT_DIALOGUE_LINE_SPACING = 6
OPENING_FONT_SIZE = 21
OPENING_LINE_SPACING = 6
ACT_SEQUENCE_FONT_SIZE = 17
ACT_SEQUENCE_LINE_SPACING = 5
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
    "喵……？",
    "你喜歡貓嗎？",
    "你會喜歡……壞掉的貓嗎？",
)
ACT_OPTIONS = (
    "稱讚",
    "整理",
    "接納",
)
PRAISE_LINES = (
    "你稱讚 Mimi-Stitch 的耳朵很特別。",
    "Mimi-Stitch 假裝不在意，但尾巴輕輕晃了一下。",
    "特別……不是奇怪嗎？",
)
TIDY_LINES = (
    "你假裝幫 Mimi-Stitch 整理縫線。",
    "雖然你沒有真的修好什麼，但牠看起來安心了一點。",
)
ACCEPT_LINES = (
    "你告訴 Mimi-Stitch，不完整也沒有關係。",
    "Mimi-Stitch 低下頭，縫線旁的小鈴鐺輕輕響了一聲。",
    "那我……可以只當我自己嗎？",
)
MERCY_LINES = (
    "我不會再假裝成別人了。",
    "如果你又看到掉在地上的玩具……",
    "可以不要踩到它們嗎？",
)

DIALOGUE_ASSETS = (
    ("map3_mimistitch_opening_01.png", OPENING_LINES[0], "opening"),
    ("map3_mimistitch_opening_02.png", OPENING_LINES[1], "opening"),
    ("map3_mimistitch_opening_03.png", OPENING_LINES[2], "opening"),
    ("map3_mimistitch_praise_01.png", PRAISE_LINES[0], "act_sequence"),
    ("map3_mimistitch_praise_02.png", PRAISE_LINES[1], "act_sequence"),
    ("map3_mimistitch_praise_03.png", PRAISE_LINES[2], "act_sequence"),
    ("map3_mimistitch_tidy_01.png", TIDY_LINES[0], "act_sequence"),
    ("map3_mimistitch_tidy_02.png", TIDY_LINES[1], "act_sequence"),
    ("map3_mimistitch_accept_01.png", ACCEPT_LINES[0], "act_sequence"),
    ("map3_mimistitch_accept_02.png", ACCEPT_LINES[1], "act_sequence"),
    ("map3_mimistitch_accept_03.png", ACCEPT_LINES[2], "act_sequence"),
    ("map3_mimistitch_mercy_01.png", MERCY_LINES[0], "default"),
    ("map3_mimistitch_mercy_02.png", MERCY_LINES[1], "default"),
    ("map3_mimistitch_mercy_03.png", MERCY_LINES[2], "default"),
)

ACT_ASSETS = (
    ("map3_mimistitch_act_praise.png", ACT_OPTIONS[0]),
    ("map3_mimistitch_act_tidy.png", ACT_OPTIONS[1]),
    ("map3_mimistitch_act_accept.png", ACT_OPTIONS[2]),
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


def render_dialogue_asset(
    filename: str,
    text: str,
    font: ImageFont.FreeTypeFont,
    line_spacing: int,
) -> None:
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
        block_h += line_spacing * (len(line_metrics) - 1)
    y = (DIALOGUE_CANVAS_H - block_h) // 2
    if y < PADDING_Y:
        y = PADDING_Y
    for line, bbox in line_metrics:
        x = PADDING_X - bbox[0]
        draw.text((x, y - bbox[1]), line, font=font, fill=TEXT_FILL, stroke_width=0)
        y += (bbox[3] - bbox[1]) + line_spacing
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
    default_font = load_font(DEFAULT_DIALOGUE_FONT_SIZE)
    opening_font = load_font(OPENING_FONT_SIZE)
    act_sequence_font = load_font(ACT_SEQUENCE_FONT_SIZE)
    for filename, text, kind in DIALOGUE_ASSETS:
        if kind == "opening":
            render_dialogue_asset(filename, text, opening_font, OPENING_LINE_SPACING)
        elif kind == "act_sequence":
            render_dialogue_asset(filename, text, act_sequence_font, ACT_SEQUENCE_LINE_SPACING)
        else:
            render_dialogue_asset(filename, text, default_font, DEFAULT_DIALOGUE_LINE_SPACING)
    for filename, text in ACT_ASSETS:
        render_act_asset(filename, text)
    print("generated", len(DIALOGUE_ASSETS) + len(ACT_ASSETS), "assets")


if __name__ == "__main__":
    main()
