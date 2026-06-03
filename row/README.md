# MicroPython + LovyanGFX (ESP32-S3) Starter

This workspace contains a user C module for LovyanGFX (tile v2 + sprite path)
and tools for map conversion.

Note: `modules/lgfx/ili9341.c` is kept only as a historical stub and is not
linked by the current build path.

## Fixed SPI host assignment
- TFT (LovyanGFX panel bus) -> `SPI2` (HSPI)
- microSD (`machine.SDCard` in SPI mode) -> `SPI3` (VSPI)

For ESP32-S3 in this MicroPython tree, SD SPI slot mapping is:
- `slot=2` -> `SPI3`
- `slot=3` -> `SPI2`

## Tile loading mode
- `lgfx.tile_load_files()` now uses **tileset streaming + small LRU cache** in C++.
- This avoids loading full `tileset.bin` into RAM and is intended for no-PSRAM/low-RAM boards.
- Rebuild and reflash firmware after pulling code changes; Python scripts alone are not enough.
- Runtime check:
  - `lgfx.tile_loader_mode() == 2` means streaming+cache firmware is running.
  - If `tile_load_files` fails, `lgfx.tile_last_error()` returns:
    - `1` args/setup invalid
    - `2` cannot open tilemap file
    - `3` tilemap size mismatch/read fail
    - `4` cannot open tileset file
    - `5` tileset seek fail
    - `6` tileset size invalid
    - `7` tileset format invalid
    - `8` cache allocation failed

## Directory layout
- modules/ : user_cmodules (lgfx)
- app/     : MicroPython test scripts
- tools/   : asset conversion tools

## Build (ESP32-S3)
1) Clone MicroPython and LovyanGFX.
2) Set ESP-IDF environment.
3) Build with USER_C_MODULES.

One-shot build script:

```bash
tools/build_esp32s3.sh
```

Equivalent manual steps:

```bash
export IDF_PATH=/path/to/esp-idf
. $IDF_PATH/export.sh

git clone https://github.com/micropython/micropython.git

# LovyanGFX should exist at /workspace/LovyanGFX by default
# or pass LGFX_DIR via CMAKE_ARGS

cd micropython/ports/esp32
make BOARD=ESP32_GENERIC_S3 USER_C_MODULES=/workspace/modules/micropython.cmake
```

If LovyanGFX is not at /workspace/LovyanGFX, pass a CMake arg:

```bash
make BOARD=ESP32_GENERIC_S3 USER_C_MODULES=/workspace/modules/micropython.cmake \
  CMAKE_ARGS="-DLGFX_DIR=/path/to/LovyanGFX"
```

## Test scripts
- app/test_colors.py : RGB cycle (fill)
- app/test_fill.py   : fill-only FPS test
- app/test_sprite.py : sprite (back buffer) FPS test
- app/test_sd.py     : SD read test (4KB)
- app/test_tiles.py  : tile render test using the cartridge at `/sd/game`
- app/game_mvp.py    : game runtime module loaded by the SD cartridge launcher
- app/test_stability.py : long-run FPS/memory test
- app/validate_full.py : full validation (FPS + memory + long-run stability) using `/sd/game`
- app/run_all_phases.py : runs board-side validation scripts without starting the infinite game loop

## Map conversion
Example:

```bash
python3 tools/convert_map.py /workspace/undefined---640x960.jpeg \
  --out assets/out --tile 16 --endian little --spawn-x 320 --spawn-y 760
```

Expected metadata for 640x960 + tile16:
- `map_w = 40`
- `map_h = 60`

Dependency (host-side conversion/verification):

```bash
apt-get install -y python3-pil
```

Outputs:
- tileset.bin
- tilemap.bin
- map.json

## Cartridge layout
Flash root should contain only:
- `/boot.py`
- `/main.py`
- `/launcher.py`
- `/sd_host.py`

The game cartridge lives on SD:

```text
/sd/game
├── game_mvp.py
├── config.py
├── map_registry.py
├── assets/...
├── sprites/player_sheet.rgb565
├── ui/...
└── save/
```

Use `./deploy.sh` for a full sync or `./deploy_changed.sh` for a changed-only sync.
Both scripts deploy Flash launcher files plus the complete cartridge layout under `/sd/game`.
The deploy flow creates `/sd/game/save/` if missing and does not create or overwrite `save1.json`.

## Suggested board-side validation order
1) `import test_sd`
2) `import test_sprite`
3) `import test_tiles`
4) `import validate_full`
5) reset the board or `import main` to boot the cartridge launcher

Or run all at once:

1) `import run_all_phases`
