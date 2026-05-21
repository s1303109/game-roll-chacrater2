#!/usr/bin/env python3
"""Prepare 6 boot comic frames for ESP32 title intro.

Input (fixed): /workspace/6 block comics.png
Output (fixed): /workspace/comic_01_320x240.png ... /workspace/comic_06_320x240.png
"""

from __future__ import annotations

import os
import sys

INPUT_PATH = "/workspace/6 block comics.png"
OUTPUT_TEMPLATE = "/workspace/comic_{:02d}_320x240.png"
TARGET_W = 320
TARGET_H = 240
TARGET_RATIO = TARGET_W / TARGET_H


def _err(msg: str) -> int:
    print(msg, file=sys.stderr)
    return 1


def _is_light_gray(px: tuple[int, int, int]) -> bool:
    r, g, b = px
    if r < 170 or g < 170 or b < 170:
        return False
    return abs(r - g) < 25 and abs(g - b) < 25 and abs(r - b) < 25


def _best_separator_column(img, center: int, half_window: int = 90) -> int:
    w, h = img.size
    x0 = max(0, center - half_window)
    x1 = min(w - 1, center + half_window)
    pix = img.load()
    best_x = center
    best_score = -1
    for x in range(x0, x1 + 1):
        light = 0
        for y in range(h):
            if _is_light_gray(pix[x, y]):
                light += 1
        if light > best_score:
            best_score = light
            best_x = x
    return best_x


def _best_separator_row(img, center: int, half_window: int = 90) -> int:
    w, h = img.size
    y0 = max(0, center - half_window)
    y1 = min(h - 1, center + half_window)
    pix = img.load()
    best_y = center
    best_score = -1
    for y in range(y0, y1 + 1):
        light = 0
        for x in range(w):
            if _is_light_gray(pix[x, y]):
                light += 1
        if light > best_score:
            best_score = light
            best_y = y
    return best_y


def _edge_light_ratio(img, edge: str) -> float:
    w, h = img.size
    pix = img.load()
    light = 0
    total = 0
    if edge == "top":
        y = 0
        for x in range(w):
            total += 1
            if _is_light_gray(pix[x, y]):
                light += 1
    elif edge == "bottom":
        y = h - 1
        for x in range(w):
            total += 1
            if _is_light_gray(pix[x, y]):
                light += 1
    elif edge == "left":
        x = 0
        for y in range(h):
            total += 1
            if _is_light_gray(pix[x, y]):
                light += 1
    else:
        x = w - 1
        for y in range(h):
            total += 1
            if _is_light_gray(pix[x, y]):
                light += 1
    if total <= 0:
        return 0.0
    return light / total


def _trim_white_border(panel):
    # Remove separator-like white border lines around each panel.
    while panel.height > 8 and _edge_light_ratio(panel, "top") > 0.90:
        panel = panel.crop((0, 1, panel.width, panel.height))
    while panel.height > 8 and _edge_light_ratio(panel, "bottom") > 0.90:
        panel = panel.crop((0, 0, panel.width, panel.height - 1))
    while panel.width > 8 and _edge_light_ratio(panel, "left") > 0.90:
        panel = panel.crop((1, 0, panel.width, panel.height))
    while panel.width > 8 and _edge_light_ratio(panel, "right") > 0.90:
        panel = panel.crop((0, 0, panel.width - 1, panel.height))
    return panel


def _crop_to_ratio(img, ratio: float):
    w, h = img.size
    if w <= 0 or h <= 0:
        return img
    now = w / h
    if now > ratio:
        nw = int(h * ratio)
        if nw < 1:
            nw = 1
        x0 = (w - nw) // 2
        return img.crop((x0, 0, x0 + nw, h))
    if now < ratio:
        nh = int(w / ratio)
        if nh < 1:
            nh = 1
        y0 = (h - nh) // 2
        return img.crop((0, y0, w, y0 + nh))
    return img


def _remove_top_number_area(panel):
    # Remove left-top number blocks by cropping a top strip.
    top_cut = max(40, panel.height // 13)
    if top_cut >= panel.height - 4:
        top_cut = max(0, panel.height - 4)
    return panel.crop((0, top_cut, panel.width, panel.height))


def main() -> int:
    try:
        from PIL import Image
    except Exception as exc:
        return _err(f"Pillow import failed: {exc}")

    if not os.path.isfile(INPUT_PATH):
        return _err(f"Input file not found: {INPUT_PATH}")

    try:
        img = Image.open(INPUT_PATH).convert("RGB")
    except Exception as exc:
        return _err(f"Failed to open input image: {exc}")

    w, h = img.size
    x_mid = _best_separator_column(img, w // 2)
    y1 = _best_separator_row(img, h // 3)
    y2 = _best_separator_row(img, (h * 2) // 3)

    # Use separators as split boundaries: 2 columns x 3 rows.
    x_bounds = [0, x_mid, w]
    y_bounds = [0, y1, y2, h]

    idx = 1
    for r in range(3):
        for c in range(2):
            x0 = x_bounds[c]
            x1 = x_bounds[c + 1]
            y0 = y_bounds[r]
            y1_ = y_bounds[r + 1]
            panel = img.crop((x0, y0, x1, y1_))
            panel = _trim_white_border(panel)
            panel = _remove_top_number_area(panel)
            panel = _crop_to_ratio(panel, TARGET_RATIO)
            panel = panel.resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)
            out_path = OUTPUT_TEMPLATE.format(idx)
            panel.save(out_path, format="PNG")
            print("saved", out_path)
            idx += 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
