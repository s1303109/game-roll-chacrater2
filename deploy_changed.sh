#!/bin/bash
set -euo pipefail

PORT="${MP_PORT:-/dev/ttyACM0}"
APP_DIR="${APP_DIR:-/workspace/row/app}"
ASSET_ROOT="${ASSET_ROOT:-/workspace/row/assets}"
UI_SRC_DIR="${UI_SRC_DIR:-/workspace}"

if command -v mpremote >/dev/null 2>&1; then
  MPREMOTE=(mpremote)
else
  MPREMOTE=(python -m mpremote)
  export PYTHONPATH="${PYTHONPATH:-/workspace/micropython/tools/mpremote}"
fi

FLASH_FILES=(
  "${APP_DIR}/boot.py:/boot.py"
  "${APP_DIR}/main.py:/main.py"
  "${APP_DIR}/launcher.py:/launcher.py"
  "${APP_DIR}/sd_host.py:/sd_host.py"
)

GAME_FILES=(
  "${APP_DIR}/lgfx.py:/sd/game/lgfx.py"
  "${APP_DIR}/game_mvp.py:/sd/game/game_mvp.py"
  "${APP_DIR}/config.py:/sd/game/config.py"
  "${APP_DIR}/map_registry.py:/sd/game/map_registry.py"
)

MAP_DIRS=(
  "out"
  "out_map2"
  "out_map3"
  "out_map4"
  "out_map5"
  "out_map6"
  "out_map7"
  "out_map8"
  "out_map9"
  "out_map10"
  "out_map11"
  "out_map9_1"
  "out_map11_1"
  "out_end_safe"
  "out_end_normal"
  "out_end_death"
  "out_wood_main"
  "out_wood_up"
  "out_wood_right"
  "out_wood_left"
)

UI_FILE_MAP=(
  "front_cover_320x240.png|front_cover_320x240.png"
  "title_ui_start_112x54.png|title_ui_start_112x54.png"
  "title_ui_continue_112x54.png|title_ui_continue_112x54.png"
  "comic_01_320x240.png|comic_01_320x240.png"
  "comic_02_320x240.png|comic_02_320x240.png"
  "comic_03_320x240.png|comic_03_320x240.png"
  "comic_04_320x240.png|comic_04_320x240.png"
  "comic_05_320x240.png|comic_05_320x240.png"
  "comic_06_320x240.png|comic_06_320x240.png"
  "death_320x240.png|death_320x240.png"
  "ending_safe_320x240.png|ending_safe_320x240.png"
  "ending_normal_320x240.png|ending_normal_320x240.png"
  "ending_death_320x240.png|ending_death_320x240.png"
  "ending_locked_duty_text.png|ending_locked_duty_text.png"
  "inventory_portrait.png|inventory_portrait.png"
  "heart_clean_18.png|heart_clean_18.png"
  "heart.png|heart.png"
  "star_icon_24.png|star_icon_24.png"
  "enemy_clean.png|enemy.png"
  "FLOWEY.png|FLOWEY.png"
  "ANGRY FLOWEY.png|ANGRY FLOWEY.png"
  "FLOWEY_anim_96.png|FLOWEY_anim_96.png"
  "ANGRY FLOWEY_anim_96.png|ANGRY FLOWEY_anim_96.png"
  "map2_enemy_anim_96.png|map2_enemy_anim_96.png"
  "map3_enemy_anim_96.png|map3_enemy_anim_96.png"
  "map4_enemy_anim_96.png|map4_enemy_anim_96.png"
  "map5_enemy_anim_96.png|map5_enemy_anim_96.png"
  "fire ball.png|fire ball.png"
  "fire ball small.png|fire ball small.png"
  "fire ball_anim_64.png|fire ball_anim_64.png"
  "kind people.png|kind people.png"
  "kind people_anim_96.png|kind people_anim_96.png"
  "map1_story_line_01.png|map1_story_line_01.png"
  "map1_story_line_02.png|map1_story_line_02.png"
  "map1_story_line_03.png|map1_story_line_03.png"
  "map1_story_line_04.png|map1_story_line_04.png"
  "map1_story_line_05.png|map1_story_line_05.png"
  "map1_story_line_06.png|map1_story_line_06.png"
  "map1_story_line_07.png|map1_story_line_07.png"
  "map1_story_line_08.png|map1_story_line_08.png"
  "map1_story_line_09.png|map1_story_line_09.png"
  "map1_story_line_10.png|map1_story_line_10.png"
  "map1_story_line_11.png|map1_story_line_11.png"
  "map1_story_line_12.png|map1_story_line_12.png"
  "map1_story_line_13.png|map1_story_line_13.png"
  "map1_story_line_14.png|map1_story_line_14.png"
  "map1_story_line_15.png|map1_story_line_15.png"
  "map1_story_line_16.png|map1_story_line_16.png"
  "map1_story_line_17.png|map1_story_line_17.png"
  "map1_story_line_18.png|map1_story_line_18.png"
  "map2_gloombell_opening_01.png|map2_gloombell_opening_01.png"
  "map2_gloombell_opening_02.png|map2_gloombell_opening_02.png"
  "map2_gloombell_opening_03.png|map2_gloombell_opening_03.png"
  "map2_gloombell_act_watch.png|map2_gloombell_act_watch.png"
  "map2_gloombell_act_call.png|map2_gloombell_act_call.png"
  "map2_gloombell_act_wait.png|map2_gloombell_act_wait.png"
  "map2_gloombell_look_01.png|map2_gloombell_look_01.png"
  "map2_gloombell_look_02.png|map2_gloombell_look_02.png"
  "map2_gloombell_call_01.png|map2_gloombell_call_01.png"
  "map2_gloombell_call_02.png|map2_gloombell_call_02.png"
  "map2_gloombell_call_03.png|map2_gloombell_call_03.png"
  "map2_gloombell_wait_01.png|map2_gloombell_wait_01.png"
  "map2_gloombell_wait_02.png|map2_gloombell_wait_02.png"
  "map2_gloombell_wait_03.png|map2_gloombell_wait_03.png"
  "map2_gloombell_mercy_01.png|map2_gloombell_mercy_01.png"
  "map2_gloombell_mercy_02.png|map2_gloombell_mercy_02.png"
  "map2_gloombell_mercy_03.png|map2_gloombell_mercy_03.png"
  "map3_mimistitch_opening_01.png|map3_mimistitch_opening_01.png"
  "map3_mimistitch_opening_02.png|map3_mimistitch_opening_02.png"
  "map3_mimistitch_opening_03.png|map3_mimistitch_opening_03.png"
  "map3_mimistitch_act_praise.png|map3_mimistitch_act_praise.png"
  "map3_mimistitch_act_tidy.png|map3_mimistitch_act_tidy.png"
  "map3_mimistitch_act_accept.png|map3_mimistitch_act_accept.png"
  "map3_mimistitch_praise_01.png|map3_mimistitch_praise_01.png"
  "map3_mimistitch_praise_02.png|map3_mimistitch_praise_02.png"
  "map3_mimistitch_praise_03.png|map3_mimistitch_praise_03.png"
  "map3_mimistitch_tidy_01.png|map3_mimistitch_tidy_01.png"
  "map3_mimistitch_tidy_02.png|map3_mimistitch_tidy_02.png"
  "map3_mimistitch_accept_01.png|map3_mimistitch_accept_01.png"
  "map3_mimistitch_accept_02.png|map3_mimistitch_accept_02.png"
  "map3_mimistitch_accept_03.png|map3_mimistitch_accept_03.png"
  "map3_mimistitch_mercy_01.png|map3_mimistitch_mercy_01.png"
  "map3_mimistitch_mercy_02.png|map3_mimistitch_mercy_02.png"
  "map3_mimistitch_mercy_03.png|map3_mimistitch_mercy_03.png"
  "map3_book_dialog_01.png|map3_book_dialog_01.png"
  "map3_book_dialog_02.png|map3_book_dialog_02.png"
  "map3_book_dialog_03.png|map3_book_dialog_03.png"
  "map3_book_dialog_04.png|map3_book_dialog_04.png"
  "map4_mushmuse_opening_01.png|map4_mushmuse_opening_01.png"
  "map4_mushmuse_opening_02.png|map4_mushmuse_opening_02.png"
  "map4_mushmuse_opening_03.png|map4_mushmuse_opening_03.png"
  "map4_mushmuse_act_hum.png|map4_mushmuse_act_hum.png"
  "map4_mushmuse_act_breath.png|map4_mushmuse_act_breath.png"
  "map4_mushmuse_act_share.png|map4_mushmuse_act_share.png"
  "map4_mushmuse_hum_01.png|map4_mushmuse_hum_01.png"
  "map4_mushmuse_breath_01.png|map4_mushmuse_breath_01.png"
  "map4_mushmuse_share_01.png|map4_mushmuse_share_01.png"
  "map4_mushmuse_share_02.png|map4_mushmuse_share_02.png"
  "map4_mushmuse_mercy_01.png|map4_mushmuse_mercy_01.png"
  "map4_mushmuse_mercy_02.png|map4_mushmuse_mercy_02.png"
  "map4_mushmuse_mercy_03.png|map4_mushmuse_mercy_03.png"
  "map5_cyclobot_opening_01.png|map5_cyclobot_opening_01.png"
  "map5_cyclobot_opening_02.png|map5_cyclobot_opening_02.png"
  "map5_cyclobot_opening_03.png|map5_cyclobot_opening_03.png"
  "map5_cyclobot_act_wave.png|map5_cyclobot_act_wave.png"
  "map5_cyclobot_act_explain.png|map5_cyclobot_act_explain.png"
  "map5_cyclobot_act_reset.png|map5_cyclobot_act_reset.png"
  "map5_cyclobot_wave_01.png|map5_cyclobot_wave_01.png"
  "map5_cyclobot_wave_02.png|map5_cyclobot_wave_02.png"
  "map5_cyclobot_explain_01.png|map5_cyclobot_explain_01.png"
  "map5_cyclobot_explain_02.png|map5_cyclobot_explain_02.png"
  "map5_cyclobot_reset_01.png|map5_cyclobot_reset_01.png"
  "map5_cyclobot_reset_02.png|map5_cyclobot_reset_02.png"
  "map5_cyclobot_mercy_01.png|map5_cyclobot_mercy_01.png"
  "map5_cyclobot_mercy_02.png|map5_cyclobot_mercy_02.png"
  "map5_cyclobot_mercy_03.png|map5_cyclobot_mercy_03.png"
  "map6_crystalgolem_act_observe.png|map6_crystalgolem_act_observe.png"
  "map6_crystalgolem_act_remember.png|map6_crystalgolem_act_remember.png"
  "map6_crystalgolem_act_tell.png|map6_crystalgolem_act_tell.png"
  "map6_crystalgolem_act_touch_core.png|map6_crystalgolem_act_touch_core.png"
  "map6_crystalgolem_opening_01.png|map6_crystalgolem_opening_01.png"
  "map6_crystalgolem_opening_02.png|map6_crystalgolem_opening_02.png"
  "map6_crystalgolem_opening_03.png|map6_crystalgolem_opening_03.png"
  "map6_crystalgolem_opening_04.png|map6_crystalgolem_opening_04.png"
  "map6_crystalgolem_opening_05.png|map6_crystalgolem_opening_05.png"
  "map6_crystalgolem_opening_06.png|map6_crystalgolem_opening_06.png"
  "map6_crystalgolem_opening_07.png|map6_crystalgolem_opening_07.png"
  "map6_crystalgolem_opening_08.png|map6_crystalgolem_opening_08.png"
  "map6_crystalgolem_opening_09.png|map6_crystalgolem_opening_09.png"
  "map6_crystalgolem_opening_10.png|map6_crystalgolem_opening_10.png"
  "map6_crystalgolem_observe_01.png|map6_crystalgolem_observe_01.png"
  "map6_crystalgolem_observe_02.png|map6_crystalgolem_observe_02.png"
  "map6_crystalgolem_remember_01.png|map6_crystalgolem_remember_01.png"
  "map6_crystalgolem_remember_02.png|map6_crystalgolem_remember_02.png"
  "map6_crystalgolem_remember_03.png|map6_crystalgolem_remember_03.png"
  "map6_crystalgolem_remember_04.png|map6_crystalgolem_remember_04.png"
  "map6_crystalgolem_remember_05.png|map6_crystalgolem_remember_05.png"
  "map6_crystalgolem_remember_06.png|map6_crystalgolem_remember_06.png"
  "map6_crystalgolem_remember_07.png|map6_crystalgolem_remember_07.png"
  "map6_crystalgolem_remember_08.png|map6_crystalgolem_remember_08.png"
  "map6_crystalgolem_tell_01.png|map6_crystalgolem_tell_01.png"
  "map6_crystalgolem_tell_02.png|map6_crystalgolem_tell_02.png"
  "map6_crystalgolem_tell_03.png|map6_crystalgolem_tell_03.png"
  "map6_crystalgolem_tell_04.png|map6_crystalgolem_tell_04.png"
  "map6_crystalgolem_tell_05.png|map6_crystalgolem_tell_05.png"
  "map6_crystalgolem_tell_06.png|map6_crystalgolem_tell_06.png"
  "map6_crystalgolem_touch_core_01.png|map6_crystalgolem_touch_core_01.png"
  "map6_crystalgolem_touch_core_02.png|map6_crystalgolem_touch_core_02.png"
  "map6_crystalgolem_touch_core_03.png|map6_crystalgolem_touch_core_03.png"
  "map6_crystalgolem_touch_core_04.png|map6_crystalgolem_touch_core_04.png"
  "map6_crystalgolem_touch_core_05.png|map6_crystalgolem_touch_core_05.png"
  "map6_crystalgolem_touch_core_06.png|map6_crystalgolem_touch_core_06.png"
  "map6_crystalgolem_touch_core_07.png|map6_crystalgolem_touch_core_07.png"
  "map6_crystalgolem_touch_core_08.png|map6_crystalgolem_touch_core_08.png"
  "map6_crystalgolem_mercy_01.png|map6_crystalgolem_mercy_01.png"
  "map6_crystalgolem_mercy_02.png|map6_crystalgolem_mercy_02.png"
  "map6_crystalgolem_mercy_03.png|map6_crystalgolem_mercy_03.png"
  "map6_crystalgolem_mercy_04.png|map6_crystalgolem_mercy_04.png"
  "map6_crystalgolem_mercy_05.png|map6_crystalgolem_mercy_05.png"
  "map9_mossidol_act_observe.png|map9_mossidol_act_observe.png"
  "map9_mossidol_act_clean_moss.png|map9_mossidol_act_clean_moss.png"
  "map9_mossidol_act_remember.png|map9_mossidol_act_remember.png"
  "map9_mossidol_act_whisper.png|map9_mossidol_act_whisper.png"
  "map9_mossidol_opening_01.png|map9_mossidol_opening_01.png"
  "map9_mossidol_opening_02.png|map9_mossidol_opening_02.png"
  "map9_mossidol_opening_03.png|map9_mossidol_opening_03.png"
  "map9_mossidol_opening_04.png|map9_mossidol_opening_04.png"
  "map9_mossidol_opening_05.png|map9_mossidol_opening_05.png"
  "map9_mossidol_observe_01.png|map9_mossidol_observe_01.png"
  "map9_mossidol_observe_02.png|map9_mossidol_observe_02.png"
  "map9_mossidol_observe_03.png|map9_mossidol_observe_03.png"
  "map9_mossidol_clean_moss_01.png|map9_mossidol_clean_moss_01.png"
  "map9_mossidol_clean_moss_02.png|map9_mossidol_clean_moss_02.png"
  "map9_mossidol_clean_moss_03.png|map9_mossidol_clean_moss_03.png"
  "map9_mossidol_remember_01.png|map9_mossidol_remember_01.png"
  "map9_mossidol_remember_02.png|map9_mossidol_remember_02.png"
  "map9_mossidol_remember_03.png|map9_mossidol_remember_03.png"
  "map9_mossidol_remember_04.png|map9_mossidol_remember_04.png"
  "map9_mossidol_whisper_01.png|map9_mossidol_whisper_01.png"
  "map9_mossidol_whisper_02.png|map9_mossidol_whisper_02.png"
  "map9_mossidol_whisper_03.png|map9_mossidol_whisper_03.png"
  "map9_mossidol_mercy_01.png|map9_mossidol_mercy_01.png"
  "map9_mossidol_mercy_02.png|map9_mossidol_mercy_02.png"
  "map9_mossidol_mercy_03.png|map9_mossidol_mercy_03.png"
  "map9_mossidol_mercy_04.png|map9_mossidol_mercy_04.png"
  "map10_iceguardian_act_observe.png|map10_iceguardian_act_observe.png"
  "map10_iceguardian_act_listen.png|map10_iceguardian_act_listen.png"
  "map10_iceguardian_act_touch_crystal.png|map10_iceguardian_act_touch_crystal.png"
  "map10_iceguardian_act_tell.png|map10_iceguardian_act_tell.png"
  "map10_iceguardian_opening_01.png|map10_iceguardian_opening_01.png"
  "map10_iceguardian_opening_02.png|map10_iceguardian_opening_02.png"
  "map10_iceguardian_opening_03.png|map10_iceguardian_opening_03.png"
  "map10_iceguardian_opening_04.png|map10_iceguardian_opening_04.png"
  "map10_iceguardian_opening_05.png|map10_iceguardian_opening_05.png"
  "map10_iceguardian_observe_01.png|map10_iceguardian_observe_01.png"
  "map10_iceguardian_observe_02.png|map10_iceguardian_observe_02.png"
  "map10_iceguardian_observe_03.png|map10_iceguardian_observe_03.png"
  "map10_iceguardian_listen_01.png|map10_iceguardian_listen_01.png"
  "map10_iceguardian_listen_02.png|map10_iceguardian_listen_02.png"
  "map10_iceguardian_listen_03.png|map10_iceguardian_listen_03.png"
  "map10_iceguardian_touch_crystal_01.png|map10_iceguardian_touch_crystal_01.png"
  "map10_iceguardian_touch_crystal_02.png|map10_iceguardian_touch_crystal_02.png"
  "map10_iceguardian_touch_crystal_03.png|map10_iceguardian_touch_crystal_03.png"
  "map10_iceguardian_touch_crystal_04.png|map10_iceguardian_touch_crystal_04.png"
  "map10_iceguardian_tell_01.png|map10_iceguardian_tell_01.png"
  "map10_iceguardian_tell_02.png|map10_iceguardian_tell_02.png"
  "map10_iceguardian_tell_03.png|map10_iceguardian_tell_03.png"
  "map10_iceguardian_mercy_01.png|map10_iceguardian_mercy_01.png"
  "map10_iceguardian_mercy_02.png|map10_iceguardian_mercy_02.png"
  "map10_iceguardian_mercy_03.png|map10_iceguardian_mercy_03.png"
  "map10_iceguardian_mercy_04.png|map10_iceguardian_mercy_04.png"
  "map11_lavabrute_act_observe.png|map11_lavabrute_act_observe.png"
  "map11_lavabrute_act_endure.png|map11_lavabrute_act_endure.png"
  "map11_lavabrute_act_approach.png|map11_lavabrute_act_approach.png"
  "map11_lavabrute_act_calm.png|map11_lavabrute_act_calm.png"
  "map11_lavabrute_opening_01.png|map11_lavabrute_opening_01.png"
  "map11_lavabrute_opening_02.png|map11_lavabrute_opening_02.png"
  "map11_lavabrute_opening_03.png|map11_lavabrute_opening_03.png"
  "map11_lavabrute_opening_04.png|map11_lavabrute_opening_04.png"
  "map11_lavabrute_opening_05.png|map11_lavabrute_opening_05.png"
  "map11_lavabrute_observe_01.png|map11_lavabrute_observe_01.png"
  "map11_lavabrute_observe_02.png|map11_lavabrute_observe_02.png"
  "map11_lavabrute_observe_03.png|map11_lavabrute_observe_03.png"
  "map11_lavabrute_endure_01.png|map11_lavabrute_endure_01.png"
  "map11_lavabrute_endure_02.png|map11_lavabrute_endure_02.png"
  "map11_lavabrute_endure_03.png|map11_lavabrute_endure_03.png"
  "map11_lavabrute_approach_01.png|map11_lavabrute_approach_01.png"
  "map11_lavabrute_approach_02.png|map11_lavabrute_approach_02.png"
  "map11_lavabrute_approach_03.png|map11_lavabrute_approach_03.png"
  "map11_lavabrute_approach_04.png|map11_lavabrute_approach_04.png"
  "map11_lavabrute_calm_01.png|map11_lavabrute_calm_01.png"
  "map11_lavabrute_calm_02.png|map11_lavabrute_calm_02.png"
  "map11_lavabrute_calm_03.png|map11_lavabrute_calm_03.png"
  "map11_lavabrute_mercy_01.png|map11_lavabrute_mercy_01.png"
  "map11_lavabrute_mercy_02.png|map11_lavabrute_mercy_02.png"
  "map11_lavabrute_mercy_03.png|map11_lavabrute_mercy_03.png"
  "map11_lavabrute_mercy_04.png|map11_lavabrute_mercy_04.png"
  "map5_map6_door_locked_dialog.png|map5_map6_door_locked_dialog.png"
  "fight_icon.png|fight_icon.png"
  "act_icon.png|act_icon.png"
  "item_icon.png|item_icon.png"
  "item_icon_weapon_knife.png|item_icon_weapon_knife.png"
  "item_icon_weapon_sword.png|item_icon_weapon_sword.png"
  "item_icon_item_red_potion.png|item_icon_item_red_potion.png"
  "item_icon_armor_map3.png|item_icon_armor_map3.png"
  "item_icon_weapon_great_sword.png|item_icon_weapon_great_sword.png"
  "item_icon_item_small_red_potion.png|item_icon_item_small_red_potion.png"
  "item_icon_item_map5_door_key.png|item_icon_item_map5_door_key.png"
  "item_icon_item_map7_gate_key.png|item_icon_item_map7_gate_key.png"
  "mercy_icon.png|mercy_icon.png"
  "act_dialog_text.png|act_dialog_text.png"
  "mercy_dialog_text.png|mercy_dialog_text.png"
  "lamp_dialog_text.png|lamp_dialog_text.png"
  "wood_up_bed_dialog.png|wood_up_bed_dialog.png"
  "wood_up_mirror_dialog.png|wood_up_mirror_dialog.png"
  "wood_up_bookshelf_dialog.png|wood_up_bookshelf_dialog.png"
  "wood_left_bathtub_dialog.png|wood_left_bathtub_dialog.png"
  "wood_left_toilet_dialog.png|wood_left_toilet_dialog.png"
  "wood_left_plant_dialog.png|wood_left_plant_dialog.png"
  "act_opt1_text.png|act_opt1_text.png"
  "act_opt2_text.png|act_opt2_text.png"
  "act_opt3_text.png|act_opt3_text.png"
  "act_reply1_text.png|act_reply1_text.png"
  "act_reply2_text.png|act_reply2_text.png"
  "act_reply3_text.png|act_reply3_text.png"
  "mercy_locked_text.png|mercy_locked_text.png"
  "map6_boss_battle.png|map6_boss_battle.png"
  "map9_forest_boss_battle.png|map9_forest_boss_battle.png"
  "map10_ice_boss_battle.png|map10_ice_boss_battle.png"
  "map11_fire_boss_battle.png|map11_fire_boss_battle.png"
  "main character close eyes.clean.png|main character close eyes.clean.png"
  "main character close eyes.orig.png|main character close eyes.orig.png"
)

run_mpremote() {
  "${MPREMOTE[@]}" "$@"
}

run_mpremote_with_sd() {
  run_mpremote connect "$PORT" exec "from sd_host import mount_sd; mount_sd('/sd', return_ok=True)" "$@"
}

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

copy_with_fallback() {
  local src="$1"
  local remote="$2"
  local label="${3:-$2}"

  if [[ "$remote" == /sd/* ]]; then
    if run_mpremote_with_sd fs cp "$src" ":$remote"; then
      sleep 0.5
      return 0
    fi
  else
    if run_mpremote connect "$PORT" fs cp "$src" ":$remote"; then
      sleep 0.5
      return 0
    fi
  fi

  echo "fs cp failed for ${label}; fallback to SerialTransport.fs_writefile chunked..."
  python - "$PORT" "$src" "$remote" <<'PY'
import os
import sys

port, src, remote = sys.argv[1], sys.argv[2], sys.argv[3]
repo_mpremote = "/workspace/micropython/tools/mpremote"
if repo_mpremote not in sys.path:
    sys.path.insert(0, repo_mpremote)

from mpremote.transport_serial import SerialTransport

t = SerialTransport(port, baudrate=115200)
try:
    t.enter_raw_repl(soft_reset=False)
    if remote.startswith("/sd/"):
        t.exec("from sd_host import mount_sd\nmount_sd('/sd', return_ok=True)")
    with open(src, "rb") as f:
        data = f.read()
    t.fs_writefile(remote, data, chunk_size=1024)
finally:
    try:
        if t.in_raw_repl:
            t.exit_raw_repl()
    finally:
        t.close()

print("fallback_chunk_write_ok:", remote, "bytes:", os.path.getsize(src))
PY
  sleep 0.5
}

verify_required_sources() {
  local spec src dir name

  for spec in "${FLASH_FILES[@]}" "${GAME_FILES[@]}"; do
    src="${spec%%:*}"
    [[ -f "$src" ]] || fail "Missing required source: $src"
  done

  [[ -f "${ASSET_ROOT}/out/player_sheet.rgb565" ]] || fail "Missing sprite source: ${ASSET_ROOT}/out/player_sheet.rgb565"
  [[ -f "${ASSET_ROOT}/out/map6_boss_sheet.rgb565" ]] || fail "Missing sprite source: ${ASSET_ROOT}/out/map6_boss_sheet.rgb565"
  [[ -f "${ASSET_ROOT}/out/map9_forest_boss_sheet.rgb565" ]] || fail "Missing sprite source: ${ASSET_ROOT}/out/map9_forest_boss_sheet.rgb565"
  [[ -f "${ASSET_ROOT}/out/map10_ice_boss_sheet.rgb565" ]] || fail "Missing sprite source: ${ASSET_ROOT}/out/map10_ice_boss_sheet.rgb565"
  [[ -f "${ASSET_ROOT}/out/map11_fire_boss_sheet.rgb565" ]] || fail "Missing sprite source: ${ASSET_ROOT}/out/map11_fire_boss_sheet.rgb565"

  for dir in "${MAP_DIRS[@]}"; do
    for name in map.json tilemap.bin tileset.bin collision.bin; do
      [[ -f "${ASSET_ROOT}/${dir}/${name}" ]] || fail "Missing map asset: ${ASSET_ROOT}/${dir}/${name}"
    done
  done

  for spec in "${UI_FILE_MAP[@]}"; do
    src="${spec%%|*}"
    [[ -f "${UI_SRC_DIR}/${src}" ]] || fail "Missing UI asset: ${UI_SRC_DIR}/${src}"
  done
}

check_psram_firmware() {
  local py
  py=$(cat <<'PY'
import gc
import sys

build = getattr(sys.implementation, "_build", "")
mem_free = gc.mem_free()
print("fw_build:", build)
print("fw_mem_free:", mem_free)
if "SPIRAM_OCT" not in build:
    print("[ERROR] PSRAM_BUILD_MISMATCH: firmware is not SPIRAM_OCT.")
    print("[ERROR] build =", build)
    raise RuntimeError("PSRAM_BUILD_MISMATCH")
if mem_free < 3_000_000:
    print("[ERROR] PSRAM_MEM_TOO_LOW: gc.mem_free() is below 3000000, this is likely not the expected PSRAM heap configuration.")
    print("[ERROR] mem_free =", mem_free)
    raise RuntimeError("PSRAM_MEM_TOO_LOW")
PY
)
  run_mpremote connect "$PORT" exec "$py"
  sleep 0.5
}

check_sd_capacity_32gb() {
  local py
  py=$(cat <<'PY'
from sd_host import ensure_sd_32gb, mount_sd, sd_capacity_bytes

if not mount_sd("/sd", return_ok=True):
    raise RuntimeError("SD_MOUNT_FAILED")

cap, source = ensure_sd_32gb("/sd")
print("sd_capacity_ok:", cap, "source:", source)
probe_cap, probe_source = sd_capacity_bytes("/sd")
print("sd_capacity_probe:", probe_cap, "source:", probe_source)
PY
)
  run_mpremote connect "$PORT" exec "$py"
  sleep 0.5
}

local_sha256() {
  sha256sum "$1" | awk '{print $1}'
}

remote_meta_hash() {
  local remote="$1"
  local py out
  py=$(cat <<PY
import os
try:
  import hashlib
except ImportError:
  hashlib = None
try:
  import ubinascii as binascii
except ImportError:
  import binascii
name = ${remote@Q}
try:
  size = os.stat(name)[6]
except OSError:
  print("-1 missing")
else:
  if hashlib is None or not hasattr(hashlib, "sha256"):
    print("%d nohash" % size)
  else:
    h = hashlib.sha256()
    with open(name, "rb") as f:
      while True:
        b = f.read(4096)
        if not b:
          break
        h.update(b)
    print("%d %s" % (size, binascii.hexlify(h.digest()).decode()))
PY
)
  if [[ "$remote" == /sd/* ]]; then
    out="$(run_mpremote_with_sd exec "$py")" || return 1
  else
    out="$(run_mpremote connect "$PORT" exec "$py")" || return 1
  fi
  sleep 0.5
  printf '%s\n' "$out" | tail -n 1 | tr -d '\r'
}

copy_if_changed() {
  local src="$1"
  local remote="$2"
  local label="${3:-$2}"
  local lsize lhash rmeta rsize rhash

  [[ -f "$src" ]] || fail "Local file not found: $src"

  lsize="$(stat -c%s "$src")"
  lhash="$(local_sha256 "$src")"
  rmeta="$(remote_meta_hash "$remote")" || fail "Failed to read remote metadata for $remote"
  rsize="$(printf '%s' "$rmeta" | awk '{print $1}')"
  rhash="$(printf '%s' "$rmeta" | awk '{print $2}')"

  if [[ "$rsize" == "$lsize" && "$rhash" == "$lhash" ]]; then
    echo "Skipping ${label} -> ${remote}"
    return
  fi

  echo "Copying ${label} -> ${remote}"
  copy_with_fallback "$src" "$remote" "$label"
}

copy_flash_files() {
  local spec src dst
  for spec in "${FLASH_FILES[@]}"; do
    src="${spec%%:*}"
    dst="${spec#*:}"
    copy_if_changed "$src" "$dst" "$dst"
  done
}

prepare_device() {
  local py
  py=$(cat <<'PY'
import os
from sd_host import ensure_sd_32gb, mount_sd

STALE_FLASH_FILES = (
    "/lgfx.py",
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
    "/FLOWEY_anim_96.png",
    "/ANGRY FLOWEY_anim_96.png",
    "/fire ball.png",
    "/fire ball small.png",
    "/fire ball_anim_64.png",
    "/kind people.png",
    "/kind people_anim_96.png",
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
    "/map1_story_line_11.png",
    "/map1_story_line_12.png",
    "/map1_story_line_13.png",
    "/map1_story_line_14.png",
    "/map1_story_line_15.png",
    "/map1_story_line_16.png",
    "/map1_story_line_17.png",
    "/map1_story_line_18.png",
    "/map2_gloombell_opening_01.png",
    "/map2_gloombell_opening_02.png",
    "/map2_gloombell_opening_03.png",
    "/map2_gloombell_act_watch.png",
    "/map2_gloombell_act_call.png",
    "/map2_gloombell_act_wait.png",
    "/map2_gloombell_look_01.png",
    "/map2_gloombell_look_02.png",
    "/map2_gloombell_call_01.png",
    "/map2_gloombell_call_02.png",
    "/map2_gloombell_call_03.png",
    "/map2_gloombell_wait_01.png",
    "/map2_gloombell_wait_02.png",
    "/map2_gloombell_wait_03.png",
    "/map2_gloombell_mercy_01.png",
    "/map2_gloombell_mercy_02.png",
    "/map2_gloombell_mercy_03.png",
    "/map4_mushmuse_opening_01.png",
    "/map4_mushmuse_opening_02.png",
    "/map4_mushmuse_opening_03.png",
    "/map4_mushmuse_act_hum.png",
    "/map4_mushmuse_act_breath.png",
    "/map4_mushmuse_act_share.png",
    "/map4_mushmuse_hum_01.png",
    "/map4_mushmuse_breath_01.png",
    "/map4_mushmuse_share_01.png",
    "/map4_mushmuse_share_02.png",
    "/map4_mushmuse_mercy_01.png",
    "/map4_mushmuse_mercy_02.png",
    "/map4_mushmuse_mercy_03.png",
    "/fight_icon.png",
    "/act_icon.png",
    "/item_icon.png",
    "/mercy_icon.png",
    "/act_dialog_text.png",
    "/mercy_dialog_text.png",
    "/lamp_dialog_text.png",
    "/wood_up_bed_dialog.png",
    "/wood_up_mirror_dialog.png",
    "/wood_up_bookshelf_dialog.png",
    "/wood_left_bathtub_dialog.png",
    "/wood_left_toilet_dialog.png",
    "/wood_left_plant_dialog.png",
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


def exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def ensure_dir(path):
    cur = ""
    for part in path.split("/"):
        if not part:
            continue
        cur += "/" + part
        try:
            os.stat(cur)
        except OSError:
            os.mkdir(cur)

if not mount_sd("/sd", return_ok=True):
    raise RuntimeError("SD_MOUNT_FAILED")
ensure_sd_32gb("/sd")

for path in (
    "/sd/game",
    "/sd/game/assets",
    "/sd/game/assets/out",
    "/sd/game/assets/out_map2",
    "/sd/game/assets/out_map3",
    "/sd/game/assets/out_map4",
    "/sd/game/assets/out_map5",
    "/sd/game/assets/out_map6",
    "/sd/game/assets/out_map7",
    "/sd/game/assets/out_map8",
    "/sd/game/assets/out_map9",
    "/sd/game/assets/out_map10",
    "/sd/game/assets/out_map11",
    "/sd/game/assets/out_map9_1",
    "/sd/game/assets/out_map11_1",
    "/sd/game/assets/out_end_safe",
    "/sd/game/assets/out_end_normal",
    "/sd/game/assets/out_end_death",
    "/sd/game/assets/out_wood_main",
    "/sd/game/assets/out_wood_up",
    "/sd/game/assets/out_wood_right",
    "/sd/game/assets/out_wood_left",
    "/sd/game/ui",
    "/sd/game/sprites",
    "/sd/game/save",
):
    ensure_dir(path)

for path in STALE_FLASH_FILES:
    try:
        os.remove(path)
        print("removed stale:", path)
    except OSError:
        if exists(path):
            print("stale ignored:", path)

print("device_ready")
PY
)
  run_mpremote connect "$PORT" exec "$py"
  sleep 0.5
}

copy_game_files() {
  local spec src dst dir name src_name dst_name

  for spec in "${GAME_FILES[@]}"; do
    src="${spec%%:*}"
    dst="${spec#*:}"
    copy_if_changed "$src" "$dst" "$dst"
  done

  copy_if_changed "${ASSET_ROOT}/out/player_sheet.rgb565" "/sd/game/sprites/player_sheet.rgb565" "/sd/game/sprites/player_sheet.rgb565"
  copy_if_changed "${ASSET_ROOT}/out/map6_boss_sheet.rgb565" "/sd/game/sprites/map6_boss_sheet.rgb565" "/sd/game/sprites/map6_boss_sheet.rgb565"
  copy_if_changed "${ASSET_ROOT}/out/map9_forest_boss_sheet.rgb565" "/sd/game/sprites/map9_forest_boss_sheet.rgb565" "/sd/game/sprites/map9_forest_boss_sheet.rgb565"
  copy_if_changed "${ASSET_ROOT}/out/map10_ice_boss_sheet.rgb565" "/sd/game/sprites/map10_ice_boss_sheet.rgb565" "/sd/game/sprites/map10_ice_boss_sheet.rgb565"
  copy_if_changed "${ASSET_ROOT}/out/map11_fire_boss_sheet.rgb565" "/sd/game/sprites/map11_fire_boss_sheet.rgb565" "/sd/game/sprites/map11_fire_boss_sheet.rgb565"

  for dir in "${MAP_DIRS[@]}"; do
    for name in map.json tilemap.bin tileset.bin collision.bin; do
      copy_if_changed "${ASSET_ROOT}/${dir}/${name}" "/sd/game/assets/${dir}/${name}" "/sd/game/assets/${dir}/${name}"
    done
  done

  for spec in "${UI_FILE_MAP[@]}"; do
    src_name="${spec%%|*}"
    dst_name="${spec#*|}"
    copy_if_changed "${UI_SRC_DIR}/${src_name}" "/sd/game/ui/${dst_name}" "/sd/game/ui/${dst_name}"
  done
}

run_game() {
  echo "Resetting board to boot launcher..."
  run_mpremote connect "$PORT" reset
}

verify_required_sources
copy_flash_files
check_psram_firmware
check_sd_capacity_32gb
prepare_device
copy_game_files
run_game

echo "Deploy (changed only) succeeded."
