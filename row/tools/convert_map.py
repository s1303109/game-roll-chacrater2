import argparse
import json
import os
from collections import deque
from PIL import Image


def rgb_to_565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def pack_565(value, endian):
    if endian == "little":
        return bytes([value & 0xFF, (value >> 8) & 0xFF])
    return bytes([(value >> 8) & 0xFF, value & 0xFF])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="source image")
    parser.add_argument("--out", default="assets/out", help="output folder")
    parser.add_argument("--tile", type=int, default=16, help="tile size")
    parser.add_argument("--endian", choices=["little", "big"], default="little")
    parser.add_argument("--spawn-x", type=int, default=-1)
    parser.add_argument("--spawn-y", type=int, default=-1)
    parser.add_argument("--collision", help="collision mask image")
    args = parser.parse_args()

    img = Image.open(args.input).convert("RGB")
    w, h = img.size
    tile = args.tile

    if w % tile != 0 or h % tile != 0:
        raise SystemExit("image size must be divisible by tile size")

    map_w = w // tile
    map_h = h // tile

    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)

    tileset = []
    tile_index = {}
    tilemap = []

    pixels = img.load()
    for ty in range(map_h):
        for tx in range(map_w):
            data = bytearray()
            for y in range(tile):
                for x in range(tile):
                    r, g, b = pixels[tx * tile + x, ty * tile + y]
                    color = rgb_to_565(r, g, b)
                    data += pack_565(color, args.endian)
            key = bytes(data)
            if key in tile_index:
                idx = tile_index[key]
            else:
                idx = len(tileset)
                tile_index[key] = idx
                tileset.append(key)
            tilemap.append(idx)

    tileset_path = os.path.join(out_dir, "tileset.bin")
    tilemap_path = os.path.join(out_dir, "tilemap.bin")

    with open(tileset_path, "wb") as f:
        for t in tileset:
            f.write(t)

    with open(tilemap_path, "wb") as f:
        for idx in tilemap:
            f.write(idx.to_bytes(2, args.endian))

    if args.spawn_x < 0:
        args.spawn_x = w // 2
    if args.spawn_y < 0:
        args.spawn_y = h // 2

    collision_written = False
    if args.collision:
        col_img = Image.open(args.collision).convert("RGB")
        if col_img.size != img.size:
            raise SystemExit("collision image size mismatch")
        col_pixels = col_img.load()
        line = [bytearray(w) for _ in range(h)]
        for y in range(h):
            row = line[y]
            for x in range(w):
                r, g, b = col_pixels[x, y]
                if r >= 200 and g <= 80 and b <= 80:
                    row[x] = 1

        outside = [bytearray(w) for _ in range(h)]
        q = deque()
        for x in range(w):
            q.append((x, 0))
            q.append((x, h - 1))
        for y in range(h):
            q.append((0, y))
            q.append((w - 1, y))

        while q:
            x, y = q.popleft()
            if x < 0 or y < 0 or x >= w or y >= h:
                continue
            if outside[y][x] or line[y][x]:
                continue
            outside[y][x] = 1
            q.append((x + 1, y))
            q.append((x - 1, y))
            q.append((x, y + 1))
            q.append((x, y - 1))

        collision = bytearray(map_w * map_h)
        for ty in range(map_h):
            base_y = ty * tile
            for tx in range(map_w):
                base_x = tx * tile
                blocked = False
                for y in range(tile):
                    row = base_y + y
                    line_row = line[row]
                    outside_row = outside[row]
                    for x in range(tile):
                        col = base_x + x
                        if line_row[col] or outside_row[col]:
                            blocked = True
                            break
                    if blocked:
                        break
                collision[ty * map_w + tx] = 1 if blocked else 0

        collision_path = os.path.join(out_dir, "collision.bin")
        with open(collision_path, "wb") as f:
            f.write(collision)
        collision_written = True

    meta = {
        "tile_size": tile,
        "map_w": map_w,
        "map_h": map_h,
        "tileset_count": len(tileset),
        "endian": args.endian,
        "row_order": "top_to_bottom",
        "spawn_x": args.spawn_x,
        "spawn_y": args.spawn_y,
    }
    if collision_written:
        meta["collision"] = "collision.bin"
        meta["collision_format"] = "u8"
    with open(os.path.join(out_dir, "map.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("tileset:", tileset_path)
    print("tilemap:", tilemap_path)
    if collision_written:
        print("collision:", os.path.join(out_dir, "collision.bin"))
    print("meta:", os.path.join(out_dir, "map.json"))


if __name__ == "__main__":
    main()
