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
    "death_320x240.png",
    "inventory_portrait.png",
    "heart_clean_18.png",
    "heart.png",
    "star_icon_24.png",
    "enemy.png",
    "FLOWEY.png",
    "ANGRY FLOWEY.png",
    "FLOWEY_anim_96.png",
    "ANGRY FLOWEY_anim_96.png",
    "map2_enemy_anim_96.png",
    "map3_enemy_anim_96.png",
    "map4_enemy_anim_96.png",
    "map5_enemy_anim_96.png",
    "fire ball.png",
    "fire ball small.png",
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
    "map2_gloombell_opening_01.png",
    "map2_gloombell_opening_02.png",
    "map2_gloombell_opening_03.png",
    "map2_gloombell_act_watch.png",
    "map2_gloombell_act_call.png",
    "map2_gloombell_act_wait.png",
    "map2_gloombell_look_01.png",
    "map2_gloombell_look_02.png",
    "map2_gloombell_call_01.png",
    "map2_gloombell_call_02.png",
    "map2_gloombell_call_03.png",
    "map2_gloombell_wait_01.png",
    "map2_gloombell_wait_02.png",
    "map2_gloombell_wait_03.png",
    "map2_gloombell_mercy_01.png",
    "map2_gloombell_mercy_02.png",
    "map2_gloombell_mercy_03.png",
    "map3_mimistitch_opening_01.png",
    "map3_mimistitch_opening_02.png",
    "map3_mimistitch_opening_03.png",
    "map3_mimistitch_act_praise.png",
    "map3_mimistitch_act_tidy.png",
    "map3_mimistitch_act_accept.png",
    "map3_mimistitch_praise_01.png",
    "map3_mimistitch_praise_02.png",
    "map3_mimistitch_praise_03.png",
    "map3_mimistitch_tidy_01.png",
    "map3_mimistitch_tidy_02.png",
    "map3_mimistitch_accept_01.png",
    "map3_mimistitch_accept_02.png",
    "map3_mimistitch_accept_03.png",
    "map3_mimistitch_mercy_01.png",
    "map3_mimistitch_mercy_02.png",
    "map3_mimistitch_mercy_03.png",
    "map3_book_dialog_01.png",
    "map3_book_dialog_02.png",
    "map3_book_dialog_03.png",
    "map3_book_dialog_04.png",
    "map4_mushmuse_opening_01.png",
    "map4_mushmuse_opening_02.png",
    "map4_mushmuse_opening_03.png",
    "map4_mushmuse_act_hum.png",
    "map4_mushmuse_act_breath.png",
    "map4_mushmuse_act_share.png",
    "map4_mushmuse_hum_01.png",
    "map4_mushmuse_breath_01.png",
    "map4_mushmuse_share_01.png",
    "map4_mushmuse_share_02.png",
    "map4_mushmuse_mercy_01.png",
    "map4_mushmuse_mercy_02.png",
    "map4_mushmuse_mercy_03.png",
    "map5_cyclobot_opening_01.png",
    "map5_cyclobot_opening_02.png",
    "map5_cyclobot_opening_03.png",
    "map5_cyclobot_act_wave.png",
    "map5_cyclobot_act_explain.png",
    "map5_cyclobot_act_reset.png",
    "map5_cyclobot_wave_01.png",
    "map5_cyclobot_wave_02.png",
    "map5_cyclobot_explain_01.png",
    "map5_cyclobot_explain_02.png",
    "map5_cyclobot_reset_01.png",
    "map5_cyclobot_reset_02.png",
    "map5_cyclobot_mercy_01.png",
    "map5_cyclobot_mercy_02.png",
    "map5_cyclobot_mercy_03.png",
    "map6_crystalgolem_act_observe.png",
    "map6_crystalgolem_act_remember.png",
    "map6_crystalgolem_act_tell.png",
    "map6_crystalgolem_act_touch_core.png",
    "map6_crystalgolem_opening_01.png",
    "map6_crystalgolem_opening_02.png",
    "map6_crystalgolem_opening_03.png",
    "map6_crystalgolem_opening_04.png",
    "map6_crystalgolem_opening_05.png",
    "map6_crystalgolem_opening_06.png",
    "map6_crystalgolem_opening_07.png",
    "map6_crystalgolem_opening_08.png",
    "map6_crystalgolem_opening_09.png",
    "map6_crystalgolem_opening_10.png",
    "map6_crystalgolem_observe_01.png",
    "map6_crystalgolem_observe_02.png",
    "map6_crystalgolem_remember_01.png",
    "map6_crystalgolem_remember_02.png",
    "map6_crystalgolem_remember_03.png",
    "map6_crystalgolem_remember_04.png",
    "map6_crystalgolem_remember_05.png",
    "map6_crystalgolem_remember_06.png",
    "map6_crystalgolem_remember_07.png",
    "map6_crystalgolem_remember_08.png",
    "map6_crystalgolem_tell_01.png",
    "map6_crystalgolem_tell_02.png",
    "map6_crystalgolem_tell_03.png",
    "map6_crystalgolem_tell_04.png",
    "map6_crystalgolem_tell_05.png",
    "map6_crystalgolem_tell_06.png",
    "map6_crystalgolem_touch_core_01.png",
    "map6_crystalgolem_touch_core_02.png",
    "map6_crystalgolem_touch_core_03.png",
    "map6_crystalgolem_touch_core_04.png",
    "map6_crystalgolem_touch_core_05.png",
    "map6_crystalgolem_touch_core_06.png",
    "map6_crystalgolem_touch_core_07.png",
    "map6_crystalgolem_touch_core_08.png",
    "map6_crystalgolem_mercy_01.png",
    "map6_crystalgolem_mercy_02.png",
    "map6_crystalgolem_mercy_03.png",
    "map6_crystalgolem_mercy_04.png",
    "map6_crystalgolem_mercy_05.png",
    "map5_map6_door_locked_dialog.png",
    "map6_boss_battle.png",
    "map9_forest_boss_battle.png",
    "map10_ice_boss_battle.png",
    "map11_fire_boss_battle.png",
    "fight_icon.png",
    "act_icon.png",
    "item_icon.png",
    "item_icon_weapon_knife.png",
    "item_icon_weapon_sword.png",
    "item_icon_item_red_potion.png",
    "item_icon_armor_map3.png",
    "item_icon_weapon_great_sword.png",
    "item_icon_item_small_red_potion.png",
    "item_icon_item_map5_door_key.png",
    "mercy_icon.png",
    "act_dialog_text.png",
    "mercy_dialog_text.png",
    "lamp_dialog_text.png",
    "wood_up_bed_dialog.png",
    "wood_up_mirror_dialog.png",
    "wood_up_bookshelf_dialog.png",
    "wood_main_table_dialog_01.png",
    "wood_main_table_dialog_02.png",
    "wood_main_table_dialog_03.png",
    "wood_left_bathtub_dialog.png",
    "wood_left_toilet_dialog.png",
    "wood_left_plant_dialog.png",
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
