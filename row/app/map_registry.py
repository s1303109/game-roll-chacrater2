import config


MAP1_ID = 1
MAP2_ID = 2
MAP3_ID = 3
WOOD_MAIN_ID = 4
WOOD_UP_ID = 5
WOOD_RIGHT_ID = 6
WOOD_LEFT_ID = 7
MAP4_ID = 8
MAP5_ID = 9
MAP6_ID = 10
MAP7_ID = 11
MAP8_ID = 12
MAP9_ID = 13
MAP10_ID = 14
MAP11_ID = 15


MAP1_PORTAL_TO_MAP2_RECT_PX = (304, 160, 32, 96)
MAP2_PORTAL_TO_MAP1_RECT_PX = (54, 156, 22, 64)
MAP2_PORTAL_TO_WOOD_MAIN_RECT_PX = (842, 176, 30, 84)
MAP1_TO_MAP2_SPAWN = (152, 228)
MAP2_TO_MAP1_SPAWN = (320, 272)
MAP2_PORTAL_TO_MAP3_RECT_PX = (448, 584, 64, 6)
MAP3_PORTAL_TO_MAP2_RECT_PX = (448, 0, 64, 8)
MAP3_PORTAL_TO_MAP4_RECT_PX = (448, 300, 64, 96)
MAP4_PORTAL_TO_MAP3_RECT_PX = (72, 56, 64, 112)
MAP4_PORTAL_TO_MAP5_RECT_PX = (768, 56, 64, 112)
MAP5_PORTAL_TO_MAP4_RECT_PX = (72, 56, 64, 112)
MAP5_PORTAL_TO_MAP6_RECT_PX = (688, 32, 16, 80)
MAP5_PORTAL_TO_MAP7_RECT_PX = (455, 40, 57, 72)
MAP6_PORTAL_TO_MAP5_RECT_PX = (72, 56, 64, 112)
MAP7_PORTAL_TO_MAP5_RECT_PX = (288, 872, 64, 32)
MAP7_PORTAL_TO_MAP8_RECT_PX = (254, 202, 80, 80)
MAP8_PORTAL_TO_MAP7_RECT_PX = (592, 828, 254, 194)
MAP8_PORTAL_TO_MAP9_RECT_PX = (1128, 350, 80, 80)
MAP8_PORTAL_TO_MAP10_RECT_PX = (247, 348, 80, 80)
MAP8_PORTAL_TO_MAP11_RECT_PX = (267, 781, 80, 80)
MAP9_PORTAL_TO_MAP8_RECT_PX = (440, 464, 80, 80)
MAP10_PORTAL_TO_MAP8_RECT_PX = (437, 431, 80, 80)
MAP11_PORTAL_TO_MAP8_RECT_PX = (442, 456, 80, 80)
MAP2_FROM_MAP3_SPAWN_X = 480
MAP2_FROM_MAP3_SPAWN_Y = 590
MAP4_FROM_MAP3_SPAWN = (112, 172)
MAP3_FROM_MAP4_SPAWN = (480, 430)
MAP5_FROM_MAP4_SPAWN = (96, 172)
MAP4_FROM_MAP5_SPAWN = (800, 172)
MAP6_FROM_MAP5_SPAWN = (96, 172)
MAP5_FROM_MAP6_SPAWN = (696, 96)
MAP7_FROM_MAP5_SPAWN = (320, 888)
MAP5_FROM_MAP7_SPAWN = (480, 172)
MAP8_FROM_MAP7_SPAWN = (722, 900)
MAP7_FROM_MAP8_SPAWN = (294, 320)
MAP9_FROM_MAP8_SPAWN = (480, 472)
MAP8_FROM_MAP9_SPAWN = (1167, 436)
MAP10_FROM_MAP8_SPAWN = (477, 423)
MAP8_FROM_MAP10_SPAWN = (287, 436)
MAP11_FROM_MAP8_SPAWN = (482, 448)
MAP8_FROM_MAP11_SPAWN = (307, 869)
WOOD_MAIN_PORTAL_TO_UP_RECT_PX = (144, 0, 32, 24)
WOOD_MAIN_PORTAL_TO_RIGHT_RECT_PX = (296, 106, 24, 36)
WOOD_MAIN_PORTAL_TO_LEFT_RECT_PX = (0, 106, 24, 36)
WOOD_MAIN_PORTAL_TO_MAP2_RECT_PX = (144, 216, 32, 24)
WOOD_UP_PORTAL_TO_MAIN_RECT_PX = (136, 216, 48, 24)
WOOD_RIGHT_PORTAL_TO_MAIN_RECT_PX = (0, 120, 24, 80)
WOOD_LEFT_PORTAL_TO_MAIN_RECT_PX = (296, 120, 24, 80)


def _map_entry(subdir, tileset_id, portals, prefer_stream=True, fallback_all_walkable=False):
    asset_base = config.asset_dir(subdir)
    return {
        "asset_base": asset_base,
        "asset_bases": (asset_base,),
        "map_json": asset_base + "/map.json",
        "tilemap_path": asset_base + "/tilemap.bin",
        "tileset_path": asset_base + "/tileset.bin",
        "collision_path": asset_base + "/collision.bin",
        "tileset_id": tileset_id,
        "prefer_stream": prefer_stream,
        "fallback_all_walkable": fallback_all_walkable,
        "portals": portals,
    }


MAP_REGISTRY = {
    MAP1_ID: _map_entry(
        "out",
        "map1_tileset",
        (
            {
                "rect": MAP1_PORTAL_TO_MAP2_RECT_PX,
                "target_map_id": MAP2_ID,
                "target_spawn": MAP1_TO_MAP2_SPAWN,
            },
        ),
    ),
    MAP2_ID: _map_entry(
        "out_map2",
        "map2_tileset",
        (
            {
                "rect": MAP2_PORTAL_TO_MAP1_RECT_PX,
                "target_map_id": MAP1_ID,
                "target_spawn": MAP2_TO_MAP1_SPAWN,
                "preload_pad_px": 96,
                "entry_move_x_sign": -1,
            },
            {
                "rect": MAP2_PORTAL_TO_MAP3_RECT_PX,
                "target_map_id": MAP3_ID,
                "target_spawn": (480, 116),
                "entry_move_y_sign": 1,
            },
            {
                "rect": MAP2_PORTAL_TO_WOOD_MAIN_RECT_PX,
                "target_map_id": WOOD_MAIN_ID,
                "target_spawn": (160, 206),
                "entry_move_x_sign": 1,
                "preload_pad_px": 96,
            },
        ),
    ),
    MAP3_ID: _map_entry(
        "out_map3",
        "map3_tileset",
        (
            {
                "rect": MAP3_PORTAL_TO_MAP2_RECT_PX,
                "target_map_id": MAP2_ID,
                "target_spawn": (MAP2_FROM_MAP3_SPAWN_X, MAP2_FROM_MAP3_SPAWN_Y),
                "entry_move_y_sign": -1,
            },
            {
                "rect": MAP3_PORTAL_TO_MAP4_RECT_PX,
                "target_map_id": MAP4_ID,
                "target_spawn": MAP4_FROM_MAP3_SPAWN,
                "preload_pad_px": 96,
            },
        ),
    ),
    MAP4_ID: _map_entry(
        "out_map4",
        "map4_tileset",
        (
            {
                "rect": MAP4_PORTAL_TO_MAP3_RECT_PX,
                "target_map_id": MAP3_ID,
                "target_spawn": MAP3_FROM_MAP4_SPAWN,
                "entry_move_y_sign": -1,
                "preload_pad_px": 96,
            },
            {
                "rect": MAP4_PORTAL_TO_MAP5_RECT_PX,
                "target_map_id": MAP5_ID,
                "target_spawn": MAP5_FROM_MAP4_SPAWN,
                "entry_move_y_sign": -1,
                "preload_pad_px": 96,
            },
        ),
    ),
    MAP5_ID: _map_entry(
        "out_map5",
        "map5_tileset",
        (
            {
                "rect": MAP5_PORTAL_TO_MAP4_RECT_PX,
                "target_map_id": MAP4_ID,
                "target_spawn": MAP4_FROM_MAP5_SPAWN,
                "entry_move_y_sign": -1,
                "preload_pad_px": 96,
            },
            {
                "rect": MAP5_PORTAL_TO_MAP6_RECT_PX,
                "target_map_id": MAP6_ID,
                "target_spawn": MAP6_FROM_MAP5_SPAWN,
                "entry_move_y_sign": -1,
                "preload_pad_px": 96,
            },
            {
                "rect": MAP5_PORTAL_TO_MAP7_RECT_PX,
                "target_map_id": MAP7_ID,
                "target_spawn": MAP7_FROM_MAP5_SPAWN,
                "entry_move_y_sign": -1,
                "preload_pad_px": 96,
            },
        ),
    ),
    MAP6_ID: _map_entry(
        "out_map6",
        "map6_tileset",
        (
            {
                "rect": MAP6_PORTAL_TO_MAP5_RECT_PX,
                "target_map_id": MAP5_ID,
                "target_spawn": MAP5_FROM_MAP6_SPAWN,
                "entry_move_y_sign": -1,
                "preload_pad_px": 96,
            },
        ),
    ),
    MAP7_ID: _map_entry(
        "out_map7",
        "map7_tileset",
        (
            {
                "rect": MAP7_PORTAL_TO_MAP5_RECT_PX,
                "target_map_id": MAP5_ID,
                "target_spawn": MAP5_FROM_MAP7_SPAWN,
                "entry_move_y_sign": 1,
                "preload_pad_px": 96,
            },
            {
                "rect": MAP7_PORTAL_TO_MAP8_RECT_PX,
                "target_map_id": MAP8_ID,
                "target_spawn": MAP8_FROM_MAP7_SPAWN,
                "preload_pad_px": 128,
                "trigger_center_px": (295, 241),
                "trigger_radius_px": 20,
                "transition_effect": "spotlight_shrink",
                "transition_shrink_ms": 4000,
                "transition_black_ms": 1000,
            },
        ),
    ),
    MAP8_ID: _map_entry(
        "out_map8",
        "map8_tileset",
        (
            {
                "rect": MAP8_PORTAL_TO_MAP7_RECT_PX,
                "target_map_id": MAP7_ID,
                "target_spawn": MAP7_FROM_MAP8_SPAWN,
                "preload_pad_px": 128,
                "trigger_center_px": (722, 945),
                "trigger_radius_px": 18,
                "transition_effect": "spotlight_shrink",
                "transition_shrink_ms": 4000,
                "transition_black_ms": 1000,
            },
            {
                "rect": MAP8_PORTAL_TO_MAP9_RECT_PX,
                "target_map_id": MAP9_ID,
                "target_spawn": MAP9_FROM_MAP8_SPAWN,
                "preload_pad_px": 128,
                "preload_allow_spotlight": True,
                "trigger_center_px": (1167, 389),
                "trigger_radius_px": 20,
                "transition_effect": "spotlight_shrink",
                "transition_shrink_ms": 4000,
                "transition_black_ms": 1000,
            },
            {
                "rect": MAP8_PORTAL_TO_MAP10_RECT_PX,
                "target_map_id": MAP10_ID,
                "target_spawn": MAP10_FROM_MAP8_SPAWN,
                "preload_pad_px": 128,
                "preload_allow_spotlight": True,
                "trigger_center_px": (287, 388),
                "trigger_radius_px": 20,
                "transition_effect": "spotlight_shrink",
                "transition_shrink_ms": 4000,
                "transition_black_ms": 1000,
            },
            {
                "rect": MAP8_PORTAL_TO_MAP11_RECT_PX,
                "target_map_id": MAP11_ID,
                "target_spawn": MAP11_FROM_MAP8_SPAWN,
                "preload_pad_px": 128,
                "preload_allow_spotlight": True,
                "trigger_center_px": (307, 821),
                "trigger_radius_px": 20,
                "transition_effect": "spotlight_shrink",
                "transition_shrink_ms": 4000,
                "transition_black_ms": 1000,
            },
        ),
    ),
    MAP9_ID: _map_entry(
        "out_map9",
        "map9_tileset",
        (
            {
                "rect": MAP9_PORTAL_TO_MAP8_RECT_PX,
                "target_map_id": MAP8_ID,
                "target_spawn": MAP8_FROM_MAP9_SPAWN,
                "preload_pad_px": 128,
                "preload_allow_spotlight": True,
                "trigger_center_px": (479, 502),
                "trigger_radius_px": 22,
                "transition_effect": "spotlight_shrink",
                "transition_shrink_ms": 4000,
                "transition_black_ms": 1000,
            },
        ),
    ),
    MAP10_ID: _map_entry(
        "out_map10",
        "map10_tileset",
        (
            {
                "rect": MAP10_PORTAL_TO_MAP8_RECT_PX,
                "target_map_id": MAP8_ID,
                "target_spawn": MAP8_FROM_MAP10_SPAWN,
                "preload_pad_px": 128,
                "preload_allow_spotlight": True,
                "trigger_center_px": (477, 471),
                "trigger_radius_px": 20,
                "transition_effect": "spotlight_shrink",
                "transition_shrink_ms": 4000,
                "transition_black_ms": 1000,
            },
        ),
    ),
    MAP11_ID: _map_entry(
        "out_map11",
        "map11_tileset",
        (
            {
                "rect": MAP11_PORTAL_TO_MAP8_RECT_PX,
                "target_map_id": MAP8_ID,
                "target_spawn": MAP8_FROM_MAP11_SPAWN,
                "preload_pad_px": 128,
                "preload_allow_spotlight": True,
                "trigger_center_px": (482, 496),
                "trigger_radius_px": 20,
                "transition_effect": "spotlight_shrink",
                "transition_shrink_ms": 4000,
                "transition_black_ms": 1000,
            },
        ),
    ),
    WOOD_MAIN_ID: _map_entry(
        "out_wood_main",
        "wood_main_tileset",
        (
            {
                "rect": WOOD_MAIN_PORTAL_TO_UP_RECT_PX,
                "target_map_id": WOOD_UP_ID,
                "target_spawn": (160, 206),
                "entry_move_y_sign": -1,
                "preload_pad_px": 40,
            },
            {
                "rect": WOOD_MAIN_PORTAL_TO_RIGHT_RECT_PX,
                "target_map_id": WOOD_RIGHT_ID,
                "target_spawn": (36, 160),
                "entry_move_x_sign": 1,
                "preload_pad_px": 40,
            },
            {
                "rect": WOOD_MAIN_PORTAL_TO_LEFT_RECT_PX,
                "target_map_id": WOOD_LEFT_ID,
                "target_spawn": (284, 160),
                "entry_move_x_sign": -1,
                "preload_pad_px": 40,
            },
            {
                "rect": WOOD_MAIN_PORTAL_TO_MAP2_RECT_PX,
                "target_map_id": MAP2_ID,
                "target_spawn": (824, 248),
                "entry_move_y_sign": 1,
                "preload_pad_px": 48,
            },
        ),
    ),
    WOOD_UP_ID: _map_entry(
        "out_wood_up",
        "wood_up_tileset",
        (
            {
                "rect": WOOD_UP_PORTAL_TO_MAIN_RECT_PX,
                "target_map_id": WOOD_MAIN_ID,
                "target_spawn": (160, 34),
                "entry_move_y_sign": 1,
                "preload_pad_px": 36,
            },
        ),
    ),
    WOOD_RIGHT_ID: _map_entry(
        "out_wood_right",
        "wood_right_tileset",
        (
            {
                "rect": WOOD_RIGHT_PORTAL_TO_MAIN_RECT_PX,
                "target_map_id": WOOD_MAIN_ID,
                "target_spawn": (286, 124),
                "entry_move_x_sign": -1,
                "preload_pad_px": 36,
            },
        ),
    ),
    WOOD_LEFT_ID: _map_entry(
        "out_wood_left",
        "wood_left_tileset",
        (
            {
                "rect": WOOD_LEFT_PORTAL_TO_MAIN_RECT_PX,
                "target_map_id": WOOD_MAIN_ID,
                "target_spawn": (34, 124),
                "entry_move_x_sign": 1,
                "preload_pad_px": 36,
            },
        ),
    ),
}
