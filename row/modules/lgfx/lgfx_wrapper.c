#include "py/obj.h"
#include "py/runtime.h"
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif
void lgfx_init_impl(void);
void lgfx_fill_impl(uint16_t color);
void lgfx_draw_text_impl(int x, int y, const char *text, uint16_t color);
void lgfx_draw_rect_impl(int x, int y, int w, int h, uint16_t color);
void lgfx_draw_circle_impl(int x, int y, int r, uint16_t color);
void lgfx_clear_impl(void);
void lgfx_set_rotation_impl(int rotation);
void lgfx_set_brightness_impl(int brightness);
void lgfx_set_swap_bytes_impl(bool swap);
void lgfx_sprite_create_impl(int w, int h, bool use_psram);
void lgfx_sprite_fill_impl(uint16_t color);
void lgfx_sprite_push_impl(int x, int y);
bool lgfx_tile_setup_impl(int tile_size, int map_w, int map_h, int view_w, int view_h, bool use_psram);
bool lgfx_tile_load_impl(const uint8_t *tileset_data, size_t tileset_len, const uint8_t *tilemap_data, size_t tilemap_len);
bool lgfx_tile_load_files_impl(const char *tileset_path, const char *tilemap_path);
int lgfx_tile_loader_mode_impl(void);
int lgfx_tile_last_error_impl(void);
bool lgfx_slot_load_files_impl(int slot_id, uint32_t map_token, uint32_t tileset_token, const char *tileset_path, const char *tilemap_path, int tile_size, int map_w, int map_h);
bool lgfx_slot_begin_load_files_impl(int slot_id, uint32_t map_token, uint32_t tileset_token, const char *tileset_path, const char *tilemap_path, int tile_size, int map_w, int map_h);
int lgfx_slot_pump_load_impl(int slot_id, size_t max_bytes);
bool lgfx_slot_cancel_load_impl(int slot_id);
bool lgfx_slot_select_impl(int slot_id, bool force_full_redraw);
bool lgfx_slot_release_impl(int slot_id);
bool lgfx_slot_has_map_impl(int slot_id, uint32_t map_token);
bool lgfx_slot_info_impl(int slot_id, int *role, int *state, uint32_t *map_token, uint32_t *tileset_token, int *load_stage, size_t *loaded_bytes, size_t *total_bytes, int *ref_count, int *waiter_count, bool *is_active);
void lgfx_slot_set_role_impl(int slot_id, int role);
void lgfx_display_wait_idle_impl(void);
bool lgfx_tile_set_impl(int tx, int ty, int tile_index);
int lgfx_tile_render_impl(int scroll_x, int scroll_y, bool force_full);
int lgfx_tile_render_player_impl(int scroll_x, int scroll_y, int player_x, int player_y, uint16_t color, int radius, bool force_full);
void lgfx_draw_player_impl(int x, int y, uint16_t color, int radius);
bool lgfx_player_sheet_load_impl(const uint8_t *sheet_data, size_t sheet_len, int sheet_w, int sheet_h, int frame_w, int frame_h);
bool lgfx_player_sheet_load_file_impl(const char *sheet_path, int sheet_w, int sheet_h, int frame_w, int frame_h);
void lgfx_player_frame_set_impl(int frame_index);
void lgfx_player_flip_x_set_impl(bool flip_x);
void lgfx_player_sheet_clear_impl(void);
bool lgfx_enemy_sheet_load_file_impl(const char *sheet_path, int sheet_w, int sheet_h, int frame_w, int frame_h);
void lgfx_enemy_frame_set_impl(int frame_index);
void lgfx_enemy_sheet_clear_impl(void);
void lgfx_enemy_draw_impl(int x, int y);
bool lgfx_draw_png_file_impl(const char *path, int x, int y, int w, int h);
bool lgfx_png_slot_load_file_impl(int slot_id, const char *path);
bool lgfx_png_slot_draw_impl(int slot_id, int x, int y, int w, int h);
void lgfx_png_slot_release_impl(int slot_id);
void lgfx_png_slot_release_all_impl(void);
void lgfx_get_stats_impl(uint32_t *full_frames, uint32_t *dirty_frames, uint32_t *last_us, uint32_t *last_tiles);
#ifdef __cplusplus
}
#endif

static mp_obj_t lgfx_init(void) {
    lgfx_init_impl();
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(lgfx_init_obj, lgfx_init);

static mp_obj_t lgfx_fill(mp_obj_t color_obj) {
    lgfx_fill_impl((uint16_t)mp_obj_get_int(color_obj));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(lgfx_fill_obj, lgfx_fill);

static mp_obj_t lgfx_draw_rect(size_t n_args, const mp_obj_t *args) {
    (void)n_args;
    int x = mp_obj_get_int(args[0]);
    int y = mp_obj_get_int(args[1]);
    int w = mp_obj_get_int(args[2]);
    int h = mp_obj_get_int(args[3]);
    uint16_t color = (uint16_t)mp_obj_get_int(args[4]);
    lgfx_draw_rect_impl(x, y, w, h, color);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR(lgfx_draw_rect_obj, 5, lgfx_draw_rect);

static mp_obj_t lgfx_draw_text(size_t n_args, const mp_obj_t *args) {
    (void)n_args;
    int x = mp_obj_get_int(args[0]);
    int y = mp_obj_get_int(args[1]);
    const char *text = mp_obj_str_get_str(args[2]);
    uint16_t color = (uint16_t)mp_obj_get_int(args[3]);
    lgfx_draw_text_impl(x, y, text, color);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR(lgfx_draw_text_obj, 4, lgfx_draw_text);

static mp_obj_t lgfx_draw_circle(size_t n_args, const mp_obj_t *args) {
    (void)n_args;
    int x = mp_obj_get_int(args[0]);
    int y = mp_obj_get_int(args[1]);
    int r = mp_obj_get_int(args[2]);
    uint16_t color = (uint16_t)mp_obj_get_int(args[3]);
    lgfx_draw_circle_impl(x, y, r, color);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR(lgfx_draw_circle_obj, 4, lgfx_draw_circle);

static mp_obj_t lgfx_clear(void) {
    lgfx_clear_impl();
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(lgfx_clear_obj, lgfx_clear);

static mp_obj_t lgfx_set_rotation(mp_obj_t rotation_obj) {
    lgfx_set_rotation_impl(mp_obj_get_int(rotation_obj));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(lgfx_set_rotation_obj, lgfx_set_rotation);

static mp_obj_t lgfx_set_brightness(mp_obj_t brightness_obj) {
    lgfx_set_brightness_impl(mp_obj_get_int(brightness_obj));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(lgfx_set_brightness_obj, lgfx_set_brightness);

static mp_obj_t lgfx_set_swap_bytes(mp_obj_t swap_obj) {
    lgfx_set_swap_bytes_impl(mp_obj_is_true(swap_obj));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(lgfx_set_swap_bytes_obj, lgfx_set_swap_bytes);

static mp_obj_t lgfx_sprite_create(size_t n_args, const mp_obj_t *args) {
    int w = mp_obj_get_int(args[0]);
    int h = mp_obj_get_int(args[1]);
    bool use_psram = true;
    if (n_args >= 3) {
        use_psram = mp_obj_is_true(args[2]);
    }
    lgfx_sprite_create_impl(w, h, use_psram);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(lgfx_sprite_create_obj, 2, 3, lgfx_sprite_create);

static mp_obj_t lgfx_sprite_fill(mp_obj_t color_obj) {
    lgfx_sprite_fill_impl((uint16_t)mp_obj_get_int(color_obj));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(lgfx_sprite_fill_obj, lgfx_sprite_fill);

static mp_obj_t lgfx_sprite_push(mp_obj_t x_obj, mp_obj_t y_obj) {
    int x = mp_obj_get_int(x_obj);
    int y = mp_obj_get_int(y_obj);
    lgfx_sprite_push_impl(x, y);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(lgfx_sprite_push_obj, lgfx_sprite_push);

static mp_obj_t lgfx_tile_setup(size_t n_args, const mp_obj_t *args) {
    int tile_size = mp_obj_get_int(args[0]);
    int map_w = mp_obj_get_int(args[1]);
    int map_h = mp_obj_get_int(args[2]);
    int view_w = 240;
    int view_h = 320;
    bool use_psram = true;
    if (n_args >= 5) {
        view_w = mp_obj_get_int(args[3]);
        view_h = mp_obj_get_int(args[4]);
    }
    if (n_args >= 6) {
        use_psram = mp_obj_is_true(args[5]);
    }
    return mp_obj_new_bool(lgfx_tile_setup_impl(tile_size, map_w, map_h, view_w, view_h, use_psram));
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(lgfx_tile_setup_obj, 3, 6, lgfx_tile_setup);

static mp_obj_t lgfx_tile_load(mp_obj_t tileset_obj, mp_obj_t tilemap_obj) {
    mp_buffer_info_t tileset_buf;
    mp_buffer_info_t tilemap_buf;
    mp_get_buffer_raise(tileset_obj, &tileset_buf, MP_BUFFER_READ);
    mp_get_buffer_raise(tilemap_obj, &tilemap_buf, MP_BUFFER_READ);
    bool ok = lgfx_tile_load_impl(
        (const uint8_t *)tileset_buf.buf, tileset_buf.len,
        (const uint8_t *)tilemap_buf.buf, tilemap_buf.len
    );
    return mp_obj_new_bool(ok);
}
static MP_DEFINE_CONST_FUN_OBJ_2(lgfx_tile_load_obj, lgfx_tile_load);

static mp_obj_t lgfx_tile_load_files(mp_obj_t tileset_path_obj, mp_obj_t tilemap_path_obj) {
    const char *tileset_path = mp_obj_str_get_str(tileset_path_obj);
    const char *tilemap_path = mp_obj_str_get_str(tilemap_path_obj);
    return mp_obj_new_bool(lgfx_tile_load_files_impl(tileset_path, tilemap_path));
}
static MP_DEFINE_CONST_FUN_OBJ_2(lgfx_tile_load_files_obj, lgfx_tile_load_files);

static mp_obj_t lgfx_tile_loader_mode(void) {
    return mp_obj_new_int(lgfx_tile_loader_mode_impl());
}
static MP_DEFINE_CONST_FUN_OBJ_0(lgfx_tile_loader_mode_obj, lgfx_tile_loader_mode);

static mp_obj_t lgfx_tile_last_error(void) {
    return mp_obj_new_int(lgfx_tile_last_error_impl());
}
static MP_DEFINE_CONST_FUN_OBJ_0(lgfx_tile_last_error_obj, lgfx_tile_last_error);

static mp_obj_t lgfx_slot_load_files(size_t n_args, const mp_obj_t *args) {
    (void)n_args;
    int slot_id = mp_obj_get_int(args[0]);
    uint32_t map_token = (uint32_t)mp_obj_get_int_truncated(args[1]);
    uint32_t tileset_token = (uint32_t)mp_obj_get_int_truncated(args[2]);
    const char *tileset_path = mp_obj_str_get_str(args[3]);
    const char *tilemap_path = mp_obj_str_get_str(args[4]);
    int tile_size = mp_obj_get_int(args[5]);
    int map_w = mp_obj_get_int(args[6]);
    int map_h = mp_obj_get_int(args[7]);
    return mp_obj_new_bool(lgfx_slot_load_files_impl(slot_id, map_token, tileset_token, tileset_path, tilemap_path, tile_size, map_w, map_h));
}
static MP_DEFINE_CONST_FUN_OBJ_VAR(lgfx_slot_load_files_obj, 8, lgfx_slot_load_files);

static mp_obj_t lgfx_slot_begin_load_files(size_t n_args, const mp_obj_t *args) {
    (void)n_args;
    int slot_id = mp_obj_get_int(args[0]);
    uint32_t map_token = (uint32_t)mp_obj_get_int_truncated(args[1]);
    uint32_t tileset_token = (uint32_t)mp_obj_get_int_truncated(args[2]);
    const char *tileset_path = mp_obj_str_get_str(args[3]);
    const char *tilemap_path = mp_obj_str_get_str(args[4]);
    int tile_size = mp_obj_get_int(args[5]);
    int map_w = mp_obj_get_int(args[6]);
    int map_h = mp_obj_get_int(args[7]);
    return mp_obj_new_bool(lgfx_slot_begin_load_files_impl(slot_id, map_token, tileset_token, tileset_path, tilemap_path, tile_size, map_w, map_h));
}
static MP_DEFINE_CONST_FUN_OBJ_VAR(lgfx_slot_begin_load_files_obj, 8, lgfx_slot_begin_load_files);

static mp_obj_t lgfx_slot_pump_load(size_t n_args, const mp_obj_t *args) {
    int slot_id = mp_obj_get_int(args[0]);
    size_t max_bytes = 8192;
    if (n_args >= 2) {
        max_bytes = (size_t)mp_obj_get_int(args[1]);
    }
    return mp_obj_new_int(lgfx_slot_pump_load_impl(slot_id, max_bytes));
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(lgfx_slot_pump_load_obj, 1, 2, lgfx_slot_pump_load);

static mp_obj_t lgfx_slot_cancel_load(mp_obj_t slot_id_obj) {
    return mp_obj_new_bool(lgfx_slot_cancel_load_impl(mp_obj_get_int(slot_id_obj)));
}
static MP_DEFINE_CONST_FUN_OBJ_1(lgfx_slot_cancel_load_obj, lgfx_slot_cancel_load);

static mp_obj_t lgfx_slot_select(size_t n_args, const mp_obj_t *args) {
    int slot_id = mp_obj_get_int(args[0]);
    bool force_full_redraw = true;
    if (n_args >= 2) {
        force_full_redraw = mp_obj_is_true(args[1]);
    }
    return mp_obj_new_bool(lgfx_slot_select_impl(slot_id, force_full_redraw));
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(lgfx_slot_select_obj, 1, 2, lgfx_slot_select);

static mp_obj_t lgfx_slot_release(mp_obj_t slot_id_obj) {
    return mp_obj_new_bool(lgfx_slot_release_impl(mp_obj_get_int(slot_id_obj)));
}
static MP_DEFINE_CONST_FUN_OBJ_1(lgfx_slot_release_obj, lgfx_slot_release);

static mp_obj_t lgfx_slot_has_map(mp_obj_t slot_id_obj, mp_obj_t map_token_obj) {
    int slot_id = mp_obj_get_int(slot_id_obj);
    uint32_t map_token = (uint32_t)mp_obj_get_int_truncated(map_token_obj);
    return mp_obj_new_bool(lgfx_slot_has_map_impl(slot_id, map_token));
}
static MP_DEFINE_CONST_FUN_OBJ_2(lgfx_slot_has_map_obj, lgfx_slot_has_map);

static mp_obj_t lgfx_slot_info(mp_obj_t slot_id_obj) {
    int slot_id = mp_obj_get_int(slot_id_obj);
    int role = 0;
    int state = 0;
    uint32_t map_token = 0;
    uint32_t tileset_token = 0;
    int load_stage = 0;
    size_t loaded_bytes = 0;
    size_t total_bytes = 0;
    int ref_count = 0;
    int waiter_count = 0;
    bool is_active = false;
    if (!lgfx_slot_info_impl(slot_id, &role, &state, &map_token, &tileset_token, &load_stage, &loaded_bytes, &total_bytes, &ref_count, &waiter_count, &is_active)) {
        return mp_const_none;
    }
    mp_obj_t tuple[10];
    tuple[0] = mp_obj_new_int(role);
    tuple[1] = mp_obj_new_int(state);
    tuple[2] = mp_obj_new_int_from_uint(map_token);
    tuple[3] = mp_obj_new_int_from_uint(tileset_token);
    tuple[4] = mp_obj_new_int(load_stage);
    tuple[5] = mp_obj_new_int_from_ull((unsigned long long)loaded_bytes);
    tuple[6] = mp_obj_new_int_from_ull((unsigned long long)total_bytes);
    tuple[7] = mp_obj_new_int(ref_count);
    tuple[8] = mp_obj_new_int(waiter_count);
    tuple[9] = mp_obj_new_bool(is_active);
    return mp_obj_new_tuple(10, tuple);
}
static MP_DEFINE_CONST_FUN_OBJ_1(lgfx_slot_info_obj, lgfx_slot_info);

static mp_obj_t lgfx_slot_set_role(mp_obj_t slot_id_obj, mp_obj_t role_obj) {
    lgfx_slot_set_role_impl(mp_obj_get_int(slot_id_obj), mp_obj_get_int(role_obj));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(lgfx_slot_set_role_obj, lgfx_slot_set_role);

static mp_obj_t lgfx_display_wait_idle(void) {
    lgfx_display_wait_idle_impl();
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(lgfx_display_wait_idle_obj, lgfx_display_wait_idle);

static mp_obj_t lgfx_tile_set(mp_obj_t tx_obj, mp_obj_t ty_obj, mp_obj_t idx_obj) {
    int tx = mp_obj_get_int(tx_obj);
    int ty = mp_obj_get_int(ty_obj);
    int idx = mp_obj_get_int(idx_obj);
    return mp_obj_new_bool(lgfx_tile_set_impl(tx, ty, idx));
}
static MP_DEFINE_CONST_FUN_OBJ_3(lgfx_tile_set_obj, lgfx_tile_set);

static mp_obj_t lgfx_tile_render(size_t n_args, const mp_obj_t *args) {
    int scroll_x = mp_obj_get_int(args[0]);
    int scroll_y = mp_obj_get_int(args[1]);
    bool force_full = false;
    if (n_args >= 3) {
        force_full = mp_obj_is_true(args[2]);
    }
    int mode = lgfx_tile_render_impl(scroll_x, scroll_y, force_full);
    return mp_obj_new_int(mode);
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(lgfx_tile_render_obj, 2, 3, lgfx_tile_render);

static mp_obj_t lgfx_tile_render_player(size_t n_args, const mp_obj_t *args) {
    int scroll_x = mp_obj_get_int(args[0]);
    int scroll_y = mp_obj_get_int(args[1]);
    int player_x = mp_obj_get_int(args[2]);
    int player_y = mp_obj_get_int(args[3]);
    uint16_t color = 0xF800;
    int radius = 3;
    bool force_full = false;
    if (n_args >= 5) {
        color = (uint16_t)mp_obj_get_int(args[4]);
    }
    if (n_args >= 6) {
        radius = mp_obj_get_int(args[5]);
    }
    if (n_args >= 7) {
        force_full = mp_obj_is_true(args[6]);
    }
    int mode = lgfx_tile_render_player_impl(scroll_x, scroll_y, player_x, player_y, color, radius, force_full);
    return mp_obj_new_int(mode);
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(lgfx_tile_render_player_obj, 4, 7, lgfx_tile_render_player);

static mp_obj_t lgfx_draw_player(size_t n_args, const mp_obj_t *args) {
    int x = mp_obj_get_int(args[0]);
    int y = mp_obj_get_int(args[1]);
    uint16_t color = 0xF800;
    int radius = 3;
    if (n_args >= 3) {
        color = (uint16_t)mp_obj_get_int(args[2]);
    }
    if (n_args >= 4) {
        radius = mp_obj_get_int(args[3]);
    }
    lgfx_draw_player_impl(x, y, color, radius);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(lgfx_draw_player_obj, 2, 4, lgfx_draw_player);

static mp_obj_t lgfx_player_sheet_load(size_t n_args, const mp_obj_t *args) {
    (void)n_args;
    mp_buffer_info_t sheet_buf;
    mp_get_buffer_raise(args[0], &sheet_buf, MP_BUFFER_READ);
    int sheet_w = mp_obj_get_int(args[1]);
    int sheet_h = mp_obj_get_int(args[2]);
    int frame_w = mp_obj_get_int(args[3]);
    int frame_h = mp_obj_get_int(args[4]);
    bool ok = lgfx_player_sheet_load_impl(
        (const uint8_t *)sheet_buf.buf,
        sheet_buf.len,
        sheet_w,
        sheet_h,
        frame_w,
        frame_h
    );
    return mp_obj_new_bool(ok);
}
static MP_DEFINE_CONST_FUN_OBJ_VAR(lgfx_player_sheet_load_obj, 5, lgfx_player_sheet_load);

static mp_obj_t lgfx_player_sheet_load_file(size_t n_args, const mp_obj_t *args) {
    (void)n_args;
    const char *sheet_path = mp_obj_str_get_str(args[0]);
    int sheet_w = mp_obj_get_int(args[1]);
    int sheet_h = mp_obj_get_int(args[2]);
    int frame_w = mp_obj_get_int(args[3]);
    int frame_h = mp_obj_get_int(args[4]);
    bool ok = lgfx_player_sheet_load_file_impl(sheet_path, sheet_w, sheet_h, frame_w, frame_h);
    return mp_obj_new_bool(ok);
}
static MP_DEFINE_CONST_FUN_OBJ_VAR(lgfx_player_sheet_load_file_obj, 5, lgfx_player_sheet_load_file);

static mp_obj_t lgfx_player_frame_set(mp_obj_t frame_index_obj) {
    lgfx_player_frame_set_impl(mp_obj_get_int(frame_index_obj));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(lgfx_player_frame_set_obj, lgfx_player_frame_set);

static mp_obj_t lgfx_player_flip_x_set(mp_obj_t flip_obj) {
    lgfx_player_flip_x_set_impl(mp_obj_is_true(flip_obj));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(lgfx_player_flip_x_set_obj, lgfx_player_flip_x_set);

static mp_obj_t lgfx_player_sheet_clear(void) {
    lgfx_player_sheet_clear_impl();
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(lgfx_player_sheet_clear_obj, lgfx_player_sheet_clear);

static mp_obj_t lgfx_enemy_sheet_load_file(size_t n_args, const mp_obj_t *args) {
    (void)n_args;
    const char *sheet_path = mp_obj_str_get_str(args[0]);
    int sheet_w = mp_obj_get_int(args[1]);
    int sheet_h = mp_obj_get_int(args[2]);
    int frame_w = mp_obj_get_int(args[3]);
    int frame_h = mp_obj_get_int(args[4]);
    bool ok = lgfx_enemy_sheet_load_file_impl(sheet_path, sheet_w, sheet_h, frame_w, frame_h);
    return mp_obj_new_bool(ok);
}
static MP_DEFINE_CONST_FUN_OBJ_VAR(lgfx_enemy_sheet_load_file_obj, 5, lgfx_enemy_sheet_load_file);

static mp_obj_t lgfx_enemy_frame_set(mp_obj_t frame_index_obj) {
    lgfx_enemy_frame_set_impl(mp_obj_get_int(frame_index_obj));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(lgfx_enemy_frame_set_obj, lgfx_enemy_frame_set);

static mp_obj_t lgfx_enemy_sheet_clear(void) {
    lgfx_enemy_sheet_clear_impl();
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(lgfx_enemy_sheet_clear_obj, lgfx_enemy_sheet_clear);

static mp_obj_t lgfx_enemy_draw(mp_obj_t x_obj, mp_obj_t y_obj) {
    int x = mp_obj_get_int(x_obj);
    int y = mp_obj_get_int(y_obj);
    lgfx_enemy_draw_impl(x, y);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(lgfx_enemy_draw_obj, lgfx_enemy_draw);

static mp_obj_t lgfx_draw_png_file(size_t n_args, const mp_obj_t *args) {
    (void)n_args;
    const char *path = mp_obj_str_get_str(args[0]);
    int x = mp_obj_get_int(args[1]);
    int y = mp_obj_get_int(args[2]);
    int w = mp_obj_get_int(args[3]);
    int h = mp_obj_get_int(args[4]);
    return mp_obj_new_bool(lgfx_draw_png_file_impl(path, x, y, w, h));
}
static MP_DEFINE_CONST_FUN_OBJ_VAR(lgfx_draw_png_file_obj, 5, lgfx_draw_png_file);

static mp_obj_t lgfx_png_slot_load_file(mp_obj_t slot_id_obj, mp_obj_t path_obj) {
    int slot_id = mp_obj_get_int(slot_id_obj);
    const char *path = mp_obj_str_get_str(path_obj);
    return mp_obj_new_bool(lgfx_png_slot_load_file_impl(slot_id, path));
}
static MP_DEFINE_CONST_FUN_OBJ_2(lgfx_png_slot_load_file_obj, lgfx_png_slot_load_file);

static mp_obj_t lgfx_png_slot_draw(size_t n_args, const mp_obj_t *args) {
    (void)n_args;
    int slot_id = mp_obj_get_int(args[0]);
    int x = mp_obj_get_int(args[1]);
    int y = mp_obj_get_int(args[2]);
    int w = mp_obj_get_int(args[3]);
    int h = mp_obj_get_int(args[4]);
    return mp_obj_new_bool(lgfx_png_slot_draw_impl(slot_id, x, y, w, h));
}
static MP_DEFINE_CONST_FUN_OBJ_VAR(lgfx_png_slot_draw_obj, 5, lgfx_png_slot_draw);

static mp_obj_t lgfx_png_slot_release(mp_obj_t slot_id_obj) {
    lgfx_png_slot_release_impl(mp_obj_get_int(slot_id_obj));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(lgfx_png_slot_release_obj, lgfx_png_slot_release);

static mp_obj_t lgfx_png_slot_release_all(void) {
    lgfx_png_slot_release_all_impl();
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(lgfx_png_slot_release_all_obj, lgfx_png_slot_release_all);

static mp_obj_t lgfx_stats(void) {
    uint32_t full_frames = 0;
    uint32_t dirty_frames = 0;
    uint32_t last_us = 0;
    uint32_t last_tiles = 0;
    lgfx_get_stats_impl(&full_frames, &dirty_frames, &last_us, &last_tiles);
    mp_obj_t tuple[4];
    tuple[0] = mp_obj_new_int_from_uint(full_frames);
    tuple[1] = mp_obj_new_int_from_uint(dirty_frames);
    tuple[2] = mp_obj_new_int_from_uint(last_us);
    tuple[3] = mp_obj_new_int_from_uint(last_tiles);
    return mp_obj_new_tuple(4, tuple);
}
static MP_DEFINE_CONST_FUN_OBJ_0(lgfx_stats_obj, lgfx_stats);

static const mp_rom_map_elem_t lgfx_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_lgfx) },
    { MP_ROM_QSTR(MP_QSTR_init), MP_ROM_PTR(&lgfx_init_obj) },
    { MP_ROM_QSTR(MP_QSTR_fill), MP_ROM_PTR(&lgfx_fill_obj) },
    { MP_ROM_QSTR(MP_QSTR_draw_text), MP_ROM_PTR(&lgfx_draw_text_obj) },
    { MP_ROM_QSTR(MP_QSTR_draw_rect), MP_ROM_PTR(&lgfx_draw_rect_obj) },
    { MP_ROM_QSTR(MP_QSTR_draw_circle), MP_ROM_PTR(&lgfx_draw_circle_obj) },
    { MP_ROM_QSTR(MP_QSTR_clear), MP_ROM_PTR(&lgfx_clear_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_rotation), MP_ROM_PTR(&lgfx_set_rotation_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_brightness), MP_ROM_PTR(&lgfx_set_brightness_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_swap_bytes), MP_ROM_PTR(&lgfx_set_swap_bytes_obj) },
    { MP_ROM_QSTR(MP_QSTR_sprite_create), MP_ROM_PTR(&lgfx_sprite_create_obj) },
    { MP_ROM_QSTR(MP_QSTR_sprite_fill), MP_ROM_PTR(&lgfx_sprite_fill_obj) },
    { MP_ROM_QSTR(MP_QSTR_sprite_push), MP_ROM_PTR(&lgfx_sprite_push_obj) },
    { MP_ROM_QSTR(MP_QSTR_tile_setup), MP_ROM_PTR(&lgfx_tile_setup_obj) },
    { MP_ROM_QSTR(MP_QSTR_tile_load), MP_ROM_PTR(&lgfx_tile_load_obj) },
    { MP_ROM_QSTR(MP_QSTR_tile_load_files), MP_ROM_PTR(&lgfx_tile_load_files_obj) },
    { MP_ROM_QSTR(MP_QSTR_tile_loader_mode), MP_ROM_PTR(&lgfx_tile_loader_mode_obj) },
    { MP_ROM_QSTR(MP_QSTR_tile_last_error), MP_ROM_PTR(&lgfx_tile_last_error_obj) },
    { MP_ROM_QSTR(MP_QSTR_slot_load_files), MP_ROM_PTR(&lgfx_slot_load_files_obj) },
    { MP_ROM_QSTR(MP_QSTR_slot_begin_load_files), MP_ROM_PTR(&lgfx_slot_begin_load_files_obj) },
    { MP_ROM_QSTR(MP_QSTR_slot_pump_load), MP_ROM_PTR(&lgfx_slot_pump_load_obj) },
    { MP_ROM_QSTR(MP_QSTR_slot_cancel_load), MP_ROM_PTR(&lgfx_slot_cancel_load_obj) },
    { MP_ROM_QSTR(MP_QSTR_slot_select), MP_ROM_PTR(&lgfx_slot_select_obj) },
    { MP_ROM_QSTR(MP_QSTR_slot_release), MP_ROM_PTR(&lgfx_slot_release_obj) },
    { MP_ROM_QSTR(MP_QSTR_slot_has_map), MP_ROM_PTR(&lgfx_slot_has_map_obj) },
    { MP_ROM_QSTR(MP_QSTR_slot_info), MP_ROM_PTR(&lgfx_slot_info_obj) },
    { MP_ROM_QSTR(MP_QSTR_slot_set_role), MP_ROM_PTR(&lgfx_slot_set_role_obj) },
    { MP_ROM_QSTR(MP_QSTR_display_wait_idle), MP_ROM_PTR(&lgfx_display_wait_idle_obj) },
    { MP_ROM_QSTR(MP_QSTR_tile_set), MP_ROM_PTR(&lgfx_tile_set_obj) },
    { MP_ROM_QSTR(MP_QSTR_tile_render), MP_ROM_PTR(&lgfx_tile_render_obj) },
    { MP_ROM_QSTR(MP_QSTR_tile_render_player), MP_ROM_PTR(&lgfx_tile_render_player_obj) },
    { MP_ROM_QSTR(MP_QSTR_draw_player), MP_ROM_PTR(&lgfx_draw_player_obj) },
    { MP_ROM_QSTR(MP_QSTR_player_sheet_load), MP_ROM_PTR(&lgfx_player_sheet_load_obj) },
    { MP_ROM_QSTR(MP_QSTR_player_sheet_load_file), MP_ROM_PTR(&lgfx_player_sheet_load_file_obj) },
    { MP_ROM_QSTR(MP_QSTR_player_frame_set), MP_ROM_PTR(&lgfx_player_frame_set_obj) },
    { MP_ROM_QSTR(MP_QSTR_player_flip_x_set), MP_ROM_PTR(&lgfx_player_flip_x_set_obj) },
    { MP_ROM_QSTR(MP_QSTR_player_sheet_clear), MP_ROM_PTR(&lgfx_player_sheet_clear_obj) },
    { MP_ROM_QSTR(MP_QSTR_enemy_sheet_load_file), MP_ROM_PTR(&lgfx_enemy_sheet_load_file_obj) },
    { MP_ROM_QSTR(MP_QSTR_enemy_frame_set), MP_ROM_PTR(&lgfx_enemy_frame_set_obj) },
    { MP_ROM_QSTR(MP_QSTR_enemy_sheet_clear), MP_ROM_PTR(&lgfx_enemy_sheet_clear_obj) },
    { MP_ROM_QSTR(MP_QSTR_enemy_draw), MP_ROM_PTR(&lgfx_enemy_draw_obj) },
    { MP_ROM_QSTR(MP_QSTR_draw_png_file), MP_ROM_PTR(&lgfx_draw_png_file_obj) },
    { MP_ROM_QSTR(MP_QSTR_png_slot_load_file), MP_ROM_PTR(&lgfx_png_slot_load_file_obj) },
    { MP_ROM_QSTR(MP_QSTR_png_slot_draw), MP_ROM_PTR(&lgfx_png_slot_draw_obj) },
    { MP_ROM_QSTR(MP_QSTR_png_slot_release), MP_ROM_PTR(&lgfx_png_slot_release_obj) },
    { MP_ROM_QSTR(MP_QSTR_png_slot_release_all), MP_ROM_PTR(&lgfx_png_slot_release_all_obj) },
    { MP_ROM_QSTR(MP_QSTR_stats), MP_ROM_PTR(&lgfx_stats_obj) },
};
static MP_DEFINE_CONST_DICT(lgfx_module_globals, lgfx_module_globals_table);

const mp_obj_module_t lgfx_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&lgfx_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_lgfx, lgfx_user_cmodule);
