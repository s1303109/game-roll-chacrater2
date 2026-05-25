import gc
import os
import sys

from sd_host import mount_sd


GAME_ROOT = "/sd/game"
STALE_FLASH_FILES = (
    "/game_mvp.py",
    "/config.py",
    "/map_registry.py",
    "/map.json",
    "/tilemap.bin",
    "/tileset.bin",
    "/collision.bin",
    "/player_sheet.rgb565",
    "/front_cover_320x240.png",
    "/title_ui_start_112x54.png",
    "/title_ui_continue_112x54.png",
    "/comic_01_320x240.png",
    "/comic_02_320x240.png",
    "/comic_03_320x240.png",
    "/comic_04_320x240.png",
    "/comic_05_320x240.png",
    "/comic_06_320x240.png",
    "/inventory_portrait.png",
    "/heart_clean_18.png",
    "/heart.png",
    "/star_icon_24.png",
    "/enemy.png",
    "/FLOWEY.png",
    "/ANGRY FLOWEY.png",
    "/map1_story_line_01.png",
    "/map1_story_line_02.png",
    "/map1_story_line_03.png",
    "/map1_story_line_04.png",
    "/map1_story_line_05.png",
    "/map1_story_line_06.png",
    "/map1_story_line_07.png",
    "/map1_story_line_08.png",
    "/map1_story_line_09.png",
    "/map1_story_line_10.png",
    "/fight_icon.png",
    "/act_icon.png",
    "/item_icon.png",
    "/mercy_icon.png",
    "/act_dialog_text.png",
    "/mercy_dialog_text.png",
    "/lamp_dialog_text.png",
    "/act_opt1_text.png",
    "/act_opt2_text.png",
    "/act_opt3_text.png",
    "/act_reply1_text.png",
    "/act_reply2_text.png",
    "/act_reply3_text.png",
    "/mercy_locked_text.png",
    "/main character close eyes.clean.png",
    "/main character close eyes.orig.png",
    "/titleui.png",
    "/comic_.png",
    "/spawn_closed_eyes_32x32.rgb565",
)


def _path_exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def _ensure_game_path():
    if GAME_ROOT in sys.path:
        sys.path.remove(GAME_ROOT)
    sys.path.insert(0, GAME_ROOT)


def _clear_game_modules():
    for name in list(sys.modules):
        if name in ("config", "map_registry", "game_mvp") or name.startswith("game_mvp."):
            del sys.modules[name]


def _report_stale_flash_files():
    stale = []
    for path in STALE_FLASH_FILES:
        if _path_exists(path):
            stale.append(path)
    for path in stale:
        print("[launcher] stale flash file ignored:", path)


def main():
    try:
        if not mount_sd("/sd", return_ok=True):
            raise RuntimeError("SD_MOUNT_FAILED")
    except Exception as err:
        print("[launcher] SD mount failed:", err)
        raise

    if not _path_exists(GAME_ROOT):
        print("[launcher] missing file:", GAME_ROOT)
        raise RuntimeError("GAME_ROOT_MISSING")

    _ensure_game_path()
    _clear_game_modules()
    _report_stale_flash_files()

    try:
        import config
        import map_registry

        config.validate_cartridge(map_registry.MAP_REGISTRY)
        import game_mvp
    except Exception as err:
        print("[launcher] cartridge load failed:", err)
        raise

    if not hasattr(game_mvp, "main"):
        print("[launcher] game_mvp.py has no main()")
        raise RuntimeError("GAME_MAIN_MISSING")

    gc.collect()
    try:
        game_mvp.main()
    except Exception as err:
        print("[launcher] game start failed:", err)
        raise
