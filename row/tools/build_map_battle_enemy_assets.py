#!/usr/bin/env python3
"""Build processed 96x96 battle enemy sprites for map2-map5."""

from collections import deque
from pathlib import Path

from PIL import Image


CANVAS_SIZE = 96
CONTENT_X = 21
CONTENT_Y = 6
CONTENT_W = 55
CONTENT_H = 83
BG_DARK_THRESHOLD = 12
ROOT = Path("/workspace")

SPECS = (
    ("map2 enemy.png", "map2_enemy_anim_96.png"),
    ("map3 enemy.png", "map3_enemy_anim_96.png"),
    ("map4 enemy.png", "map4_enemy_anim_96.png"),
    ("map5 enemy.png", "map5_enemy_anim_96.png"),
)


def _is_bg(pixel):
    r, g, b, _ = pixel
    return r <= BG_DARK_THRESHOLD and g <= BG_DARK_THRESHOLD and b <= BG_DARK_THRESHOLD


def _subject_bbox(src):
    rgba = src.convert("RGBA")
    w, h = rgba.size
    seen = [[False] * w for _ in range(h)]
    queue = deque()

    for x in range(w):
        for y in (0, h - 1):
            if seen[y][x]:
                continue
            if _is_bg(rgba.getpixel((x, y))):
                seen[y][x] = True
                queue.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if seen[y][x]:
                continue
            if _is_bg(rgba.getpixel((x, y))):
                seen[y][x] = True
                queue.append((x, y))

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nx < 0 or ny < 0 or nx >= w or ny >= h:
                continue
            if seen[ny][nx]:
                continue
            if not _is_bg(rgba.getpixel((nx, ny))):
                continue
            seen[ny][nx] = True
            queue.append((nx, ny))

    min_x = w
    min_y = h
    max_x = -1
    max_y = -1
    for y in range(h):
        for x in range(w):
            if seen[y][x]:
                continue
            if x < min_x:
                min_x = x
            if y < min_y:
                min_y = y
            if x > max_x:
                max_x = x
            if y > max_y:
                max_y = y

    if max_x < min_x or max_y < min_y:
        raise ValueError("no subject pixels found")
    return rgba, seen, (min_x, min_y, max_x + 1, max_y + 1)


def _build_output(src_path, out_path):
    src = Image.open(src_path).convert("RGBA")
    processed, bg_mask, bbox = _subject_bbox(src)
    w, h = processed.size
    for y in range(h):
        for x in range(w):
            if bg_mask[y][x]:
                processed.putpixel((x, y), (0, 0, 0, 255))
    cropped = processed.crop(bbox)
    crop_w, crop_h = cropped.size
    scale = min(float(CONTENT_W) / float(crop_w), float(CONTENT_H) / float(crop_h))
    draw_w = max(1, int(round(crop_w * scale)))
    draw_h = max(1, int(round(crop_h * scale)))
    resized = cropped.resize((draw_w, draw_h), Image.NEAREST)

    canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 255))
    paste_x = CONTENT_X + ((CONTENT_W - draw_w) // 2)
    paste_y = CONTENT_Y + ((CONTENT_H - draw_h) // 2)
    canvas.paste(resized, (paste_x, paste_y), resized)
    canvas.save(out_path)
    print(f"wrote: {out_path}")


def main():
    for src_name, out_name in SPECS:
        src_path = ROOT / src_name
        out_path = ROOT / out_name
        if not src_path.exists():
            raise FileNotFoundError(f"missing source: {src_path}")
        _build_output(src_path, out_path)


if __name__ == "__main__":
    main()
