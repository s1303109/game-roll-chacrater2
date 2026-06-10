#!/usr/bin/env python3
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Tuple

from PIL import Image


ROOT = Path("/workspace")
OUT_DIR = ROOT / "row/assets/out"

FRAME_W = 192
FRAME_H = 192
SHEET_COLS = 3
SHEET_ROWS = 2
CONTENT_W = 176
CONTENT_H = 176
BATTLE_W = 96
BATTLE_H = 96
BG_DARK_THRESHOLD = 14
EDGE_FRINGE_THRESHOLD = 7


@dataclass(frozen=True)
class BossSpec:
    key: str
    src: Path
    sheet: Path
    battle: Path
    preview: Path
    animate: Callable[[Image.Image], Iterable[Image.Image]]


def _is_bg(px: Tuple[int, int, int, int]) -> bool:
    r, g, b, a = px
    return a == 0 or (r <= BG_DARK_THRESHOLD and g <= BG_DARK_THRESHOLD and b <= BG_DARK_THRESHOLD)


def _edge_bg_mask(src: Image.Image) -> Image.Image:
    rgba = src.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()
    seen = bytearray(w * h)
    mask = Image.new("L", (w, h), 255)
    mp = mask.load()
    q: deque[Tuple[int, int]] = deque()

    def push(x: int, y: int) -> None:
        idx = y * w + x
        if seen[idx]:
            return
        seen[idx] = 1
        if _is_bg(px[x, y]):
            mp[x, y] = 0
            q.append((x, y))

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(1, h - 1):
        push(0, y)
        push(w - 1, y)

    while q:
        x, y = q.popleft()
        for nx, ny in (
            (x - 1, y),
            (x + 1, y),
            (x, y - 1),
            (x, y + 1),
            (x - 1, y - 1),
            (x + 1, y - 1),
            (x - 1, y + 1),
            (x + 1, y + 1),
        ):
            if nx < 0 or ny < 0 or nx >= w or ny >= h:
                continue
            idx = ny * w + nx
            if seen[idx]:
                continue
            seen[idx] = 1
            if _is_bg(px[nx, ny]):
                mp[nx, ny] = 0
                q.append((nx, ny))
    return mask


def _trim_edge_fringe(rgba: Image.Image, passes: int = 1) -> Image.Image:
    out = rgba.copy()
    for _ in range(passes):
        src = out.copy()
        sp = src.load()
        dp = out.load()
        w, h = out.size
        changed = False
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                r, g, b, a = sp[x, y]
                if a == 0 or max(r, g, b) > EDGE_FRINGE_THRESHOLD:
                    continue
                touches_clear = False
                for nx, ny in (
                    (x - 1, y),
                    (x + 1, y),
                    (x, y - 1),
                    (x, y + 1),
                    (x - 1, y - 1),
                    (x + 1, y - 1),
                    (x - 1, y + 1),
                    (x + 1, y + 1),
                ):
                    if sp[nx, ny][3] == 0:
                        touches_clear = True
                        break
                if touches_clear:
                    dp[x, y] = (0, 0, 0, 0)
                    changed = True
        if not changed:
            break
    return out


def _remove_tiny_noise(rgba: Image.Image) -> Image.Image:
    w, h = rgba.size
    px = rgba.load()
    seen = bytearray(w * h)
    clear = []
    for y in range(h):
        for x in range(w):
            idx = y * w + x
            if seen[idx] or px[x, y][3] == 0:
                seen[idx] = 1
                continue
            cells = []
            bright = False
            q = deque(((x, y),))
            seen[idx] = 1
            while q:
                cx, cy = q.popleft()
                cells.append((cx, cy))
                r, g, b, _a = px[cx, cy]
                if max(r, g, b) >= 90:
                    bright = True
                for nx, ny in (
                    (cx - 1, cy),
                    (cx + 1, cy),
                    (cx, cy - 1),
                    (cx, cy + 1),
                    (cx - 1, cy - 1),
                    (cx + 1, cy - 1),
                    (cx - 1, cy + 1),
                    (cx + 1, cy + 1),
                ):
                    if nx < 0 or ny < 0 or nx >= w or ny >= h:
                        continue
                    nidx = ny * w + nx
                    if seen[nidx] or px[nx, ny][3] == 0:
                        continue
                    seen[nidx] = 1
                    q.append((nx, ny))
            if len(cells) < 5 and not bright:
                clear.extend(cells)
    if not clear:
        return rgba
    out = rgba.copy()
    op = out.load()
    for x, y in clear:
        op[x, y] = (0, 0, 0, 0)
    return out


def _cutout(src_path: Path) -> Image.Image:
    src = Image.open(src_path).convert("RGBA")
    alpha = _edge_bg_mask(src)
    src.putalpha(alpha)
    src = _trim_edge_fringe(src, passes=1)
    src = _remove_tiny_noise(src)
    bbox = src.getbbox()
    if not bbox:
        raise RuntimeError("no subject pixels found: %s" % src_path)
    return src.crop(bbox)


def _fit_to_content(cutout: Image.Image) -> Image.Image:
    w, h = cutout.size
    scale = min(float(CONTENT_W) / float(w), float(CONTENT_H) / float(h), 1.0)
    draw_w = max(1, int(round(w * scale)))
    draw_h = max(1, int(round(h * scale)))
    return cutout.resize((draw_w, draw_h), Image.Resampling.NEAREST)


def _center_on_frame(sprite: Image.Image, dx: int = 0, dy: int = 0) -> Image.Image:
    frame = Image.new("RGBA", (FRAME_W, FRAME_H), (255, 255, 255, 0))
    x = (FRAME_W - sprite.width) // 2 + dx
    y = (FRAME_H - sprite.height) // 2 + dy
    frame.alpha_composite(sprite, (x, y))
    return frame


def _apply_mask_overlay(base: Image.Image, predicate: Callable[[int, int, int, int, int, int], bool], offset_x: int, offset_y: int, brightness: float) -> Image.Image:
    layer = Image.new("RGBA", base.size, (255, 255, 255, 0))
    bp = base.load()
    lp = layer.load()
    w, h = base.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = bp[x, y]
            if a == 0 or not predicate(x, y, r, g, b, a):
                continue
            rr = min(255, max(0, int(round(r * brightness))))
            gg = min(255, max(0, int(round(g * brightness))))
            bb = min(255, max(0, int(round(b * brightness))))
            tx = x + offset_x
            ty = y + offset_y
            if 0 <= tx < w and 0 <= ty < h:
                lp[tx, ty] = (rr, gg, bb, a)
    out = base.copy()
    out.alpha_composite(layer)
    return out


def _animate_fire(sprite: Image.Image) -> Iterable[Image.Image]:
    def is_warm(_x: int, _y: int, r: int, g: int, b: int, _a: int) -> bool:
        return r >= 125 and g >= 32 and b <= 95 and r > g

    flicker = (
        (0, 0, 1.00),
        (1, -1, 1.16),
        (-1, -2, 0.92),
        (0, -1, 1.22),
        (-1, 0, 0.88),
        (1, -1, 1.10),
    )
    for ox, oy, bright in flicker:
        yield _center_on_frame(_apply_mask_overlay(sprite, is_warm, ox, oy, bright))


def _animate_forest(sprite: Image.Image) -> Iterable[Image.Image]:
    def is_leaf_or_vine(_x: int, y: int, r: int, g: int, b: int, _a: int) -> bool:
        green = g >= 58 and g >= r and g > b
        vine = y < (sprite.height * 3) // 4 and g >= 42 and r >= 38 and b <= 55
        return green or vine

    offsets = (-1, 0, 1, 1, 0, -1)
    for ox in offsets:
        yield _center_on_frame(_apply_mask_overlay(sprite, is_leaf_or_vine, ox, 0, 1.03 if ox else 1.0))


def _animate_ice(sprite: Image.Image) -> Iterable[Image.Image]:
    for oy in (-3, -1, 1, 3, 1, -1):
        yield _center_on_frame(sprite, dy=oy)


def _rgb565_bytes(img: Image.Image) -> bytes:
    rgb = img.convert("RGB")
    out = bytearray()
    for r, g, b in rgb.getdata():
        v = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
        out.extend(v.to_bytes(2, "little"))
    return bytes(out)


def _write_outputs(spec: BossSpec) -> None:
    cutout = _cutout(spec.src)
    sprite = _fit_to_content(cutout)
    frames = tuple(spec.animate(sprite))
    if len(frames) != SHEET_COLS * SHEET_ROWS:
        raise RuntimeError("invalid frame count for %s" % spec.key)

    sheet = Image.new("RGBA", (FRAME_W * SHEET_COLS, FRAME_H * SHEET_ROWS), (255, 255, 255, 255))
    preview = Image.new("RGBA", sheet.size, (255, 255, 255, 255))
    for index, frame in enumerate(frames):
        cell = Image.new("RGBA", (FRAME_W, FRAME_H), (255, 255, 255, 255))
        cell.alpha_composite(frame)
        x = (index % SHEET_COLS) * FRAME_W
        y = (index // SHEET_COLS) * FRAME_H
        sheet.alpha_composite(cell, (x, y))
        preview.alpha_composite(cell, (x, y))

    spec.sheet.parent.mkdir(parents=True, exist_ok=True)
    spec.sheet.write_bytes(_rgb565_bytes(sheet))
    preview.save(spec.preview)

    battle_img = frames[0].resize((BATTLE_W, BATTLE_H), Image.Resampling.NEAREST)
    spec.battle.parent.mkdir(parents=True, exist_ok=True)
    battle_img.save(spec.battle)

    print("wrote:", spec.sheet)
    print("wrote:", spec.preview)
    print("wrote:", spec.battle)


SPECS = (
    BossSpec(
        "map9_forest_boss",
        ROOT / "forest enemy .png",
        OUT_DIR / "map9_forest_boss_sheet.rgb565",
        ROOT / "map9_forest_boss_battle.png",
        OUT_DIR / "map9_forest_boss_sheet_preview.png",
        _animate_forest,
    ),
    BossSpec(
        "map10_ice_boss",
        ROOT / "ice enemy .png",
        OUT_DIR / "map10_ice_boss_sheet.rgb565",
        ROOT / "map10_ice_boss_battle.png",
        OUT_DIR / "map10_ice_boss_sheet_preview.png",
        _animate_ice,
    ),
    BossSpec(
        "map11_fire_boss",
        ROOT / "fire enemy.png",
        OUT_DIR / "map11_fire_boss_sheet.rgb565",
        ROOT / "map11_fire_boss_battle.png",
        OUT_DIR / "map11_fire_boss_sheet_preview.png",
        _animate_fire,
    ),
)


def main() -> None:
    for spec in SPECS:
        if not spec.src.exists():
            raise FileNotFoundError(spec.src)
        _write_outputs(spec)


if __name__ == "__main__":
    main()
