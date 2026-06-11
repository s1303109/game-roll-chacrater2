#!/usr/bin/env python3
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path("/workspace")
ASSET_ROOT = ROOT / "row/assets"
TILE = 16
TARGET_W = 640
TARGET_H = 608
SOURCE_H = 600
SPAWN_X = 320
SPAWN_Y = 584
COLLISION_THRESHOLD_NUM = 1
COLLISION_THRESHOLD_DEN = 5

try:
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE_LANCZOS = Image.LANCZOS


SPECS = (
    {
        "kind": "safe",
        "map_src": ROOT / "safe map.jpeg",
        "collision_src": ROOT / "safe map collision.jpeg",
        "out_dir": ASSET_ROOT / "out_end_safe",
        "end_src": ROOT / "safe map end.png",
        "end_out": ROOT / "ending_safe_320x240.png",
    },
    {
        "kind": "normal",
        "map_src": ROOT / "normal map.jpeg",
        "collision_src": ROOT / "normal map collision.jpeg",
        "out_dir": ASSET_ROOT / "out_end_normal",
        "end_src": ROOT / "normal map end.png",
        "end_out": ROOT / "ending_normal_320x240.png",
    },
    {
        "kind": "death",
        "map_src": ROOT / "death map.jpeg",
        "collision_src": ROOT / "death map collision.jpeg",
        "out_dir": ASSET_ROOT / "out_end_death",
        "end_src": ROOT / "death map end.png",
        "end_out": ROOT / "ending_death_320x240.png",
    },
)


def rgb_to_565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def pack_565(value):
    return bytes((value & 0xFF, (value >> 8) & 0xFF))


def is_red_block_pixel(r, g, b):
    return r >= 200 and g <= 80 and b <= 100


def normalize_640x608(path):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    if w != TARGET_W:
        raise SystemExit("%s width must be %d, got %d" % (path, TARGET_W, w))
    if h == TARGET_H:
        return img.copy()
    if h != SOURCE_H:
        raise SystemExit("%s height must be %d or %d, got %d" % (path, SOURCE_H, TARGET_H, h))

    out = Image.new("RGB", (TARGET_W, TARGET_H))
    out.paste(img, (0, 0))
    bottom_row = img.crop((0, SOURCE_H - 1, TARGET_W, SOURCE_H))
    for y in range(SOURCE_H, TARGET_H):
        out.paste(bottom_row, (0, y))
    return out


def build_tiles(img):
    w, h = img.size
    if (w % TILE) != 0 or (h % TILE) != 0:
        raise SystemExit("image size must be divisible by %d" % TILE)
    map_w = w // TILE
    map_h = h // TILE
    pixels = img.load()
    tileset = []
    tile_index = {}
    tilemap = []

    for ty in range(map_h):
        for tx in range(map_w):
            data = bytearray()
            base_x = tx * TILE
            base_y = ty * TILE
            for y in range(TILE):
                for x in range(TILE):
                    r, g, b = pixels[base_x + x, base_y + y]
                    data += pack_565(rgb_to_565(r, g, b))
            key = bytes(data)
            idx = tile_index.get(key)
            if idx is None:
                idx = len(tileset)
                tile_index[key] = idx
                tileset.append(key)
            tilemap.append(idx)
    return tileset, tilemap, map_w, map_h


def build_collision(collision_img, map_w, map_h):
    tile_pixels = TILE * TILE
    pixels = collision_img.load()
    collision = bytearray(map_w * map_h)
    blocked_tiles = 0

    for ty in range(map_h):
        base_y = ty * TILE
        for tx in range(map_w):
            base_x = tx * TILE
            red_count = 0
            for y in range(TILE):
                for x in range(TILE):
                    if is_red_block_pixel(*pixels[base_x + x, base_y + y]):
                        red_count += 1
            blocked = (red_count * COLLISION_THRESHOLD_DEN) >= (tile_pixels * COLLISION_THRESHOLD_NUM)
            collision[ty * map_w + tx] = 1 if blocked else 0
            if blocked:
                blocked_tiles += 1
    return collision, blocked_tiles


def write_overlay(out_path, collision_img, collision, map_w, map_h):
    overlay = collision_img.convert("RGBA")
    draw = ImageDraw.Draw(overlay, "RGBA")
    for ty in range(map_h):
        y0 = ty * TILE
        y1 = y0 + TILE - 1
        for tx in range(map_w):
            x0 = tx * TILE
            x1 = x0 + TILE - 1
            if collision[ty * map_w + tx]:
                draw.rectangle((x0, y0, x1, y1), fill=(255, 0, 0, 110), outline=(255, 0, 0, 230))
            else:
                draw.rectangle((x0, y0, x1, y1), outline=(0, 255, 0, 70))
    for x in range(0, TARGET_W + 1, TILE):
        draw.line((x, 0, x, TARGET_H - 1), fill=(255, 255, 255, 55), width=1)
    for y in range(0, TARGET_H + 1, TILE):
        draw.line((0, y, TARGET_W - 1, y), fill=(255, 255, 255, 55), width=1)
    overlay.save(out_path)


def write_map_assets(spec):
    out_dir = spec["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    map_img = normalize_640x608(spec["map_src"])
    collision_img = normalize_640x608(spec["collision_src"])
    tileset, tilemap, map_w, map_h = build_tiles(map_img)
    if collision_img.size != map_img.size:
        raise SystemExit("collision image size mismatch: %s" % spec["collision_src"])
    collision, blocked_tiles = build_collision(collision_img, map_w, map_h)

    with open(out_dir / "tileset.bin", "wb") as f:
        for tile_data in tileset:
            f.write(tile_data)
    with open(out_dir / "tilemap.bin", "wb") as f:
        for idx in tilemap:
            f.write(idx.to_bytes(2, "little"))
    with open(out_dir / "collision.bin", "wb") as f:
        f.write(collision)

    meta = {
        "tile_size": TILE,
        "map_w": map_w,
        "map_h": map_h,
        "tileset_count": len(tileset),
        "endian": "little",
        "row_order": "top_to_bottom",
        "spawn_x": SPAWN_X,
        "spawn_y": SPAWN_Y,
        "collision": "collision.bin",
        "collision_format": "u8",
        "collision_rule": "red_pixel_ratio_gte_20_percent_per_16x16_tile",
    }
    with open(out_dir / "map.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")

    write_overlay(out_dir / "collision_overlay_preview.png", collision_img, collision, map_w, map_h)

    print(
        "%s map_w=%d map_h=%d tileset=%d collision_bytes=%d blocked_tiles=%d"
        % (spec["kind"], map_w, map_h, len(tileset), len(collision), blocked_tiles)
    )


def write_end_png(spec):
    img = Image.open(spec["end_src"]).convert("RGB")
    img = img.resize((320, 240), RESAMPLE_LANCZOS)
    img.save(spec["end_out"])
    print("%s end_png=%s" % (spec["kind"], spec["end_out"]))


def main():
    for spec in SPECS:
        for key in ("map_src", "collision_src", "end_src"):
            if not spec[key].exists():
                raise SystemExit("missing source: %s" % spec[key])
        write_map_assets(spec)
        write_end_png(spec)


if __name__ == "__main__":
    main()
