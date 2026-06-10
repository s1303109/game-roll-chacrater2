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

OPENING_LINES = (
    "停止前進。",
    "孩子，不該進入更深的地方。",
    "判定結果：禁止通行。",
    "弱小的靈魂，會被遺跡吞沒。",
    "離開，或被阻止。",
    "情緒紀錄仍在。",
    "孤單。破碎。悲傷。錯誤。",
    "所有前進者，最後都留下痛苦。",
    "所有試圖深入的人，都帶著傷痕離開。",
    "所以，我會封住道路。",
)
OBSERVE_LINES = (
    "觀察無意義。",
    "理解不會改變危險。",
)
REMEMBER_LINES = (
    "你想起了之前遇見的怪物。",
    "你想起 Gloombell 害怕被丟下。",
    "你想起 Mimi-Stitch 害怕自己不完整。",
    "你想起 Mushmuse 聽見別人的悲傷。",
    "你想起 Cyclobot 只是被舊指令困住。",
    "Crystal Golem 的胸口晶核亮了一下。",
    "Crystal Golem：記憶確認。",
    "Crystal Golem：你……沒有破壞它們？",
)
TELL_LINES = (
    "我知道前面可能很危險。",
    "害怕受傷而停下，就甚麼都不會改變。",
    "Crystal Golem 沉默了。",
    "Crystal Golem：前進，代表失去。",
    "Crystal Golem：停下，代表安全。",
    "Crystal Golem：此判斷……曾經正確。",
)
TOUCH_CORE_LINES = (
    "你靠近 Crystal Golem，伸手碰向藍色晶核。",
    "晶核很冷。",
    "深處微微震動，像被壓住的心跳。",
    "Crystal Golem：不要接觸核心。",
    "Crystal Golem：那裡保存著錯誤、恐懼與失敗。",
    "你沒有退後。",
    "你只是靜靜站著。",
    "Crystal Golem：為什麼……不害怕？",
)
MERCY_LINES = (
    "Crystal Golem：……你選擇停止攻擊。",
    "Crystal Golem：修正判斷，你並非破壞者。",
    "Crystal Golem：弱小，也能選擇理解。",
    "Crystal Golem：道路封鎖……解除。",
    "Crystal Golem：孩子，你可以繼續前進。",
)
ACT_OPTIONS = (
    ("map6_crystalgolem_act_observe.png", "觀察"),
    ("map6_crystalgolem_act_remember.png", "回想"),
    ("map6_crystalgolem_act_tell.png", "訴說"),
    ("map6_crystalgolem_act_touch_core.png", "觸碰晶核"),
)


def numbered_assets(prefix: str, lines: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    return tuple(("%s_%02d.png" % (prefix, index + 1), text) for index, text in enumerate(lines))


DIALOGUE_ASSETS = (
    numbered_assets("map6_crystalgolem_observe", OBSERVE_LINES)
    + numbered_assets("map6_crystalgolem_remember", REMEMBER_LINES)
    + numbered_assets("map6_crystalgolem_tell", TELL_LINES)
    + numbered_assets("map6_crystalgolem_touch_core", TOUCH_CORE_LINES)
    + numbered_assets("map6_crystalgolem_mercy", MERCY_LINES)
)
OPENING_ASSETS = numbered_assets("map6_crystalgolem_opening", OPENING_LINES)


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


def pick_act_font(text: str) -> ImageFont.FreeTypeFont:
    scratch = Image.new("RGBA", (256, 64), TRANSPARENT)
    draw = ImageDraw.Draw(scratch)
    for size in range(ACT_MAX_FONT_SIZE, ACT_MIN_FONT_SIZE - 1, -1):
        font = load_font(size)
        bbox = text_bbox(draw, text, font)
        height = bbox[3] - bbox[1]
        if height <= ACT_TEXT_MAX_H:
            return font
    return load_font(ACT_MIN_FONT_SIZE)


def act_canvas_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    bbox = text_bbox(draw, text, font)
    width = (bbox[2] - bbox[0]) + ACT_LEFT_PAD + ACT_RIGHT_PAD
    if width < ACT_CANVAS_MIN_W:
        width = ACT_CANVAS_MIN_W
    return width


def render_act_asset(filename: str, text: str) -> None:
    font = pick_act_font(text)
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
