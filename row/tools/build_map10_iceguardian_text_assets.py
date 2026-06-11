#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("/workspace")
FONT_PATH = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
TEXT_FILL = (255, 255, 255, 255)
BLACK = (0, 0, 0)
TRANSPARENT = (0, 0, 0, 0)
TC_FONT_INDICES = (3, 0, 1, 2, 4)

DIALOGUE_FONT_SIZE = 19
DIALOGUE_LINE_SPACING = 6
DIALOGUE_CANVAS_W = 200
DIALOGUE_CANVAS_H = 72
DIALOGUE_PADDING_X = 6
DIALOGUE_PADDING_Y = 4
OPENING_FONT_SIZE = 18
OPENING_CANVAS_W = 156

ACT_CANVAS_MIN_W = 46
ACT_CANVAS_H = 18
ACT_TEXT_BASELINE_Y = 14
ACT_LEFT_PAD = 5
ACT_RIGHT_PAD = 3
ACT_MAX_FONT_SIZE = 19
ACT_MIN_FONT_SIZE = 10
ACT_TEXT_MAX_H = ACT_CANVAS_H - 2
ACT_FIXED_WIDTHS = {
    "觸碰冰晶": 64,
}

OPENING_LINES = (
    "寒氣開始聚集。",
    "藍晶發出微光。",
    "Ice Guardian：禁止接近聖座。",
    "Ice Guardian：前進者，會被冰晶吞沒。",
    "Ice Guardian：所以，道路必須停止。",
)
OBSERVE_LINES = (
    "你觀察牠身上的裂痕。",
    "牠像是由破碎誓言拼成的。",
    "Ice Guardian：你看見了裂縫。",
)
LISTEN_LINES = (
    "你聽見冰晶深處的回音。",
    "那不像威脅。",
    "Ice Guardian：你……聽見了？",
)
TOUCH_CRYSTAL_LINES = (
    "你伸手碰向冰晶核心。",
    "冰冷刺進指尖。",
    "Ice Guardian：不要觸碰核心。",
    "你沒有放手。",
)
TELL_LINES = (
    "你說，破碎不代表結束。",
    "寒冷也可以是記憶。",
    "Ice Guardian：判斷正在修正。",
)
MERCY_LINES = (
    "Ice Guardian：冰晶沒有碎裂。",
    "Ice Guardian：前進者，不一定會被凍結。",
    "Ice Guardian：聖座封鎖……解除。",
    "Ice Guardian：帶著記憶，繼續前進。",
)
ACT_OPTIONS = (
    ("map10_iceguardian_act_observe.png", "觀察"),
    ("map10_iceguardian_act_listen.png", "聆聽"),
    ("map10_iceguardian_act_touch_crystal.png", "觸碰冰晶"),
    ("map10_iceguardian_act_tell.png", "訴說"),
)


def numbered_assets(prefix: str, lines: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    return tuple(("%s_%02d.png" % (prefix, index + 1), text) for index, text in enumerate(lines))


DIALOGUE_ASSETS = (
    numbered_assets("map10_iceguardian_observe", OBSERVE_LINES)
    + numbered_assets("map10_iceguardian_listen", LISTEN_LINES)
    + numbered_assets("map10_iceguardian_touch_crystal", TOUCH_CRYSTAL_LINES)
    + numbered_assets("map10_iceguardian_tell", TELL_LINES)
    + numbered_assets("map10_iceguardian_mercy", MERCY_LINES)
)
OPENING_ASSETS = numbered_assets("map10_iceguardian_opening", OPENING_LINES)


def load_font(size: int) -> ImageFont.FreeTypeFont:
    last_exc = None
    for index in TC_FONT_INDICES:
        try:
            return ImageFont.truetype(str(FONT_PATH), size, index=index)
        except OSError as exc:
            last_exc = exc
    raise SystemExit("failed to load font from %s: %s" % (FONT_PATH, last_exc))


def text_bbox(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont):
    return draw.textbbox((0, 0), text, font=font, stroke_width=0)


def wrap_cjk_lines(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    scratch = Image.new("RGBA", (1024, 256), TRANSPARENT)
    draw = ImageDraw.Draw(scratch)
    lines = []
    current = ""
    for char in text:
        trial = current + char
        bbox = text_bbox(draw, trial, font)
        width = bbox[2] - bbox[0]
        if current and width > max_width:
            lines.append(current)
            current = char
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def render_dialogue_asset(filename: str, text: str, font: ImageFont.FreeTypeFont, canvas_w: int) -> None:
    content_w = canvas_w - (DIALOGUE_PADDING_X * 2)
    image = Image.new("RGB", (canvas_w, DIALOGUE_CANVAS_H), BLACK)
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
    if y < DIALOGUE_PADDING_Y:
        y = DIALOGUE_PADDING_Y
    for line, bbox in line_metrics:
        x = DIALOGUE_PADDING_X - bbox[0]
        draw.text((x, y - bbox[1]), line, font=font, fill=TEXT_FILL, stroke_width=0)
        y += (bbox[3] - bbox[1]) + DIALOGUE_LINE_SPACING
    image.save(ROOT / filename)


def pick_act_font(text: str, canvas_w: int | None = None) -> ImageFont.FreeTypeFont:
    scratch = Image.new("RGBA", (256, 64), TRANSPARENT)
    draw = ImageDraw.Draw(scratch)
    max_text_w = None
    if canvas_w is not None:
        max_text_w = canvas_w - ACT_LEFT_PAD - ACT_RIGHT_PAD
    for size in range(ACT_MAX_FONT_SIZE, ACT_MIN_FONT_SIZE - 1, -1):
        font = load_font(size)
        bbox = text_bbox(draw, text, font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        if height <= ACT_TEXT_MAX_H and (max_text_w is None or width <= max_text_w):
            return font
    return load_font(ACT_MIN_FONT_SIZE)


def act_canvas_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    fixed_w = ACT_FIXED_WIDTHS.get(text)
    if fixed_w:
        return fixed_w
    bbox = text_bbox(draw, text, font)
    width = (bbox[2] - bbox[0]) + ACT_LEFT_PAD + ACT_RIGHT_PAD
    if width < ACT_CANVAS_MIN_W:
        width = ACT_CANVAS_MIN_W
    return width


def render_act_asset(filename: str, text: str) -> None:
    fixed_w = ACT_FIXED_WIDTHS.get(text)
    font = pick_act_font(text, fixed_w)
    scratch = Image.new("RGBA", (256, 64), TRANSPARENT)
    scratch_draw = ImageDraw.Draw(scratch)
    canvas_w = act_canvas_width(scratch_draw, text, font)
    image = Image.new("RGBA", (canvas_w, ACT_CANVAS_H), TRANSPARENT)
    draw = ImageDraw.Draw(image)
    bbox = text_bbox(draw, text, font)
    x = ACT_LEFT_PAD - bbox[0]
    y = ACT_TEXT_BASELINE_Y - bbox[3]
    draw.text((x, y), text, font=font, fill=TEXT_FILL, stroke_width=0)
    image.save(ROOT / filename)


def main() -> None:
    dialogue_font = load_font(DIALOGUE_FONT_SIZE)
    opening_font = load_font(OPENING_FONT_SIZE)
    for filename, text in OPENING_ASSETS:
        render_dialogue_asset(filename, text, opening_font, OPENING_CANVAS_W)
    for filename, text in DIALOGUE_ASSETS:
        render_dialogue_asset(filename, text, dialogue_font, DIALOGUE_CANVAS_W)
    for filename, text in ACT_OPTIONS:
        render_act_asset(filename, text)
    total = len(OPENING_ASSETS) + len(DIALOGUE_ASSETS) + len(ACT_OPTIONS)
    print("generated", total, "assets")


if __name__ == "__main__":
    main()
