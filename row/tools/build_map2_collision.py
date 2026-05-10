#!/usr/bin/env python3
"""
Rebuild map2 collision strictly from two user-provided red references.

Rules:
- Red line image defines non-crossable border.
- New red overlay image defines blocked regions.
- Outside the red-line enclosed area is blocked.
- Tile collision is written as u8 (0 walkable / 1 blocked).
"""

import argparse
import hashlib
import json
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw


MAP2_W = 1600
MAP2_H = 960
TILE = 16
MAP2_TILES_W = MAP2_W // TILE
MAP2_TILES_H = MAP2_H // TILE

# maps 2 collision.jpeg (thin line).
LINE_R_MIN = 150
LINE_G_MAX = 125
LINE_B_MIN = 45
LINE_RG_DIFF_MIN = 25

# maps 2 collision(NEW).jpg (large red blocked regions).
BLOCK_R_MIN = 145
BLOCK_G_MAX = 95
BLOCK_B_MAX = 110
BLOCK_RG_DIFF_MIN = 40
BLOCK_RB_DIFF_MIN = 40

# When inside line-area and not on line, block tile if NEW red ratio is high enough.
BLOCK_TILE_RATIO_MIN = 0.55
BLOCK_TILE_STRONG_RATIO_MIN = 0.82
NOISE_CLEAN_PASSES = 2
NOISE_CLEAN_WALK_NEIGHBORS_MIN = 5


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


def classify_tiles(line_mask, outside_line, blocked_mask_new):
    collision = [[1] * MAP2_TILES_W for _ in range(MAP2_TILES_H)]
    forced_block = [[0] * MAP2_TILES_W for _ in range(MAP2_TILES_H)]
    new_ratio = [[0.0] * MAP2_TILES_W for _ in range(MAP2_TILES_H)]
    tile_area = TILE * TILE

    for ty in range(MAP2_TILES_H):
        py0 = ty * TILE
        py1 = py0 + TILE
        for tx in range(MAP2_TILES_W):
            px0 = tx * TILE
            px1 = px0 + TILE
            block_now = False
            new_red_count = 0

            for py in range(py0, py1):
                row_out = outside_line[py]
                row_line = line_mask[py]
                row_new = blocked_mask_new[py]
                for px in range(px0, px1):
                    if row_out[px] or row_line[px]:
                        block_now = True
                        break
                    new_red_count += row_new[px]
                if block_now:
                    break

            if block_now:
                collision[ty][tx] = 1
                forced_block[ty][tx] = 1
                new_ratio[ty][tx] = 1.0
            else:
                ratio = new_red_count / float(tile_area)
                new_ratio[ty][tx] = ratio
                collision[ty][tx] = 1 if ratio >= BLOCK_TILE_RATIO_MIN else 0

    return collision, forced_block, new_ratio


def cleanup_noise(collision, forced_block, new_ratio):
    # Remove isolated false blocked tiles on floor while keeping strong-red obstacles.
    for _ in range(NOISE_CLEAN_PASSES):
        prev = [row[:] for row in collision]
        for ty in range(1, MAP2_TILES_H - 1):
            for tx in range(1, MAP2_TILES_W - 1):
                if forced_block[ty][tx]:
                    continue
                if not prev[ty][tx]:
                    continue
                if new_ratio[ty][tx] >= BLOCK_TILE_STRONG_RATIO_MIN:
                    continue

                walk_neighbors = 0
                for ny in (ty - 1, ty, ty + 1):
                    for nx in (tx - 1, tx, tx + 1):
                        if nx == tx and ny == ty:
                            continue
                        if prev[ny][nx] == 0:
                            walk_neighbors += 1
                if walk_neighbors >= NOISE_CLEAN_WALK_NEIGHBORS_MIN:
                    collision[ty][tx] = 0


def collision_to_bytes(collision):
    out = bytearray(MAP2_TILES_W * MAP2_TILES_H)
    i = 0
    for ty in range(MAP2_TILES_H):
        for tx in range(MAP2_TILES_W):
            out[i] = 1 if collision[ty][tx] else 0
            i += 1
    return out


def build_overlay_preview(base_img, collision, outside_line, line_mask, blocked_mask_new):
    out = base_img.convert("RGBA")
    draw = ImageDraw.Draw(out, "RGBA")

    blocked_fill = (255, 0, 0, 95)
    blocked_outline = (255, 0, 0, 180)
    line_fill = (255, 30, 30, 220)

    # Draw pixel-level line and outside masks first.
    pix = out.load()
    for y in range(MAP2_H):
        row_out = outside_line[y]
        row_line = line_mask[y]
        row_new = blocked_mask_new[y]
        for x in range(MAP2_W):
            if row_line[x]:
                pix[x, y] = line_fill
            elif row_out[x]:
                r, g, b, a = pix[x, y]
                pix[x, y] = (min(255, r + 40), g // 2, b // 2, a)
            elif row_new[x]:
                r, g, b, a = pix[x, y]
                pix[x, y] = (min(255, r + 20), g, b, a)

    for ty in range(MAP2_TILES_H):
        y0 = ty * TILE
        y1 = y0 + TILE - 1
        for tx in range(MAP2_TILES_W):
            if not collision[ty][tx]:
                continue
            x0 = tx * TILE
            x1 = x0 + TILE - 1
            draw.rectangle((x0, y0, x1, y1), fill=blocked_fill, outline=blocked_outline)

    return out


def update_map_json(map_json_path, meta):
    meta["collision"] = "collision.bin"
    meta["collision_format"] = "u8"
    map_json_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


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
        default="/workspace/maps 2 collision.jpeg",
        help="Red line image (border cannot be crossed).",
    )
    parser.add_argument(
        "--blocked-image",
        default="/workspace/maps 2 collision(NEW).jpg",
        help="Red blocked-area image.",
    )
    parser.add_argument(
        "--preview-base-image",
        default="/workspace/maps 2 true.jpeg",
        help="Base map image for overlay preview.",
    )
    parser.add_argument(
        "--out-dir",
        default="/workspace/row/assets/out_map2",
        help="Output dir for collision.bin and preview.",
    )
    args = parser.parse_args()

    line_img = Image.open(str(Path(args.line_image))).convert("RGB")
    if line_img.size != (MAP2_W, MAP2_H):
        raise SystemExit(
            "line image size mismatch: expected %dx%d got %dx%d"
            % (MAP2_W, MAP2_H, line_img.size[0], line_img.size[1])
        )

    blocked_img = Image.open(str(Path(args.blocked_image))).convert("RGB")
    if blocked_img.size != (MAP2_W, MAP2_H):
        raise SystemExit(
            "blocked image size mismatch: expected %dx%d got %dx%d"
            % (MAP2_W, MAP2_H, blocked_img.size[0], blocked_img.size[1])
        )

    preview_base = Image.open(str(Path(args.preview_base_image))).convert("RGB")
    if preview_base.size != (MAP2_W, MAP2_H):
        raise SystemExit(
            "preview base size mismatch: expected %dx%d got %dx%d"
            % (MAP2_W, MAP2_H, preview_base.size[0], preview_base.size[1])
        )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    map_json_path = out_dir / "map.json"
    collision_path = out_dir / "collision.bin"
    overlay_path = out_dir / "collision_overlay_preview.png"

    if not map_json_path.exists():
        raise SystemExit("missing map.json: %s" % map_json_path)

    meta = json.loads(map_json_path.read_text(encoding="utf-8"))
    tile_size = int(meta.get("tile_size", TILE))
    map_w = int(meta.get("map_w", MAP2_TILES_W))
    map_h = int(meta.get("map_h", MAP2_TILES_H))
    if tile_size != TILE:
        raise SystemExit("map.json tile_size mismatch: got %d expected %d" % (tile_size, TILE))
    if map_w != MAP2_TILES_W or map_h != MAP2_TILES_H:
        print(
            "warning: map_json_grid_mismatch map=%dx%d image_grid=%dx%d (continuing with image grid)"
            % (map_w, map_h, MAP2_TILES_W, MAP2_TILES_H)
        )

    spawn_x = clamp(int(meta.get("spawn_x", MAP2_W // 2)), 0, MAP2_W - 1)
    spawn_y = clamp(int(meta.get("spawn_y", MAP2_H // 2)), 0, MAP2_H - 1)

    line_mask_raw = build_mask(line_img, is_line_red_pixel)
    line_mask = dilate_3x3(line_mask_raw)
    blocked_mask_new = build_mask(blocked_img, is_blocked_red_pixel)

    seed_x, seed_y = find_nearest_non_line_seed(line_mask, spawn_x, spawn_y)
    inside_line = flood_fill_inside(line_mask, seed_x, seed_y)
    outside_line = invert_mask(inside_line)

    collision, forced_block, new_ratio = classify_tiles(line_mask, outside_line, blocked_mask_new)
    cleanup_noise(collision, forced_block, new_ratio)

    collision_bytes = collision_to_bytes(collision)
    collision_path.write_bytes(collision_bytes)
    update_map_json(map_json_path, meta)

    preview = build_overlay_preview(preview_base, collision, outside_line, line_mask, blocked_mask_new)
    preview.save(overlay_path)

    blocked = sum(1 for b in collision_bytes if b)
    total = len(collision_bytes)
    line_pixels = sum(sum(row) for row in line_mask)
    blocked_new_pixels = sum(sum(row) for row in blocked_mask_new)
    outside_pixels = sum(sum(row) for row in outside_line)

    print("collision:", collision_path)
    print("overlay_preview:", overlay_path)
    print("seed:", (seed_x, seed_y), "spawn:", (spawn_x, spawn_y))
    print("line_pixels:", line_pixels)
    print("new_blocked_pixels:", blocked_new_pixels)
    print("outside_line_pixels:", outside_pixels)
    print("blocked_tiles:", blocked, "/", total)
    print("collision_sha256:", sha256_of(collision_path))


if __name__ == "__main__":
    main()
