Test scripts for MicroPython.

- test_colors.py: RGB cycle
- test_fill.py: fill-only FPS
- test_sprite.py: sprite back buffer FPS
- test_sd.py: SD read test
- test_tiles.py: tile render test (loads /sd/out and prints file sizes + tile_last_error)
- game_mvp.py: red-dot player + map scroll MVP
- test_stability.py: long-run sprite stability test
- validate_full.py: full validation (sprite fps + tile fps + stability)
- copy_assets_to_sd.py: copy /remote/assets/out -> /sd/out
