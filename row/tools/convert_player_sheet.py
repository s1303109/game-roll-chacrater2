import argparse
import os
from PIL import Image


def rgb_to_565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def pack_565(value, endian):
    if endian == "little":
        return bytes([value & 0xFF, (value >> 8) & 0xFF])
    return bytes([(value >> 8) & 0xFF, value & 0xFF])


def convert_sheet(input_path, out_path, grid, endian):
    img = Image.open(input_path).convert("RGB")
    sheet_w, sheet_h = img.size
    if sheet_w <= 0 or sheet_h <= 0:
        raise SystemExit("invalid image size")
    if sheet_w % grid != 0 or sheet_h % grid != 0:
        raise SystemExit("image size must be divisible by grid size")

    frame_w = sheet_w // grid
    frame_h = sheet_h // grid
    pixels = img.load()

    buf = bytearray()
    for y in range(sheet_h):
        for x in range(sheet_w):
            r, g, b = pixels[x, y]
            buf += pack_565(rgb_to_565(r, g, b), endian)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(buf)

    print("input:", input_path)
    print("output:", out_path)
    print("sheet:", sheet_w, sheet_h)
    print("frame:", frame_w, frame_h)
    print("grid:", grid, "x", grid)
    print("endian:", endian)
    print("bytes:", len(buf))


def main():
    parser = argparse.ArgumentParser(description="Convert sprite sheet image to raw RGB565 binary.")
    parser.add_argument("input", help="source sprite sheet image (e.g. main character.jpg)")
    parser.add_argument("--out", default="assets/out/player_sheet.rgb565", help="output raw RGB565 file")
    parser.add_argument("--grid", type=int, default=3, help="frame grid per axis (default: 3 for 3x3)")
    parser.add_argument("--endian", choices=["little", "big"], default="little", help="RGB565 byte order")
    args = parser.parse_args()

    if args.grid <= 0:
        raise SystemExit("grid must be positive")

    convert_sheet(args.input, args.out, args.grid, args.endian)


if __name__ == "__main__":
    main()
