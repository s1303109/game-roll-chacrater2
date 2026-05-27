#!/usr/bin/env python3
from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import List, Tuple

from PIL import Image


ROOT = Path("/workspace")
SRC_FILES = [ROOT / f"boss{i}.png" for i in range(1, 7)]
OUT_SHEET = ROOT / "row/assets/out/map6_boss_sheet.rgb565"
OUT_BATTLE = ROOT / "map6_boss_battle.png"
OUT_PREVIEW = ROOT / "row/assets/out/map6_boss_sheet_preview.png"

FRAME_W = 96
FRAME_H = 96
SHEET_COLS = 3
SHEET_ROWS = 2
CONTENT_W = 88
CONTENT_H = 88
BOTTOM_MARGIN = 2


def _is_bg(px: Tuple[int, int, int, int]) -> bool:
    r, g, b, a = px
    return a == 0 or (r >= 245 and g >= 245 and b >= 245)


def _edge_bg_mask(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()
    seen = bytearray(w * h)
    mask = Image.new("L", (w, h), 255)
    m = mask.load()
    q: deque[Tuple[int, int]] = deque()

    def push(x: int, y: int) -> None:
        idx = y * w + x
        if seen[idx]:
            return
        seen[idx] = 1
        if _is_bg(px[x, y]):
            q.append((x, y))
            m[x, y] = 0

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(1, h - 1):
        push(0, y)
        push(w - 1, y)

    while q:
        x, y = q.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nx < 0 or ny < 0 or nx >= w or ny >= h:
                continue
            idx = ny * w + nx
            if seen[idx]:
                continue
            seen[idx] = 1
            if _is_bg(px[nx, ny]):
                m[nx, ny] = 0
                q.append((nx, ny))
    return mask


def _prepare_frames() -> List[Image.Image]:
    cropped: List[Image.Image] = []
    sizes: List[Tuple[int, int]] = []

    for src in SRC_FILES:
        if not src.exists():
            raise FileNotFoundError(src)
        rgba = Image.open(src).convert("RGBA")
        alpha = _edge_bg_mask(rgba)
        rgba.putalpha(alpha)
        bbox = rgba.getbbox()
        if not bbox:
            raise RuntimeError(f"no visible pixels: {src}")
        sprite = rgba.crop(bbox)
        cropped.append(sprite)
        sizes.append(sprite.size)

    max_w = max(w for w, _ in sizes)
    max_h = max(h for _, h in sizes)
    scale = min(CONTENT_W / max_w, CONTENT_H / max_h, 1.0)

    frames: List[Image.Image] = []
    for sprite in cropped:
        w, h = sprite.size
        tw = max(1, int(round(w * scale)))
        th = max(1, int(round(h * scale)))
        resized = sprite.resize((tw, th), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (FRAME_W, FRAME_H), (255, 255, 255, 0))
        px = (FRAME_W - tw) // 2
        py = FRAME_H - BOTTOM_MARGIN - th
        canvas.alpha_composite(resized, (px, py))
        frames.append(canvas)
    return frames


def _rgb565_bytes(img: Image.Image) -> bytes:
    rgb = img.convert("RGB")
    out = bytearray()
    for r, g, b in rgb.getdata():
        v = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
        out.extend(v.to_bytes(2, "little"))
    return bytes(out)


def main() -> None:
    frames = _prepare_frames()

    sheet = Image.new("RGBA", (FRAME_W * SHEET_COLS, FRAME_H * SHEET_ROWS), (255, 255, 255, 255))
    for i, frame in enumerate(frames):
        x = (i % SHEET_COLS) * FRAME_W
        y = (i // SHEET_COLS) * FRAME_H
        bg = Image.new("RGBA", (FRAME_W, FRAME_H), (255, 255, 255, 255))
        bg.alpha_composite(frame, (0, 0))
        sheet.alpha_composite(bg, (x, y))

    OUT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    OUT_SHEET.write_bytes(_rgb565_bytes(sheet))
    sheet.save(OUT_PREVIEW)

    battle = Image.new("RGBA", (FRAME_W, FRAME_H), (255, 255, 255, 0))
    battle.alpha_composite(frames[0], (0, 0))
    battle.save(OUT_BATTLE)

    print("wrote:", OUT_SHEET)
    print("wrote:", OUT_PREVIEW)
    print("wrote:", OUT_BATTLE)


if __name__ == "__main__":
    main()
