Test scripts for MicroPython.

- test_colors.py: RGB cycle
- test_fill.py: fill-only FPS
- test_sprite.py: sprite back buffer FPS
- test_sd.py: SD read test
- test_tiles.py: tile render test using `/sd/game/assets/...`
- game_mvp.py: game runtime module started by `launcher.py`
- test_stability.py: long-run sprite stability test
- validate_full.py: full validation (sprite fps + tile fps + stability) against the cartridge
- copy_assets_to_sd.py: deprecated; use `deploy.sh` or `deploy_changed.sh`
- run_all_phases.py: runs validation scripts without entering the infinite game loop
