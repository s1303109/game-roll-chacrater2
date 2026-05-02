import argparse
import json
import os
from PIL import Image


def rgb_to_565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def unpack_565(data, endian):
    if endian == "little":
        return data[0] | (data[1] << 8)
    return (data[0] << 8) | data[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="source image")
    parser.add_argument("--out", default="assets/out", help="folder containing map.json/tileset.bin/tilemap.bin")
    args = parser.parse_args()

    with open(os.path.join(args.out, "map.json"), "r", encoding="utf-8") as f:
        meta = json.load(f)
    with open(os.path.join(args.out, "tileset.bin"), "rb") as f:
        tileset = f.read()
    with open(os.path.join(args.out, "tilemap.bin"), "rb") as f:
        tilemap = f.read()

    img = Image.open(args.input).convert("RGB")
    w, h = img.size
    pixels = img.load()

    tile = meta["tile_size"]
    map_w = meta["map_w"]
    map_h = meta["map_h"]
    endian = meta["endian"]
    row_order = meta["row_order"]

    if row_order != "top_to_bottom":
        raise SystemExit("unsupported row order in meta")
    if w != map_w * tile or h != map_h * tile:
        raise SystemExit("dimension mismatch between source image and map metadata")

    tile_pixels = tile * tile
    tile_bytes = tile_pixels * 2
    if len(tilemap) != map_w * map_h * 2:
        raise SystemExit("tilemap size mismatch")
    if len(tileset) % tile_bytes != 0:
        raise SystemExit("tileset size mismatch")

    mismatches = 0
    for ty in range(map_h):
        for tx in range(map_w):
            i = (ty * map_w + tx) * 2
            tile_index = unpack_565(tilemap[i:i + 2], endian)
            if tile_index * tile_bytes >= len(tileset):
                raise SystemExit(f"tile index out of range at ({tx},{ty}): {tile_index}")
            tile_offset = tile_index * tile_bytes
            tile_data = tileset[tile_offset:tile_offset + tile_bytes]
            for y in range(tile):
                for x in range(tile):
                    p = (y * tile + x) * 2
                    c_bin = unpack_565(tile_data[p:p + 2], endian)
                    r, g, b = pixels[tx * tile + x, ty * tile + y]
                    c_img = rgb_to_565(r, g, b)
                    if c_bin != c_img:
                        mismatches += 1
                        if mismatches <= 10:
                            print("mismatch", tx, ty, x, y, hex(c_bin), hex(c_img))

    if mismatches == 0:
        print("verify ok: endian and row_order match source")
    else:
        raise SystemExit(f"verify failed: {mismatches} mismatched pixels")


if __name__ == "__main__":
    main()
