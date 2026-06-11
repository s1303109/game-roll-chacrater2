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
    "觀察": 46,
    "忍耐": 46,
    "靠近": 46,
    "冷靜": 46,
}

OPENING_LINES = (
    "地面的裂縫亮起火光。",
    "熔岩像呼吸一樣翻動。",
    "Lava Brute：你的靈魂，也會燃燒嗎？",
    "Lava Brute：弱小會被火吞掉。",
    "Lava Brute：證明你不會被火支配。",
)
OBSERVE_LINES = (
    "你觀察牠身上的裂痕。",
    "火光像不穩定的心跳。",
    "Lava Brute：火焰只會吞掉軟弱。",
)
ENDURE_LINES = (
    "你站在原地，沒有反擊。",
    "熱浪逼近你的臉。",
    "Lava Brute：為什麼不逃？",
)
APPROACH_LINES = (
    "你慢慢靠近牠。",
    "牠的爪子停在半空中。",
    "Lava Brute：別靠近。",
    "Lava Brute：我控制不了這些火。",
)
CALM_LINES = (
    "你說，火焰不一定只能破壞。",
    "燃燒也可以是照亮。",
    "Lava Brute：照亮……不是燒毀？",
)
MERCY_LINES = (
    "Lava Brute：火勢安靜下來了。",
    "Lava Brute：你的靈魂沒有燃燒。",
    "Lava Brute：熔岩封鎖……解除。",
    "Lava Brute：走吧，在火失控以前。",
)
ACT_OPTIONS = (
    ("map11_lavabrute_act_observe.png", "觀察"),
    ("map11_lavabrute_act_endure.png", "忍耐"),
    ("map11_lavabrute_act_approach.png", "靠近"),
    ("map11_lavabrute_act_calm.png", "冷靜"),
)


def numbered_assets(prefix: str, lines: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    return tuple(("%s_%02d.png" % (prefix, index + 1), text) for index, text in enumerate(lines))


DIALOGUE_ASSETS = (
    numbered_assets("map11_lavabrute_observe", OBSERVE_LINES)
    + numbered_assets("map11_lavabrute_endure", ENDURE_LINES)
    + numbered_assets("map11_lavabrute_approach", APPROACH_LINES)
    + numbered_assets("map11_lavabrute_calm", CALM_LINES)
    + numbered_assets("map11_lavabrute_mercy", MERCY_LINES)
)
OPENING_ASSETS = numbered_assets("map11_lavabrute_opening", OPENING_LINES)


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
