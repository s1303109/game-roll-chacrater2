#!/usr/bin/env python3
from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageMath


ROOT = Path("/workspace")
SRC_SHEET = ROOT / "boss.png"
OUT_SHEET = ROOT / "row/assets/out/map6_boss_sheet.rgb565"
OUT_BATTLE = ROOT / "map6_boss_battle.png"
OUT_PREVIEW = ROOT / "row/assets/out/map6_boss_sheet_preview.png"

FRAME_W = 192
FRAME_H = 192
SHEET_COLS = 3
SHEET_ROWS = 3
CONTENT_W = 176
CONTENT_H = 176
BOTTOM_MARGIN = 2
BATTLE_OUT_W = 96
BATTLE_OUT_H = 96


def _is_bg(px: Tuple[int, int, int, int]) -> bool:
    r, g, b, a = px
    if a == 0:
        return True
    hi = max(r, g, b)
    lo = min(r, g, b)
    return hi >= 236 and lo >= 220 and (hi - lo) <= 22


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
                m[nx, ny] = 0
                q.append((nx, ny))
    return mask


def _main_component_in_place(rgba: Image.Image) -> Tuple[Image.Image, Tuple[int, int, int, int]]:
    w, h = rgba.size
    px = rgba.load()
    seen = bytearray(w * h)
    best_count = 0
    best_pixels: List[Tuple[int, int]] = []
    best_bbox = (0, 0, 0, 0)

    for y in range(h):
        row = y * w
        for x in range(w):
            idx = row + x
            if seen[idx]:
                continue
            if px[x, y][3] == 0:
                seen[idx] = 1
                continue
            q: deque[Tuple[int, int]] = deque()
            q.append((x, y))
            seen[idx] = 1
            count = 0
            min_x, min_y, max_x, max_y = x, y, x, y
            cells: List[Tuple[int, int]] = []
            while q:
                cx, cy = q.popleft()
                if px[cx, cy][3] == 0:
                    continue
                cells.append((cx, cy))
                count += 1
                if cx < min_x:
                    min_x = cx
                if cy < min_y:
                    min_y = cy
                if cx > max_x:
                    max_x = cx
                if cy > max_y:
                    max_y = cy
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
                    if seen[nidx]:
                        continue
                    seen[nidx] = 1
                    if px[nx, ny][3] > 0:
                        q.append((nx, ny))
            if count > best_count:
                best_count = count
                best_pixels = cells
                best_bbox = (min_x, min_y, max_x + 1, max_y + 1)

    if best_count < 1:
        raise RuntimeError("no visible component")

    out = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    out_px = out.load()
    for x, y in best_pixels:
        out_px[x, y] = px[x, y]
    return out, best_bbox


def _trim_edge_halo(rgba: Image.Image, passes: int = 2, hi_th: int = 200, lo_th: int = 150, spread_th: int = 45) -> Image.Image:
    img = rgba.copy()
    for _ in range(passes):
        src = img.copy()
        s = src.load()
        d = img.load()
        w, h = img.size
        changed = False
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                r, g, b, a = s[x, y]
                if a == 0:
                    continue
                hi = max(r, g, b)
                lo = min(r, g, b)
                if not (hi >= hi_th and lo >= lo_th and (hi - lo) <= spread_th):
                    continue
                touch_transparent = False
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
                    if s[nx, ny][3] == 0:
                        touch_transparent = True
                        break
                if touch_transparent:
                    d[x, y] = (0, 0, 0, 0)
                    changed = True
        if not changed:
            break
    return img


def _halo_metric(rgba: Image.Image, hi_th: int = 190, lo_th: int = 130, spread_th: int = 65) -> int:
    p = rgba.load()
    w, h = rgba.size
    score = 0
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            r, g, b, a = p[x, y]
            if a == 0:
                continue
            hi = max(r, g, b)
            lo = min(r, g, b)
            if not (hi >= hi_th and lo >= lo_th and (hi - lo) <= spread_th):
                continue
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
                if p[nx, ny][3] == 0:
                    score += 1
                    break
    return score


def _resize_rgba_no_halo(img: Image.Image, size: Tuple[int, int]) -> Image.Image:
    r, g, b, a = img.split()
    rp = ImageMath.eval("convert((r*a)/255, 'L')", r=r, a=a)
    gp = ImageMath.eval("convert((g*a)/255, 'L')", g=g, a=a)
    bp = ImageMath.eval("convert((b*a)/255, 'L')", b=b, a=a)
    rp = rp.resize(size, Image.Resampling.LANCZOS)
    gp = gp.resize(size, Image.Resampling.LANCZOS)
    bp = bp.resize(size, Image.Resampling.LANCZOS)
    a2 = a.resize(size, Image.Resampling.LANCZOS)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    op = out.load()
    rp2 = rp.load()
    gp2 = gp.load()
    bp2 = bp.load()
    ap2 = a2.load()
    w, h = size
    for y in range(h):
        for x in range(w):
            aa = ap2[x, y]
            if aa <= 0:
                op[x, y] = (0, 0, 0, 0)
                continue
            rr = (rp2[x, y] * 255 + (aa // 2)) // aa
            gg = (gp2[x, y] * 255 + (aa // 2)) // aa
            bb = (bp2[x, y] * 255 + (aa // 2)) // aa
            if rr > 255:
                rr = 255
            if gg > 255:
                gg = 255
            if bb > 255:
                bb = 255
            op[x, y] = (rr, gg, bb, aa)
    return out


def _component_anchor(rgba: Image.Image, bbox: Tuple[int, int, int, int]) -> Tuple[float, float]:
    l, t, r, b = bbox
    px = rgba.load()
    cutoff = t + int(round((b - t) * 0.40))
    sum_x = 0
    count = 0
    for y in range(cutoff, b):
        for x in range(l, r):
            if px[x, y][3] > 0:
                sum_x += x
                count += 1
    if count < 1:
        for y in range(t, b):
            for x in range(l, r):
                if px[x, y][3] > 0:
                    sum_x += x
                    count += 1
    if count < 1:
        return (0.5 * (l + r), float(b))
    return (sum_x / count, float(b))


def _prepare_frames() -> List[Image.Image]:
    def _trim_sprite(rgba: Image.Image) -> Tuple[Image.Image, Tuple[int, int, int, int]]:
        alpha = _edge_bg_mask(rgba)
        rgba.putalpha(alpha)
        main, bbox = _main_component_in_place(rgba)
        main = _trim_edge_halo(main, passes=3, hi_th=200, lo_th=150, spread_th=45)
        main, bbox = _main_component_in_place(main)
        return main, bbox

    if not SRC_SHEET.exists():
        raise FileNotFoundError(SRC_SHEET)
    sheet = Image.open(SRC_SHEET).convert("RGBA")
    src_w, src_h = sheet.size

    cleaned_cells: List[Tuple[Image.Image, Tuple[int, int, int, int]]] = []
    cell_sizes: List[Tuple[int, int]] = []
    for row in range(SHEET_ROWS):
        y0 = int(round((row * src_h) / SHEET_ROWS))
        y1 = int(round(((row + 1) * src_h) / SHEET_ROWS))
        for col in range(SHEET_COLS):
            x0 = int(round((col * src_w) / SHEET_COLS))
            x1 = int(round(((col + 1) * src_w) / SHEET_COLS))
            cell = sheet.crop((x0, y0, x1, y1))
            cleaned_cells.append(_trim_sprite(cell))
            cell_sizes.append(cell.size)

    if len(cleaned_cells) != (SHEET_COLS * SHEET_ROWS):
        raise RuntimeError("invalid frame count from boss.png")

    # Per-frame inspection: apply extra cleanup only to the worst 2 halo frames.
    halo_scores: List[Tuple[int, int]] = []
    for idx, (sprite, _bbox) in enumerate(cleaned_cells):
        halo_scores.append((idx, _halo_metric(sprite)))
    halo_scores.sort(key=lambda x: x[1], reverse=True)
    for idx, score in halo_scores[:2]:
        if score <= 0:
            continue
        sprite, _bbox = cleaned_cells[idx]
        refined = _trim_edge_halo(sprite, passes=2, hi_th=175, lo_th=120, spread_th=80)
        refined, refined_bbox = _main_component_in_place(refined)
        cleaned_cells[idx] = (refined, refined_bbox)

    max_comp_w = max((bbox[2] - bbox[0]) for _, bbox in cleaned_cells)
    max_comp_h = max((bbox[3] - bbox[1]) for _, bbox in cleaned_cells)
    scale = min(CONTENT_W / max_comp_w, CONTENT_H / max_comp_h, 1.0)

    max_cell_w = max(w for w, _ in cell_sizes)
    max_cell_h = max(h for _, h in cell_sizes)
    target_cell_w = max(1, int(round(max_cell_w * scale)))
    target_cell_h = max(1, int(round(max_cell_h * scale)))
    base_x = (FRAME_W - target_cell_w) // 2
    base_y = FRAME_H - BOTTOM_MARGIN - target_cell_h

    anchors: List[Tuple[float, float]] = []
    for sprite, bbox in cleaned_cells:
        ax, ay = _component_anchor(sprite, bbox)
        anchors.append((ax * scale, ay * scale))
    ref_index = 4 if len(anchors) > 4 else (len(anchors) // 2)
    ref_ax, ref_ay = anchors[ref_index]

    frames: List[Image.Image] = []
    for (sprite, bbox), (ax, ay) in zip(cleaned_cells, anchors):
        normalized = Image.new("RGBA", (max_cell_w, max_cell_h), (255, 255, 255, 0))
        normalized.alpha_composite(sprite, (0, 0))
        resized = _resize_rgba_no_halo(normalized, (target_cell_w, target_cell_h))
        canvas = Image.new("RGBA", (FRAME_W, FRAME_H), (255, 255, 255, 0))
        dx = int(round(ref_ax - ax))
        dy = int(round(ref_ay - ay))
        canvas.alpha_composite(resized, (base_x + dx, base_y + dy))
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

    battle = Image.new("RGBA", (BATTLE_OUT_W, BATTLE_OUT_H), (255, 255, 255, 0))
    battle_src = frames[0]
    if battle_src.size != (BATTLE_OUT_W, BATTLE_OUT_H):
        battle_src = battle_src.resize((BATTLE_OUT_W, BATTLE_OUT_H), Image.Resampling.LANCZOS)
    battle.alpha_composite(battle_src, (0, 0))
    battle.save(OUT_BATTLE)

    print("wrote:", OUT_SHEET)
    print("wrote:", OUT_PREVIEW)
    print("wrote:", OUT_BATTLE)


if __name__ == "__main__":
    main()
