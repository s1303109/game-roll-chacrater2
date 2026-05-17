#!/usr/bin/env python3
import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw


@dataclass(frozen=True)
class WoodMapSpec:
    key: str
    collision_src: Path
    base_src: Path
    out_dir: Path


def is_red_block_pixel(r, g, b, a):
    if a <= 0:
        return False
    return r >= 200 and g <= 80 and b <= 100


def ratio_blocked(red_count, tile_pixels, threshold):
    if tile_pixels <= 0:
        return False
    return (red_count / tile_pixels) >= threshold


def build_collision_and_overlay(collision_img, base_img, tile, threshold):
    w, h = collision_img.size
    if (w % tile) != 0 or (h % tile) != 0:
        raise ValueError("image size must be divisible by tile size")

    map_w = w // tile
    map_h = h // tile
    tile_pixels = tile * tile
    coll = bytearray(map_w * map_h)
    red_pixels = 0
    tiles_blocked = 0
    tiles_with_any_red = 0

    col_px = collision_img.load()
    overlay = base_img.convert("RGBA")
    draw = ImageDraw.Draw(overlay, "RGBA")

    for ty in range(map_h):
        py0 = ty * tile
        py1 = py0 + tile
        for tx in range(map_w):
            px0 = tx * tile
            px1 = px0 + tile

            red_count = 0
            for y in range(py0, py1):
                for x in range(px0, px1):
                    r, g, b, a = col_px[x, y]
                    if is_red_block_pixel(r, g, b, a):
                        red_count += 1

            red_pixels += red_count
            if red_count > 0:
                tiles_with_any_red += 1

            blocked = ratio_blocked(red_count, tile_pixels, threshold)
            idx = ty * map_w + tx
            coll[idx] = 1 if blocked else 0
            if blocked:
                tiles_blocked += 1
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

    # draw grid to make review easier
    for x in range(0, w + 1, tile):
        draw.line((x, 0, x, h - 1), fill=(255, 255, 255, 55), width=1)
    for y in range(0, h + 1, tile):
        draw.line((0, y, w - 1, y), fill=(255, 255, 255, 55), width=1)

    stats = {
        "width": w,
        "height": h,
        "tile": tile,
        "map_w": map_w,
        "map_h": map_h,
        "threshold": threshold,
        "red_pixels": red_pixels,
        "tiles_total": map_w * map_h,
        "tiles_with_any_red": tiles_with_any_red,
        "tiles_blocked": tiles_blocked,
    }
    return coll, overlay, stats


def update_map_json(map_json_path):
    with open(map_json_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    meta["collision"] = "collision.bin"
    meta["collision_format"] = "u8"
    with open(map_json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")


def resolve_specs(repo_root):
    assets_root = repo_root / "assets"
    return (
        WoodMapSpec(
            key="main",
            collision_src=Path("/workspace/wood main collision.png"),
            base_src=Path("/workspace/wood door main.jpeg"),
            out_dir=assets_root / "out_wood_main",
        ),
        WoodMapSpec(
            key="right",
            collision_src=Path("/workspace/wood right collision.png"),
            base_src=Path("/workspace/wood door right.jpeg"),
            out_dir=assets_root / "out_wood_right",
        ),
        WoodMapSpec(
            key="up",
            collision_src=Path("/workspace/wood up collision.png"),
            base_src=Path("/workspace/wood door up .jpeg"),
            out_dir=assets_root / "out_wood_up",
        ),
        WoodMapSpec(
            key="left",
            collision_src=Path("/workspace/wood left collision.png"),
            base_src=Path("/workspace/wood door left .jpeg"),
            out_dir=assets_root / "out_wood_left",
        ),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Build collision.bin for wood maps from red mask images."
    )
    parser.add_argument("--threshold", type=float, default=0.2)
    parser.add_argument("--tile", type=int, default=16)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.tile <= 0:
        raise SystemExit("tile must be > 0")
    if args.threshold < 0 or args.threshold > 1:
        raise SystemExit("threshold must be within [0, 1]")

    repo_root = Path(__file__).resolve().parents[1]
    specs = resolve_specs(repo_root)

    print("repo_root:", repo_root)
    print("tile:", args.tile, "threshold:", args.threshold, "dry_run:", args.dry_run)

    for spec in specs:
        if not spec.collision_src.exists():
            raise SystemExit("missing collision source: %s" % spec.collision_src)
        if not spec.out_dir.exists():
            raise SystemExit("missing output dir: %s" % spec.out_dir)

        col_img = Image.open(spec.collision_src).convert("RGBA")
        if spec.base_src.exists():
            base_img = Image.open(spec.base_src).convert("RGBA")
            if base_img.size != col_img.size:
                base_img = col_img.convert("RGBA")
        else:
            base_img = col_img.convert("RGBA")

        collision, overlay, stats = build_collision_and_overlay(
            col_img, base_img, args.tile, args.threshold
        )

        collision_path = spec.out_dir / "collision.bin"
        map_json_path = spec.out_dir / "map.json"
        overlay_path = spec.out_dir / "collision_overlay_preview.png"

        print(
            "[%s]" % spec.key,
            "blocked_tiles=%d/%d any_red_tiles=%d red_pixels=%d"
            % (
                stats["tiles_blocked"],
                stats["tiles_total"],
                stats["tiles_with_any_red"],
                stats["red_pixels"],
            ),
        )

        if args.dry_run:
            continue

        with open(collision_path, "wb") as f:
            f.write(collision)
        update_map_json(map_json_path)
        overlay.save(overlay_path)
        print("[%s] wrote:" % spec.key, collision_path)
        print("[%s] wrote:" % spec.key, map_json_path)
        print("[%s] wrote:" % spec.key, overlay_path)


if __name__ == "__main__":
    main()
