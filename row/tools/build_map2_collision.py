#!/usr/bin/env python3
"""
Build chapter-2 collision previews strictly from two 960x600 reference images.

Rules:
- Red line image defines non-crossable border.
- Outside the red-line enclosed area is blocked.
- Red area image defines blocked regions.
- Output is preview-only (no write to row/assets/out_map2).

Tile compatibility mode:
- 16px tiles, 60x38 grid (960x608).
- The bottom 8px padding (y=600..607) is treated as blocked.
"""

import argparse
import hashlib
import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


SRC_W = 960
SRC_H = 600
TILE = 16
GRID_W = SRC_W // TILE
GRID_H = 38
GRID_H_PX = GRID_H * TILE

# Red line (first image): slightly magenta/red line from JPEG.
LINE_R_MIN = 140
LINE_G_MAX = 125
LINE_B_MIN = 40
LINE_RG_DIFF_MIN = 25

# Red blocked area (second image): mostly pure red with JPEG noise.
BLOCK_R_MIN = 145
BLOCK_G_MAX = 115
BLOCK_B_MAX = 120
BLOCK_RG_DIFF_MIN = 35
BLOCK_RB_DIFF_MIN = 35


def is_line_red_pixel(r, g, b):
    return (
        r >= LINE_R_MIN
        and g <= LINE_G_MAX
        and b >= LINE_B_MIN
        and (r - g) >= LINE_RG_DIFF_MIN
    )


def is_blocked_red_pixel(r, g, b):
    return (
        r >= BLOCK_R_MIN
        and g <= BLOCK_G_MAX
        and b <= BLOCK_B_MAX
        and (r - g) >= BLOCK_RG_DIFF_MIN
        and (r - b) >= BLOCK_RB_DIFF_MIN
    )


def build_mask(img, predicate):
    w, h = img.size
    px = img.load()
    mask = [bytearray(w) for _ in range(h)]
    for y in range(h):
        row = mask[y]
        for x in range(w):
            r, g, b = px[x, y]
            row[x] = 1 if predicate(r, g, b) else 0
    return mask


def dilate_3x3(mask):
    h = len(mask)
    w = len(mask[0])
    out = [bytearray(w) for _ in range(h)]
    for y in range(h):
        y0 = max(0, y - 1)
        y1 = min(h - 1, y + 1)
        out_row = out[y]
        for x in range(w):
            x0 = max(0, x - 1)
            x1 = min(w - 1, x + 1)
            hit = 0
            for ny in range(y0, y1 + 1):
                src = mask[ny]
                for nx in range(x0, x1 + 1):
                    if src[nx]:
                        hit = 1
                        break
                if hit:
                    break
            out_row[x] = hit
    return out


def erode_3x3(mask):
    h = len(mask)
    w = len(mask[0])
    out = [bytearray(w) for _ in range(h)]
    for y in range(h):
        y0 = max(0, y - 1)
        y1 = min(h - 1, y + 1)
        out_row = out[y]
        for x in range(w):
            x0 = max(0, x - 1)
            x1 = min(w - 1, x + 1)
            keep = 1
            for ny in range(y0, y1 + 1):
                src = mask[ny]
                for nx in range(x0, x1 + 1):
                    if not src[nx]:
                        keep = 0
                        break
                if not keep:
                    break
            out_row[x] = keep
    return out


def open_3x3(mask):
    # Morphological opening (erode then dilate): keeps core areas, removes tiny speckles.
    return dilate_3x3(erode_3x3(mask))


def invert_mask(mask):
    h = len(mask)
    w = len(mask[0])
    out = [bytearray(w) for _ in range(h)]
    for y in range(h):
        src = mask[y]
        dst = out[y]
        for x in range(w):
            dst[x] = 0 if src[x] else 1
    return out


def clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def find_nearest_non_line_seed(line_mask, sx, sy):
    h = len(line_mask)
    w = len(line_mask[0])
    sx = clamp(sx, 0, w - 1)
    sy = clamp(sy, 0, h - 1)
    if not line_mask[sy][sx]:
        return sx, sy

    max_r = max(w, h)
    for r in range(1, max_r + 1):
        x0 = max(0, sx - r)
        x1 = min(w - 1, sx + r)
        y0 = max(0, sy - r)
        y1 = min(h - 1, sy + r)

        for x in range(x0, x1 + 1):
            if not line_mask[y0][x]:
                return x, y0
            if not line_mask[y1][x]:
                return x, y1

        for y in range(y0 + 1, y1):
            if not line_mask[y][x0]:
                return x0, y
            if not line_mask[y][x1]:
                return x1, y

    raise RuntimeError("NO_NON_LINE_SEED")


def flood_fill_inside(line_mask, seed_x, seed_y):
    h = len(line_mask)
    w = len(line_mask[0])
    inside = [bytearray(w) for _ in range(h)]
    q = deque()
    inside[seed_y][seed_x] = 1
    q.append((seed_x, seed_y))

    while q:
        x, y = q.popleft()
        if x > 0 and not line_mask[y][x - 1] and not inside[y][x - 1]:
            inside[y][x - 1] = 1
            q.append((x - 1, y))
        if x + 1 < w and not line_mask[y][x + 1] and not inside[y][x + 1]:
            inside[y][x + 1] = 1
            q.append((x + 1, y))
        if y > 0 and not line_mask[y - 1][x] and not inside[y - 1][x]:
            inside[y - 1][x] = 1
            q.append((x, y - 1))
        if y + 1 < h and not line_mask[y + 1][x] and not inside[y + 1][x]:
            inside[y + 1][x] = 1
            q.append((x, y + 1))

    return inside


def build_blocked_pixel_mask(line_mask, outside_line, blocked_mask_new):
    h = len(line_mask)
    w = len(line_mask[0])
    blocked = [bytearray(w) for _ in range(h)]
    for y in range(h):
        row = blocked[y]
        row_line = line_mask[y]
        row_out = outside_line[y]
        row_new = blocked_mask_new[y]
        for x in range(w):
            row[x] = 1 if (row_line[x] or row_out[x] or row_new[x]) else 0
    return blocked


def build_tile_collision(blocked_pixel_mask):
    collision = [[1] * GRID_W for _ in range(GRID_H)]

    for ty in range(GRID_H):
        py0 = ty * TILE
        py1 = py0 + TILE
        for tx in range(GRID_W):
            px0 = tx * TILE
            px1 = px0 + TILE

            tile_blocked = False
            for py in range(py0, py1):
                if py >= SRC_H:
                    tile_blocked = True
                    break
                row = blocked_pixel_mask[py]
                for px in range(px0, px1):
                    if row[px]:
                        tile_blocked = True
                        break
                if tile_blocked:
                    break

            collision[ty][tx] = 1 if tile_blocked else 0

    return collision


def verify_rules(line_mask, outside_line, blocked_mask_new, blocked_pixel_mask):
    h = len(line_mask)
    w = len(line_mask[0])
    line_fail = 0
    outside_fail = 0
    new_red_fail = 0

    for y in range(h):
        row_line = line_mask[y]
        row_out = outside_line[y]
        row_new = blocked_mask_new[y]
        row_block = blocked_pixel_mask[y]
        for x in range(w):
            if row_line[x] and not row_block[x]:
                line_fail += 1
            if row_out[x] and not row_block[x]:
                outside_fail += 1
            if row_new[x] and not row_block[x]:
                new_red_fail += 1

    return line_fail, outside_fail, new_red_fail


def build_pixel_overlay(base_img, line_mask, outside_line, blocked_mask_new, blocked_pixel_mask):
    out = base_img.convert("RGBA")
    pix = out.load()
    w, h = base_img.size

    for y in range(h):
        row_line = line_mask[y]
        row_out = outside_line[y]
        row_new = blocked_mask_new[y]
        row_block = blocked_pixel_mask[y]
        for x in range(w):
            r, g, b, a = pix[x, y]
            if row_line[x]:
                pix[x, y] = (255, 40, 40, 255)
            elif row_out[x]:
                pix[x, y] = (min(255, r + 45), g // 2, b // 2, a)
            elif row_new[x]:
                pix[x, y] = (min(255, r + 25), g, b, a)
            elif row_block[x]:
                pix[x, y] = (min(255, r + 10), g, b, a)

    return out


def build_tile_overlay(base_img, collision):
    out = Image.new("RGBA", (SRC_W, GRID_H_PX), (0, 0, 0, 255))
    out.paste(base_img.convert("RGBA"), (0, 0))
    draw = ImageDraw.Draw(out, "RGBA")

    blocked_fill = (255, 0, 0, 185)
    blocked_outline = (255, 0, 0, 230)

    for ty in range(GRID_H):
        y0 = ty * TILE
        y1 = y0 + TILE - 1
        for tx in range(GRID_W):
            if not collision[ty][tx]:
                continue
            x0 = tx * TILE
            x1 = x0 + TILE - 1
            draw.rectangle((x0, y0, x1, y1), fill=blocked_fill, outline=blocked_outline)

    # Explicitly mark padded bottom strip (600..607) as blocked in compatibility mode.
    draw.rectangle((0, SRC_H, SRC_W - 1, GRID_H_PX - 1), fill=(255, 0, 0, 220), outline=None)

    return out


def build_binary_mask_preview(blocked_pixel_mask):
    img = Image.new("RGB", (SRC_W, SRC_H), (0, 0, 0))
    pix = img.load()
    for y in range(SRC_H):
        row = blocked_pixel_mask[y]
        for x in range(SRC_W):
            if row[x]:
                pix[x, y] = (255, 0, 0)
    return img


def build_debug_mask_preview(line_mask, outside_line, blocked_mask_new):
    img = Image.new("RGB", (SRC_W, SRC_H), (0, 0, 0))
    pix = img.load()
    for y in range(SRC_H):
        row_line = line_mask[y]
        row_out = outside_line[y]
        row_new = blocked_mask_new[y]
        for x in range(SRC_W):
            if row_line[x]:
                pix[x, y] = (255, 255, 255)  # white = red line (after dilation)
            elif row_out[x]:
                pix[x, y] = (0, 0, 255)  # blue = outside line area
            elif row_new[x]:
                pix[x, y] = (255, 0, 0)  # red = blocked by 2nd image
    return img


def sha256_of(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--line-image",
        required=True,
        help="Red line image (cannot cross line).",
    )
    parser.add_argument(
        "--blocked-image",
        required=True,
        help="Red blocked-area image.",
    )
    parser.add_argument(
        "--preview-base-image",
        default="/workspace/map2 960x600.jpeg",
        help="Base map image for overlay preview.",
    )
    parser.add_argument(
        "--out-root",
        default="/workspace/tmp_board_dump",
        help="Parent directory for isolated timestamp output directory.",
    )
    args = parser.parse_args()

    line_path = Path(args.line_image).resolve()
    blocked_path = Path(args.blocked_image).resolve()
    preview_path = Path(args.preview_base_image).resolve()

    line_img = Image.open(str(line_path)).convert("RGB")
    blocked_img = Image.open(str(blocked_path)).convert("RGB")
    preview_base = Image.open(str(preview_path)).convert("RGB")

    for name, img in (("line", line_img), ("blocked", blocked_img), ("preview", preview_base)):
        if img.size != (SRC_W, SRC_H):
            raise SystemExit(
                "%s image size mismatch: expected %dx%d got %dx%d"
                % (name, SRC_W, SRC_H, img.size[0], img.size[1])
            )

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_root).resolve() / ("rebuild_" + run_stamp)
    out_dir.mkdir(parents=True, exist_ok=True)

    tile_overlay_path = out_dir / "collision_overlay_tile16_from_two_sources.png"
    manifest_path = out_dir / "inputs_manifest.json"

    line_mask_raw = build_mask(line_img, is_line_red_pixel)
    line_mask = dilate_3x3(line_mask_raw)  # red-line expand 1px (3x3)
    blocked_mask_new_raw = build_mask(blocked_img, is_blocked_red_pixel)
    blocked_mask_new = open_3x3(blocked_mask_new_raw)

    seed_x, seed_y = find_nearest_non_line_seed(line_mask, SRC_W // 2, SRC_H // 2)
    inside_line = flood_fill_inside(line_mask, seed_x, seed_y)
    outside_line = invert_mask(inside_line)

    blocked_pixel_mask = build_blocked_pixel_mask(line_mask, outside_line, blocked_mask_new)
    collision = build_tile_collision(blocked_pixel_mask)

    line_fail, outside_fail, new_red_fail = verify_rules(
        line_mask, outside_line, blocked_mask_new, blocked_pixel_mask
    )

    tile_overlay = build_tile_overlay(preview_base, collision)
    tile_overlay.save(tile_overlay_path)

    blocked_pixels = sum(sum(row) for row in blocked_pixel_mask)
    total_pixels = SRC_W * SRC_H
    blocked_tiles = sum(collision[ty][tx] for ty in range(GRID_H) for tx in range(GRID_W))
    total_tiles = GRID_W * GRID_H

    line_pixels = sum(sum(row) for row in line_mask)
    blocked_pixels_raw = sum(sum(row) for row in blocked_mask_new_raw)
    blocked_pixels_denoised = sum(sum(row) for row in blocked_mask_new)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "rules": {
            "line_rule": "red line cannot be crossed; outside enclosed area is blocked",
            "blocked_rule": "red area from second image is blocked after 3x3 opening denoise",
            "tile_rule": "16x16 tile blocked if any pixel is blocked",
            "compatibility_height_px": GRID_H_PX,
        },
        "inputs": [
            {
                "role": "line_image",
                "path": str(line_path),
                "sha256": sha256_of(line_path),
                "width": line_img.size[0],
                "height": line_img.size[1],
            },
            {
                "role": "blocked_image",
                "path": str(blocked_path),
                "sha256": sha256_of(blocked_path),
                "width": blocked_img.size[0],
                "height": blocked_img.size[1],
            },
            {
                "role": "preview_base_image",
                "path": str(preview_path),
                "sha256": sha256_of(preview_path),
                "width": preview_base.size[0],
                "height": preview_base.size[1],
            },
        ],
        "verification": {
            "rule_verify_line_fail": line_fail,
            "rule_verify_outside_fail": outside_fail,
            "rule_verify_blocked_red_fail": new_red_fail,
        },
        "stats": {
            "line_pixels_dilated": line_pixels,
            "blocked_red_pixels_raw": blocked_pixels_raw,
            "blocked_red_pixels_after_open3x3": blocked_pixels_denoised,
            "blocked_pixels_final": blocked_pixels,
            "blocked_pixels_total": total_pixels,
            "blocked_tiles_final": blocked_tiles,
            "blocked_tiles_total": total_tiles,
            "seed_xy": [seed_x, seed_y],
            "grid_wh": [GRID_W, GRID_H],
            "tile_size": TILE,
        },
        "outputs": [
            {
                "role": "tile_overlay",
                "path": str(tile_overlay_path),
                "sha256": sha256_of(tile_overlay_path),
            }
        ],
    }
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=True, indent=2)

    print("seed:", (seed_x, seed_y))
    print("grid:", "%dx%d" % (GRID_W, GRID_H), "tile:", TILE, "compat_height:", GRID_H_PX)
    print("blocked_pixels:", blocked_pixels, "/", total_pixels)
    print("blocked_tiles:", blocked_tiles, "/", total_tiles)
    print("blocked_red_raw:", blocked_pixels_raw)
    print("blocked_red_after_open3x3:", blocked_pixels_denoised)

    print("rule_verify_line_fail:", line_fail)
    print("rule_verify_outside_fail:", outside_fail)
    print("rule_verify_new_red_fail:", new_red_fail)

    print("tile_overlay:", tile_overlay_path)
    print("manifest:", manifest_path)
    print("output_dir:", out_dir)

    print("tile_overlay_sha256:", sha256_of(tile_overlay_path))
    print("manifest_sha256:", sha256_of(manifest_path))


if __name__ == "__main__":
    main()
