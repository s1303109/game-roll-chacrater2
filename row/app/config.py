import os


GAME_ROOT = "/sd/game"
ASSET_ROOT = GAME_ROOT + "/assets"
UI_ROOT = GAME_ROOT + "/ui"
SPRITE_ROOT = GAME_ROOT + "/sprites"
SAVE_ROOT = GAME_ROOT + "/save"

GAME_MVP_PATH = GAME_ROOT + "/game_mvp.py"
CONFIG_PATH = GAME_ROOT + "/config.py"
MAP_REGISTRY_PATH = GAME_ROOT + "/map_registry.py"
SAVE1_PATH = SAVE_ROOT + "/save1.json"

PLAYER_SHEET_NAME = "player_sheet.rgb565"
PLAYER_SHEET_PATH = SPRITE_ROOT + "/" + PLAYER_SHEET_NAME

REQUIRED_UI_FILES = (
    "front_cover_320x240.png",
    "title_ui_start_112x54.png",
    "title_ui_continue_112x54.png",
    "comic_01_320x240.png",
    "comic_02_320x240.png",
    "comic_03_320x240.png",
    "comic_04_320x240.png",
    "comic_05_320x240.png",
    "comic_06_320x240.png",
    "inventory_portrait.png",
    "heart_clean_18.png",
    "heart.png",
    "star_icon_24.png",
    "enemy.png",
    "FLOWEY.png",
    "ANGRY FLOWEY.png",
    "FLOWEY_anim_96.png",
    "ANGRY FLOWEY_anim_96.png",
    "fire ball.png",
    "fire ball_anim_64.png",
    "kind people.png",
    "kind people_anim_96.png",
    "map1_story_line_01.png",
    "map1_story_line_02.png",
    "map1_story_line_03.png",
    "map1_story_line_04.png",
    "map1_story_line_05.png",
    "map1_story_line_06.png",
    "map1_story_line_07.png",
    "map1_story_line_08.png",
    "map1_story_line_09.png",
    "map1_story_line_10.png",
    "map1_story_line_11.png",
    "map1_story_line_12.png",
    "map1_story_line_13.png",
    "map1_story_line_14.png",
    "map1_story_line_15.png",
    "map1_story_line_16.png",
    "map1_story_line_17.png",
    "map1_story_line_18.png",
    "fight_icon.png",
    "act_icon.png",
    "item_icon.png",
    "mercy_icon.png",
    "act_dialog_text.png",
    "mercy_dialog_text.png",
    "lamp_dialog_text.png",
    "act_opt1_text.png",
    "act_opt2_text.png",
    "act_opt3_text.png",
    "act_reply1_text.png",
    "act_reply2_text.png",
    "act_reply3_text.png",
    "mercy_locked_text.png",
)

OPTIONAL_UI_GROUPS = (
    (
        "main character close eyes.clean.png",
        "main character close eyes.orig.png",
    ),
)


def game_path(name):
    return GAME_ROOT + "/" + name


def asset_dir(name):
    return ASSET_ROOT + "/" + name


def ui_path(name):
    return UI_ROOT + "/" + name


def sprite_path(name):
    return SPRITE_ROOT + "/" + name


def _path_exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def _ensure_dir(path):
    cur = ""
    for part in path.split("/"):
        if not part:
            continue
        cur += "/" + part
        try:
            os.stat(cur)
        except OSError:
            os.mkdir(cur)


def ensure_save_dir():
    _ensure_dir(SAVE_ROOT)


def validate_cartridge(map_registry):
    ensure_save_dir()

    required_paths = (
        GAME_MVP_PATH,
        CONFIG_PATH,
        MAP_REGISTRY_PATH,
        PLAYER_SHEET_PATH,
    )
    missing = []
    seen = {}

    def _remember(path):
        if path and path not in seen:
            seen[path] = True
            if not _path_exists(path):
                missing.append(path)

    for path in required_paths:
        _remember(path)

    for name in REQUIRED_UI_FILES:
        _remember(ui_path(name))

    for map_id in map_registry:
        record = map_registry[map_id]
        for key in ("map_json", "tilemap_path", "tileset_path", "collision_path"):
            _remember(record.get(key))

    if missing:
        for path in missing:
            print("[launcher] missing file:", path)
        raise RuntimeError("CARTRIDGE_INVALID")

    return True
