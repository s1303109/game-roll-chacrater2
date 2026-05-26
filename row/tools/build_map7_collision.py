#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw


SRC_COLLISION_PATH = Path("/workspace/map7 collision.jpeg")
OUT_DIR = Path("/workspace/row/assets/out_map7")
OUT_COLLISION_PATH = OUT_DIR / "collision.bin"
OUT_MAP_JSON_PATH = OUT_DIR / "map.json"
OUT_TILEMAP_PATH = OUT_DIR / "tilemap.bin"
OUT_TILESET_PATH = OUT_DIR / "tileset.bin"
OUT_OVERLAY_PATH = OUT_DIR / "collision_overlay_preview.png"

TILE = 16
THRESHOLD = 0.2
TARGET_W = 640
TARGET_H = 1200
DEFAULT_SPAWN_X = 320
DEFAULT_SPAWN_Y = 888


def is_red_block_pixel(r, g, b):
    return r >= 200 and g <= 80 and b <= 100


def prepare_collision_image(src):
    img = Image.open(src).convert("RGB")
    w, h = img.size
    if w != TARGET_W or h != TARGET_H:
        raise SystemExit(
            "collision image size mismatch expected=%dx%d got=%dx%d"
            % (TARGET_W, TARGET_H, w, h)
        )
    return img


def build_collision(collision_img):
    w, h = collision_img.size
    if (w % TILE) != 0 or (h % TILE) != 0:
        raise SystemExit("image size must be divisible by tile")

    map_w = w // TILE
    map_h = h // TILE
    tile_pixels = TILE * TILE
    collision = bytearray(map_w * map_h)
    blocked_tiles = 0

    px = collision_img.load()
    for ty in range(map_h):
        py0 = ty * TILE
        py1 = py0 + TILE
        for tx in range(map_w):
            px0 = tx * TILE
            px1 = px0 + TILE
            red_count = 0
            for y in range(py0, py1):
                for x in range(px0, px1):
                    if is_red_block_pixel(*px[x, y]):
                        red_count += 1
            blocked = (red_count / tile_pixels) >= THRESHOLD
            idx = ty * map_w + tx
            collision[idx] = 1 if blocked else 0
            if blocked:
                blocked_tiles += 1

    return collision, map_w, map_h, blocked_tiles


def write_overlay(collision_img, collision, map_w, map_h):
    overlay = collision_img.convert("RGBA")
    draw = ImageDraw.Draw(overlay, "RGBA")
    for ty in range(map_h):
        py0 = ty * TILE
        py1 = py0 + TILE
        for tx in range(map_w):
            px0 = tx * TILE
            px1 = px0 + TILE
            blocked = bool(collision[ty * map_w + tx])
            if blocked:
                draw.rectangle(
                    (px0, py0, px1 - 1, py1 - 1),
                    fill=(255, 0, 0, 110),
                    outline=(255, 0, 0, 220),
                )
            else:
                draw.rectangle(
                    (px0, py0, px1 - 1, py1 - 1),
                    outline=(0, 255, 0, 70),
                )

    w, h = collision_img.size
    for x in range(0, w + 1, TILE):
        draw.line((x, 0, x, h - 1), fill=(255, 255, 255, 55), width=1)
    for y in range(0, h + 1, TILE):
        draw.line((0, y, w - 1, y), fill=(255, 255, 255, 55), width=1)

    overlay.save(OUT_OVERLAY_PATH)


def _ensure_map_assets_shape(map_w, map_h):
    if not OUT_TILEMAP_PATH.exists():
        raise SystemExit("missing tilemap: %s" % OUT_TILEMAP_PATH)
    if not OUT_TILESET_PATH.exists():
        raise SystemExit("missing tileset: %s" % OUT_TILESET_PATH)

    tilemap_size = OUT_TILEMAP_PATH.stat().st_size
    expected_tilemap_size = map_w * map_h * 2
    if tilemap_size != expected_tilemap_size:
        raise SystemExit(
            "tilemap size mismatch expected=%d got=%d"
            % (expected_tilemap_size, tilemap_size)
        )

    tile_bytes = TILE * TILE * 2
    tileset_size = OUT_TILESET_PATH.stat().st_size
    if tileset_size <= 0 or (tileset_size % tile_bytes) != 0:
        raise SystemExit(
            "tileset size invalid expected_multiple=%d got=%d"
            % (tile_bytes, tileset_size)
        )
    return tileset_size // tile_bytes


def update_or_create_map_json(path, map_w, map_h, tileset_count):
    meta = {}
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            meta = json.load(f)

    meta["tile_size"] = TILE
    meta["map_w"] = map_w
    meta["map_h"] = map_h
    meta["tileset_count"] = int(tileset_count)
    meta["endian"] = "little"
    meta["row_order"] = "top_to_bottom"
    meta["spawn_x"] = int(meta.get("spawn_x", DEFAULT_SPAWN_X))
    meta["spawn_y"] = int(meta.get("spawn_y", DEFAULT_SPAWN_Y))
    meta["collision"] = "collision.bin"
    meta["collision_format"] = "u8"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build Map7 collision from red mask image (16x16, red>=20% => blocked)."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preview-only", action="store_true", help="Only write overlay preview.")
    group.add_argument("--apply", action="store_true", help="Write collision.bin and update/create map.json.")
    return parser.parse_args()


def main():
    args = parse_args()

    if not SRC_COLLISION_PATH.exists():
        raise SystemExit("missing source: %s" % SRC_COLLISION_PATH)
    if not OUT_DIR.exists():
        raise SystemExit("missing out dir: %s" % OUT_DIR)

    collision_img = prepare_collision_image(SRC_COLLISION_PATH)
    collision, map_w, map_h, blocked_tiles = build_collision(collision_img)
    write_overlay(collision_img, collision, map_w, map_h)

    mode = "preview-only"
    tileset_count = _ensure_map_assets_shape(map_w, map_h)

    if args.apply:
        with open(OUT_COLLISION_PATH, "wb") as f:
            f.write(collision)
        update_or_create_map_json(OUT_MAP_JSON_PATH, map_w, map_h, tileset_count)
        mode = "apply"

    print("mode:", mode)
    print("source:", SRC_COLLISION_PATH)
    print("out_overlay:", OUT_OVERLAY_PATH)
    if args.apply:
        print("out_collision:", OUT_COLLISION_PATH)
        print("out_map_json:", OUT_MAP_JSON_PATH)
    print("map_w:", map_w, "map_h:", map_h, "blocked_tiles:", blocked_tiles)
    print("tileset_count:", tileset_count)
    print("collision_bytes:", len(collision))


if __name__ == "__main__":
    main()
