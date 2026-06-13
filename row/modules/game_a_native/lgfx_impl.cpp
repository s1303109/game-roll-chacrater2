#ifdef NO_QSTR

#include <stddef.h>
#include <stdint.h>

extern "C" void game_a_lgfx_init_impl(void) {}
extern "C" void game_a_lgfx_fill_impl(uint16_t color) {
  (void)color;
}
extern "C" void game_a_lgfx_draw_text_impl(int x, int y, const char *text, uint16_t color) {
  (void)x;
  (void)y;
  (void)text;
  (void)color;
}
extern "C" void game_a_lgfx_draw_rect_impl(int x, int y, int w, int h, uint16_t color) {
  (void)x;
  (void)y;
  (void)w;
  (void)h;
  (void)color;
}
extern "C" void game_a_lgfx_draw_circle_impl(int x, int y, int r, uint16_t color) {
  (void)x;
  (void)y;
  (void)r;
  (void)color;
}
extern "C" void game_a_lgfx_clear_impl(void) {}
extern "C" void game_a_lgfx_set_rotation_impl(int rotation) {
  (void)rotation;
}
extern "C" void game_a_lgfx_set_brightness_impl(int brightness) {
  (void)brightness;
}
extern "C" void game_a_lgfx_set_swap_bytes_impl(bool swap) {
  (void)swap;
}
extern "C" void game_a_lgfx_sprite_create_impl(int w, int h, bool use_psram) {
  (void)w;
  (void)h;
  (void)use_psram;
}
extern "C" void game_a_lgfx_sprite_fill_impl(uint16_t color) {
  (void)color;
}
extern "C" void game_a_lgfx_sprite_push_impl(int x, int y) {
  (void)x;
  (void)y;
}
extern "C" bool game_a_lgfx_tile_setup_impl(int tile_size, int map_w, int map_h, int view_w, int view_h, bool use_psram) {
  (void)tile_size;
  (void)map_w;
  (void)map_h;
  (void)view_w;
  (void)view_h;
  (void)use_psram;
  return false;
}
extern "C" bool game_a_lgfx_tile_load_impl(const uint8_t *tileset_data, size_t tileset_len, const uint8_t *tilemap_data, size_t tilemap_len) {
  (void)tileset_data;
  (void)tileset_len;
  (void)tilemap_data;
  (void)tilemap_len;
  return false;
}
extern "C" bool game_a_lgfx_tile_set_impl(int tx, int ty, int tile_index) {
  (void)tx;
  (void)ty;
  (void)tile_index;
  return false;
}
extern "C" bool game_a_lgfx_tile_load_files_impl(const char *tileset_path, const char *tilemap_path) {
  (void)tileset_path;
  (void)tilemap_path;
  return false;
}
extern "C" int game_a_lgfx_tile_loader_mode_impl(void) {
  return 0;
}
extern "C" bool game_a_lgfx_slot_load_files_impl(int slot_id, uint32_t map_token, uint32_t tileset_token, const char *tileset_path, const char *tilemap_path, int tile_size, int map_w, int map_h) {
  (void)slot_id;
  (void)map_token;
  (void)tileset_token;
  (void)tileset_path;
  (void)tilemap_path;
  (void)tile_size;
  (void)map_w;
  (void)map_h;
  return false;
}
extern "C" bool game_a_lgfx_slot_begin_load_files_impl(int slot_id, uint32_t map_token, uint32_t tileset_token, const char *tileset_path, const char *tilemap_path, int tile_size, int map_w, int map_h) {
  (void)slot_id;
  (void)map_token;
  (void)tileset_token;
  (void)tileset_path;
  (void)tilemap_path;
  (void)tile_size;
  (void)map_w;
  (void)map_h;
  return false;
}
extern "C" int game_a_lgfx_slot_pump_load_impl(int slot_id, size_t max_bytes) {
  (void)slot_id;
  (void)max_bytes;
  return 0;
}
extern "C" bool game_a_lgfx_slot_cancel_load_impl(int slot_id) {
  (void)slot_id;
  return false;
}
extern "C" bool game_a_lgfx_slot_select_impl(int slot_id, bool force_full_redraw) {
  (void)slot_id;
  (void)force_full_redraw;
  return false;
}
extern "C" bool game_a_lgfx_slot_release_impl(int slot_id) {
  (void)slot_id;
  return false;
}
extern "C" void game_a_lgfx_slot_release_all_impl(void) {}
extern "C" bool game_a_lgfx_slot_has_map_impl(int slot_id, uint32_t map_token) {
  (void)slot_id;
  (void)map_token;
  return false;
}
extern "C" bool game_a_lgfx_slot_info_impl(int slot_id, int *role, int *state, uint32_t *map_token, uint32_t *tileset_token, int *load_stage, size_t *loaded_bytes, size_t *total_bytes, int *ref_count, int *waiter_count, bool *is_active) {
  (void)slot_id;
  if (role) {
    *role = 0;
  }
  if (state) {
    *state = 0;
  }
  if (map_token) {
    *map_token = 0;
  }
  if (tileset_token) {
    *tileset_token = 0;
  }
  if (load_stage) {
    *load_stage = 0;
  }
  if (loaded_bytes) {
    *loaded_bytes = 0;
  }
  if (total_bytes) {
    *total_bytes = 0;
  }
  if (ref_count) {
    *ref_count = 0;
  }
  if (waiter_count) {
    *waiter_count = 0;
  }
  if (is_active) {
    *is_active = false;
  }
  return false;
}
extern "C" void game_a_lgfx_slot_set_role_impl(int slot_id, int role) {
  (void)slot_id;
  (void)role;
}
extern "C" void game_a_lgfx_display_wait_idle_impl(void) {}
extern "C" int game_a_lgfx_tile_last_error_impl(void) {
  return -1;
}
extern "C" int game_a_lgfx_tile_render_impl(int scroll_x, int scroll_y, bool force_full) {
  (void)scroll_x;
  (void)scroll_y;
  (void)force_full;
  return 0;
}
// tile_render_player_impl is defined later in the file with full implementation
extern "C" int game_a_lgfx_tile_render_player_enemy_impl(int scroll_x, int scroll_y, int player_x, int player_y, uint16_t color, int radius,
                                                  int enemy_x, int enemy_y, int enemy_frame, bool enemy_enabled, bool force_full) {
  (void)scroll_x;
  (void)scroll_y;
  (void)player_x;
  (void)player_y;
  (void)color;
  (void)radius;
  (void)enemy_x;
  (void)enemy_y;
  (void)enemy_frame;
  (void)enemy_enabled;
  (void)force_full;
  return 0;
}
extern "C" void game_a_lgfx_draw_player_impl(int x, int y, uint16_t color, int radius) {
  (void)x;
  (void)y;
  (void)color;
  (void)radius;
}
extern "C" bool game_a_lgfx_player_sheet_load_impl(const uint8_t *sheet_data, size_t sheet_len, int sheet_w, int sheet_h, int frame_w, int frame_h) {
  (void)sheet_data;
  (void)sheet_len;
  (void)sheet_w;
  (void)sheet_h;
  (void)frame_w;
  (void)frame_h;
  return false;
}
extern "C" bool game_a_lgfx_player_sheet_load_file_impl(const char *sheet_path, int sheet_w, int sheet_h, int frame_w, int frame_h) {
  (void)sheet_path;
  (void)sheet_w;
  (void)sheet_h;
  (void)frame_w;
  (void)frame_h;
  return false;
}
extern "C" void game_a_lgfx_player_frame_set_impl(int frame_index) {
  (void)frame_index;
}
extern "C" void game_a_lgfx_player_flip_x_set_impl(bool flip_x) {
  (void)flip_x;
}
extern "C" void game_a_lgfx_player_sheet_clear_impl(void) {}
extern "C" bool game_a_lgfx_enemy_sheet_load_file_impl(const char *sheet_path, int sheet_w, int sheet_h, int frame_w, int frame_h) {
  (void)sheet_path;
  (void)sheet_w;
  (void)sheet_h;
  (void)frame_w;
  (void)frame_h;
  return false;
}
extern "C" void game_a_lgfx_enemy_frame_set_impl(int frame_index) {
  (void)frame_index;
}
extern "C" void game_a_lgfx_enemy_sheet_clear_impl(void) {}
extern "C" void game_a_lgfx_enemy_draw_impl(int x, int y) {
  (void)x;
  (void)y;
}
extern "C" void game_a_lgfx_enemy_overlay_clear_impl(void) {}
extern "C" void game_a_lgfx_interact_hint_begin_impl(void) {}
extern "C" void game_a_lgfx_interact_hint_rect_impl(int slot_id, int x, int y, int w, int h, int phase_step) {
  (void)slot_id;
  (void)x;
  (void)y;
  (void)w;
  (void)h;
  (void)phase_step;
}
extern "C" void game_a_lgfx_interact_hint_circle_impl(int slot_id, int cx, int cy, int r, int phase_step) {
  (void)slot_id;
  (void)cx;
  (void)cy;
  (void)r;
  (void)phase_step;
}
extern "C" void game_a_lgfx_interact_hint_end_impl(void) {}
extern "C" void game_a_lgfx_interact_hint_clear_impl(void) {}
extern "C" bool game_a_lgfx_draw_png_file_impl(const char *path, int x, int y, int w, int h) {
  (void)path;
  (void)x;
  (void)y;
  (void)w;
  (void)h;
  return false;
}
extern "C" bool game_a_lgfx_png_slot_load_file_impl(int slot_id, const char *path) {
  (void)slot_id;
  (void)path;
  return false;
}
extern "C" bool game_a_lgfx_png_slot_draw_impl(int slot_id, int x, int y, int w, int h) {
  (void)slot_id;
  (void)x;
  (void)y;
  (void)w;
  (void)h;
  return false;
}
extern "C" void game_a_lgfx_png_slot_release_impl(int slot_id) {
  (void)slot_id;
}
extern "C" void game_a_lgfx_png_slot_release_all_impl(void) {}
extern "C" void game_a_lgfx_get_stats_impl(uint32_t *full_frames, uint32_t *dirty_frames, uint32_t *last_us, uint32_t *last_tiles) {
  if (full_frames) {
    *full_frames = 0;
  }
  if (dirty_frames) {
    *dirty_frames = 0;
  }
  if (last_us) {
    *last_us = 0;
  }
  if (last_tiles) {
    *last_tiles = 0;
  }
}

#else

#include <LovyanGFX.hpp>
#ifdef __cplusplus
extern "C" {
#endif
#include "extmod/vfs.h"
#include "py/nlr.h"
#include "py/runtime.h"
#include "py/stream.h"
#ifdef __cplusplus
}
#endif
#include <driver/spi_common.h>
#include <esp_heap_caps.h>
#include <esp_timer.h>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include "../../../LovyanGFX/src/lgfx/utility/lgfx_pngle.h"

// Forward declarations for functions called before definition
extern "C" void game_a_lgfx_draw_player_impl(int x, int y, uint16_t color, int radius);
extern "C" bool game_a_lgfx_slot_load_files_impl(int slot_id, uint32_t map_token, uint32_t tileset_token, const char *tileset_path, const char *tilemap_path, int tile_size, int map_w, int map_h);

class GameA_LGFX : public lgfx::LGFX_Device {
  lgfx::Panel_ILI9341 _panel;
  lgfx::Bus_SPI _bus;
  lgfx::Light_PWM _light;

public:
  GameA_LGFX(void) {
    constexpr spi_host_device_t TFT_SPI_HOST = SPI2_HOST;
    auto bcfg = _bus.config();
    bcfg.spi_host = TFT_SPI_HOST;
    bcfg.spi_mode = 0;
    bcfg.freq_write = 40000000;
    bcfg.freq_read = 16000000;
    bcfg.spi_3wire = false;
    bcfg.use_lock = true;
    bcfg.dma_channel = SPI_DMA_CH_AUTO;
    bcfg.pin_sclk = 12;
    bcfg.pin_mosi = 11;
    bcfg.pin_miso = -1;
    bcfg.pin_dc = 9;
    _bus.config(bcfg);
    _panel.setBus(&_bus);

    auto pcfg = _panel.config();
    pcfg.pin_cs = 10;
    pcfg.pin_rst = 14;
    pcfg.pin_busy = -1;
    pcfg.panel_width = 240;
    pcfg.panel_height = 320;
    pcfg.offset_x = 0;
    pcfg.offset_y = 0;
    pcfg.offset_rotation = 0;
    pcfg.dummy_read_pixel = 8;
    pcfg.dummy_read_bits = 1;
    pcfg.readable = false;
    pcfg.invert = false;
    pcfg.rgb_order = false;
    pcfg.dlen_16bit = false;
    pcfg.bus_shared = false;
    _panel.config(pcfg);

    auto lcfg = _light.config();
    lcfg.pin_bl = 47;
    lcfg.invert = false;
    lcfg.freq = 5000;
    lcfg.pwm_channel = 7;
    _light.config(lcfg);
    _panel.setLight(&_light);

    setPanel(&_panel);
  }
};

static GameA_LGFX lcd;
static LGFX_Sprite sprite(&lcd);
static bool sprite_ready = false;

struct TileState {
  int tile_size = 16;
  int map_w = 0;
  int map_h = 0;
  int view_w = 240;
  int view_h = 320;
  bool use_psram = true;

  uint16_t *tileset = nullptr;
  size_t tileset_len = 0;
  size_t tile_count = 0;
  size_t tile_bytes = 0;

  uint16_t *tilemap = nullptr;
  uint8_t *dirty = nullptr;
  size_t dirty_len = 0;

  bool tileset_stream = false;
  char tileset_path[160] = {0};
  uint16_t *cache_pixels = nullptr;
  uint32_t *cache_index = nullptr;
  uint32_t *cache_age = nullptr;
  size_t cache_slots = 0;
  uint32_t cache_tick = 0;

  bool loaded = false;
  int last_error = 0;
  bool has_prev_scroll = false;
  int prev_scroll_x = 0;
  int prev_scroll_y = 0;
  int active_slot_id = -1;
} tile_state;

struct RenderStats {
  uint32_t full_frames = 0;
  uint32_t dirty_frames = 0;
  uint32_t last_us = 0;
  uint32_t last_tiles = 0;
} render_stats;

enum TileLoadError {
  TILE_LOAD_OK = 0,
  TILE_LOAD_ERR_ARGS = 1,
  TILE_LOAD_ERR_MAP_OPEN = 2,
  TILE_LOAD_ERR_MAP_READ = 3,
  TILE_LOAD_ERR_TILESET_OPEN = 4,
  TILE_LOAD_ERR_TILESET_SEEK = 5,
  TILE_LOAD_ERR_TILESET_SIZE = 6,
  TILE_LOAD_ERR_TILESET_FORMAT = 7,
  TILE_LOAD_ERR_CACHE_ALLOC = 8,
  TILE_LOAD_ERR_SLOT_RANGE = 9,
  TILE_LOAD_ERR_SLOT_ACTIVE = 10,
  TILE_LOAD_ERR_SLOT_STATE = 11,
  TILE_LOAD_ERR_TILESET_REF = 12,
};

enum ResidentSlotState {
  SLOT_STATE_EMPTY = 0,
  SLOT_STATE_LOADING = 1,
  SLOT_STATE_READY = 2,
  SLOT_STATE_FAILED = 3,
};

enum ResidentSlotRole {
  SLOT_ROLE_NONE = 0,
  SLOT_ROLE_BACK = 1,
  SLOT_ROLE_ACTIVE = 2,
  SLOT_ROLE_AHEAD = 3,
};

enum ResidentLoadStage {
  SLOT_STAGE_NONE = 0,
  SLOT_STAGE_VALIDATE = 1,
  SLOT_STAGE_ACQUIRE_TILESET = 2,
  SLOT_STAGE_WAIT_TILESET = 3,
  SLOT_STAGE_LOAD_TILESET = 4,
  SLOT_STAGE_LOAD_TILEMAP = 5,
  SLOT_STAGE_READY = 6,
};

enum TilesetCacheState {
  CACHE_STATE_EMPTY = 0,
  CACHE_STATE_LOADING = 1,
  CACHE_STATE_READY = 2,
  CACHE_STATE_FAILED = 3,
};

constexpr int RESIDENT_SLOT_COUNT = 3;
constexpr int TILESET_CACHE_COUNT = 6;
constexpr size_t RESIDENT_PATH_LEN = 192;

struct TilesetCacheEntry {
  uint32_t tileset_token = 0;
  uint16_t *ptr = nullptr;
  size_t total_bytes = 0;
  size_t load_offset = 0;
  size_t tile_count = 0;
  size_t tile_bytes = 0;
  int ref_count = 0;
  int waiter_count = 0;
  int state = CACHE_STATE_EMPTY;
  bool use_psram = true;
  char tileset_path[RESIDENT_PATH_LEN] = {0};
};

struct ResidentSlot {
  int role = SLOT_ROLE_NONE;
  int state = SLOT_STATE_EMPTY;
  int load_stage = SLOT_STAGE_NONE;
  uint32_t map_token = 0;
  uint32_t tileset_token = 0;
  int tile_size = 0;
  int map_w = 0;
  int map_h = 0;
  uint16_t *tilemap_ptr = nullptr;
  size_t tilemap_bytes = 0;
  size_t tilemap_offset = 0;
  size_t loaded_bytes = 0;
  size_t total_bytes = 0;
  int cache_index = -1;
  bool cache_waiting = false;
  bool use_psram = true;
  bool invalid_tile_logged = false;
  char tileset_path[RESIDENT_PATH_LEN] = {0};
  char tilemap_path[RESIDENT_PATH_LEN] = {0};
};

static ResidentSlot resident_slots[RESIDENT_SLOT_COUNT];
static TilesetCacheEntry tileset_cache[TILESET_CACHE_COUNT];

struct PlayerOverlayState {
  bool valid = false;
  int x = 0;
  int y = 0;
  int w = 0;
  int h = 0;
  int center_x = 0;
  int center_y = 0;
  int radius = 0;
  uint16_t color = 0;
  bool used_sprite = false;
  int frame_index = 0;
  bool flip_x = false;
  uint32_t scene_epoch = 0;
} player_overlay;

struct EnemyOverlayState {
  bool valid = false;
  int x = 0;
  int y = 0;
  int w = 0;
  int h = 0;
  int center_x = 0;
  int center_y = 0;
  bool used_sprite = false;
  int frame_index = 0;
  uint32_t scene_epoch = 0;
} enemy_overlay;

static uint32_t scene_epoch = 0;

static bool render_compose_player = false;
static bool render_compose_applied = false;
static int render_compose_player_x = 0;
static int render_compose_player_y = 0;
static uint16_t render_compose_player_color = 0xF800;
static int render_compose_player_radius = 3;
static bool render_compose_enemy = false;
static bool render_compose_enemy_applied = false;
static int render_compose_enemy_x = 0;
static int render_compose_enemy_y = 0;
static int render_compose_enemy_frame = 0;

constexpr int MAX_INTERACT_HINTS = 6;

enum InteractHintShape {
  INTERACT_HINT_SHAPE_NONE = 0,
  INTERACT_HINT_SHAPE_RECT = 1,
  INTERACT_HINT_SHAPE_CIRCLE = 2,
};

struct InteractHintState {
  bool valid = false;
  int slot_id = -1;
  int shape = INTERACT_HINT_SHAPE_NONE;
  int x = 0;
  int y = 0;
  int w = 0;
  int h = 0;
  int p0 = 0;
  int p1 = 0;
  int p2 = 0;
  int p3 = 0;
  int phase = 0;
  uint32_t scene_epoch = 0;
};

static InteractHintState interact_hint_prev[MAX_INTERACT_HINTS];
static InteractHintState interact_hint_pending[MAX_INTERACT_HINTS];
static int interact_hint_prev_count = 0;
static int interact_hint_pending_count = 0;
static uint32_t interact_hint_prev_scene_epoch = 0;
static bool interact_hint_write_active = false;

struct PlayerSpriteState {
  uint16_t *pixels = nullptr;
  size_t pixels_len = 0;
  uint8_t *bg_mask = nullptr;
  size_t bg_mask_len = 0;
  int sheet_w = 0;
  int sheet_h = 0;
  int frame_w = 0;
  int frame_h = 0;
  int frame_count = 0;
  int current_frame = 0;
  bool flip_x = false;
  bool enabled = false;
} player_sprite;

struct EnemySpriteState {
  uint16_t *pixels = nullptr;
  size_t pixels_len = 0;
  uint8_t *bg_mask = nullptr;
  size_t bg_mask_len = 0;
  int sheet_w = 0;
  int sheet_h = 0;
  int frame_w = 0;
  int frame_h = 0;
  int frame_count = 0;
  int current_frame = 0;
  bool enabled = false;
} enemy_sprite;

constexpr int MAX_PNG_SLOTS = 16;

struct PngSlot {
  uint16_t *pixels = nullptr;
  int w = 0;
  int h = 0;
  bool valid = false;
};

static PngSlot png_slots[MAX_PNG_SLOTS];

static bool tile_fail(int code) {
  tile_state.last_error = code;
  return false;
}

static mp_obj_t vfs_open_rb(const char *path);
static void vfs_close_quiet(mp_obj_t file);
static bool vfs_read_exact(mp_obj_t file, void *dst, size_t len);
static void interact_hint_reset_storage(void);

static void *lgfx_alloc(size_t size, bool use_psram) {
  if (size == 0) {
    return nullptr;
  }
  if (use_psram) {
    void *p = heap_caps_malloc(size, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (p) {
      return p;
    }
  }
  return heap_caps_malloc(size, MALLOC_CAP_8BIT);
}

static bool copy_cstr(char *dst, size_t dst_len, const char *src) {
  if (!dst || dst_len == 0 || !src) {
    return false;
  }
  size_t len = strlen(src);
  if (len >= dst_len) {
    return false;
  }
  memcpy(dst, src, len + 1);
  return true;
}

static bool slot_id_valid(int slot_id) {
  return slot_id >= 0 && slot_id < RESIDENT_SLOT_COUNT;
}

static void tileset_cache_reset(TilesetCacheEntry *cache) {
  if (!cache) {
    return;
  }
  if (cache->ptr) {
    heap_caps_free(cache->ptr);
    cache->ptr = nullptr;
  }
  cache->tileset_token = 0;
  cache->total_bytes = 0;
  cache->load_offset = 0;
  cache->tile_count = 0;
  cache->tile_bytes = 0;
  cache->ref_count = 0;
  cache->waiter_count = 0;
  cache->state = CACHE_STATE_EMPTY;
  cache->use_psram = true;
  cache->tileset_path[0] = '\0';
}

static void resident_slot_reset(ResidentSlot *slot, bool preserve_role = true) {
  if (!slot) {
    return;
  }
  int role = preserve_role ? slot->role : SLOT_ROLE_NONE;
  memset(slot, 0, sizeof(*slot));
  slot->role = role;
  slot->state = SLOT_STATE_EMPTY;
  slot->load_stage = SLOT_STAGE_NONE;
  slot->cache_index = -1;
  slot->use_psram = true;
}

static void resident_slot_free_tilemap(ResidentSlot *slot) {
  if (slot && slot->tilemap_ptr) {
    heap_caps_free(slot->tilemap_ptr);
    slot->tilemap_ptr = nullptr;
  }
}

static void tileset_cache_maybe_release(int cache_index) {
  if (cache_index < 0 || cache_index >= TILESET_CACHE_COUNT) {
    return;
  }
  TilesetCacheEntry *cache = &tileset_cache[cache_index];
  if (cache->ref_count <= 0 && cache->waiter_count <= 0) {
    tileset_cache_reset(cache);
  }
}

static void resident_slot_detach_cache(ResidentSlot *slot) {
  if (!slot || slot->cache_index < 0 || slot->cache_index >= TILESET_CACHE_COUNT) {
    slot->cache_index = -1;
    slot->cache_waiting = false;
    return;
  }
  TilesetCacheEntry *cache = &tileset_cache[slot->cache_index];
  if (slot->cache_waiting) {
    if (cache->waiter_count > 0) {
      cache->waiter_count -= 1;
    }
    slot->cache_waiting = false;
  } else if (cache->ref_count > 0) {
    cache->ref_count -= 1;
  }
  int cache_index = slot->cache_index;
  slot->cache_index = -1;
  tileset_cache_maybe_release(cache_index);
}

static void resident_slot_release_resources(ResidentSlot *slot, bool preserve_role = true) {
  if (!slot) {
    return;
  }
  resident_slot_detach_cache(slot);
  resident_slot_free_tilemap(slot);
  resident_slot_reset(slot, preserve_role);
}

static int tileset_cache_find(uint32_t tileset_token) {
  for (int i = 0; i < TILESET_CACHE_COUNT; ++i) {
    if (tileset_cache[i].state != CACHE_STATE_EMPTY && tileset_cache[i].tileset_token == tileset_token) {
      return i;
    }
  }
  return -1;
}

static int tileset_cache_find_free(void) {
  for (int i = 0; i < TILESET_CACHE_COUNT; ++i) {
    if (tileset_cache[i].state == CACHE_STATE_EMPTY) {
      return i;
    }
  }
  for (int i = 0; i < TILESET_CACHE_COUNT; ++i) {
    if (tileset_cache[i].ref_count <= 0 && tileset_cache[i].waiter_count <= 0) {
      tileset_cache_reset(&tileset_cache[i]);
      return i;
    }
  }
  return -1;
}

static bool ensure_dirty_buffer(size_t map_cells, bool use_psram) {
  if (map_cells == 0) {
    return false;
  }
  if (tile_state.dirty && tile_state.dirty_len == map_cells) {
    memset(tile_state.dirty, 1, map_cells);
    return true;
  }
  if (tile_state.dirty) {
    heap_caps_free(tile_state.dirty);
    tile_state.dirty = nullptr;
    tile_state.dirty_len = 0;
  }
  tile_state.dirty = static_cast<uint8_t *>(lgfx_alloc(map_cells, use_psram));
  if (!tile_state.dirty) {
    return false;
  }
  tile_state.dirty_len = map_cells;
  memset(tile_state.dirty, 1, map_cells);
  return true;
}

static bool vfs_file_size(const char *path, size_t *size_out) {
  if (!path || !size_out) {
    return false;
  }
  mp_obj_t file = vfs_open_rb(path);
  if (file == MP_OBJ_NULL) {
    return false;
  }
  int errcode = 0;
  mp_off_t size = mp_stream_seek(file, 0, MP_SEEK_END, &errcode);
  vfs_close_quiet(file);
  if (size < 0 || errcode != 0) {
    return false;
  }
  *size_out = (size_t)size;
  return true;
}

static bool resident_read_chunk(const char *path, size_t offset, void *dst, size_t len, int open_err, int seek_err, int read_err) {
  if (!path || !dst || len == 0) {
    return tile_fail(TILE_LOAD_ERR_ARGS);
  }
  mp_obj_t file = vfs_open_rb(path);
  if (file == MP_OBJ_NULL) {
    return tile_fail(open_err);
  }
  int errcode = 0;
  mp_off_t seek_res = mp_stream_seek(file, (mp_off_t)offset, MP_SEEK_SET, &errcode);
  if (seek_res < 0 || errcode != 0) {
    vfs_close_quiet(file);
    return tile_fail(seek_err);
  }
  bool ok = vfs_read_exact(file, dst, len);
  vfs_close_quiet(file);
  if (!ok) {
    return tile_fail(read_err);
  }
  return true;
}

static bool resident_validate_tilemap_ids(const ResidentSlot *slot, const TilesetCacheEntry *cache) {
  if (!slot || !cache || !slot->tilemap_ptr || cache->tile_count == 0) {
    return tile_fail(TILE_LOAD_ERR_TILESET_REF);
  }
  size_t cells = (size_t)slot->map_w * (size_t)slot->map_h;
  for (size_t i = 0; i < cells; ++i) {
    if ((size_t)slot->tilemap_ptr[i] >= cache->tile_count) {
      return tile_fail(TILE_LOAD_ERR_TILESET_REF);
    }
  }
  return true;
}

static bool resident_activate_slot(int slot_id, bool force_full_redraw) {
  if (!slot_id_valid(slot_id)) {
    return tile_fail(TILE_LOAD_ERR_SLOT_RANGE);
  }
  ResidentSlot *slot = &resident_slots[slot_id];
  if (slot->state != SLOT_STATE_READY || slot->cache_index < 0 || slot->cache_index >= TILESET_CACHE_COUNT) {
    return tile_fail(TILE_LOAD_ERR_SLOT_STATE);
  }
  TilesetCacheEntry *cache = &tileset_cache[slot->cache_index];
  if (cache->state != CACHE_STATE_READY || !cache->ptr || !slot->tilemap_ptr) {
    return tile_fail(TILE_LOAD_ERR_TILESET_REF);
  }
  size_t map_cells = (size_t)slot->map_w * (size_t)slot->map_h;
  if (!ensure_dirty_buffer(map_cells, tile_state.use_psram)) {
    return tile_fail(TILE_LOAD_ERR_CACHE_ALLOC);
  }
  tile_state.tile_size = slot->tile_size;
  tile_state.map_w = slot->map_w;
  tile_state.map_h = slot->map_h;
  tile_state.tileset = cache->ptr;
  tile_state.tileset_len = cache->total_bytes;
  tile_state.tile_count = cache->tile_count;
  tile_state.tile_bytes = cache->tile_bytes;
  tile_state.tilemap = slot->tilemap_ptr;
  tile_state.tileset_stream = false;
  tile_state.tileset_path[0] = '\0';
  tile_state.loaded = true;
  tile_state.last_error = TILE_LOAD_OK;
  tile_state.active_slot_id = slot_id;
  tile_state.has_prev_scroll = false;
  player_overlay.valid = false;
  enemy_overlay.valid = false;
  slot->invalid_tile_logged = false;
  return true;
}

static int tileset_cache_attach(uint32_t tileset_token, const char *tileset_path, size_t tileset_bytes, size_t tile_bytes, bool use_psram, ResidentSlot *slot) {
  int cache_index = tileset_cache_find(tileset_token);
  if (cache_index >= 0) {
    TilesetCacheEntry *cache = &tileset_cache[cache_index];
    if (cache->tile_bytes != tile_bytes || cache->total_bytes != tileset_bytes) {
      return -1;
    }
    if (cache->state == CACHE_STATE_READY) {
      cache->ref_count += 1;
      slot->cache_waiting = false;
    } else {
      cache->waiter_count += 1;
      slot->cache_waiting = true;
    }
    slot->cache_index = cache_index;
    return cache_index;
  }

  cache_index = tileset_cache_find_free();
  if (cache_index < 0) {
    return -1;
  }
  TilesetCacheEntry *cache = &tileset_cache[cache_index];
  cache->ptr = static_cast<uint16_t *>(lgfx_alloc(tileset_bytes, use_psram));
  if (!cache->ptr) {
    tileset_cache_reset(cache);
    return -1;
  }
  if (!copy_cstr(cache->tileset_path, sizeof(cache->tileset_path), tileset_path)) {
    tileset_cache_reset(cache);
    return -1;
  }
  cache->tileset_token = tileset_token;
  cache->total_bytes = tileset_bytes;
  cache->load_offset = 0;
  cache->tile_bytes = tile_bytes;
  cache->tile_count = tileset_bytes / tile_bytes;
  cache->ref_count = 0;
  cache->waiter_count = 1;
  cache->state = CACHE_STATE_LOADING;
  cache->use_psram = use_psram;
  slot->cache_index = cache_index;
  slot->cache_waiting = true;
  return cache_index;
}

static void tile_close_stream(void) {
  tile_state.tileset_stream = false;
  tile_state.tileset_path[0] = '\0';
}

static void tile_free_cache(void) {
  if (tile_state.cache_pixels) {
    heap_caps_free(tile_state.cache_pixels);
    tile_state.cache_pixels = nullptr;
  }
  if (tile_state.cache_index) {
    heap_caps_free(tile_state.cache_index);
    tile_state.cache_index = nullptr;
  }
  if (tile_state.cache_age) {
    heap_caps_free(tile_state.cache_age);
    tile_state.cache_age = nullptr;
  }
  tile_state.cache_slots = 0;
  tile_state.cache_tick = 0;
}

static bool tile_alloc_cache(size_t tile_bytes, bool use_psram) {
  tile_free_cache();
  if (tile_bytes == 0) {
    return false;
  }

  // Keep cache budget tighter so 320x240 view can fit on low-memory boards.
  constexpr size_t kCacheBudgetBytes = 96 * 1024;
  size_t slots = kCacheBudgetBytes / tile_bytes;
  if (slots > 128) {
    slots = 128;
  }
  if (slots < 1) {
    slots = 1;
  }

  while (slots >= 1) {
    uint16_t *pixels = static_cast<uint16_t *>(lgfx_alloc(slots * tile_bytes, use_psram));
    uint32_t *index = static_cast<uint32_t *>(lgfx_alloc(slots * sizeof(uint32_t), use_psram));
    uint32_t *age = static_cast<uint32_t *>(lgfx_alloc(slots * sizeof(uint32_t), use_psram));
    if (pixels && index && age) {
      tile_state.cache_pixels = pixels;
      tile_state.cache_index = index;
      tile_state.cache_age = age;
      tile_state.cache_slots = slots;
      memset(tile_state.cache_index, 0xFF, slots * sizeof(uint32_t));
      memset(tile_state.cache_age, 0, slots * sizeof(uint32_t));
      tile_state.cache_tick = 0;
      return true;
    }
    if (pixels) {
      heap_caps_free(pixels);
    }
    if (index) {
      heap_caps_free(index);
    }
    if (age) {
      heap_caps_free(age);
    }
    slots /= 2;
  }
  return false;
}

static mp_obj_t vfs_open_rb(const char *path) {
  mp_obj_t args[2] = {
      mp_obj_new_str(path, strlen(path)),
      MP_OBJ_NEW_QSTR(MP_QSTR_rb),
  };
  nlr_buf_t nlr;
  if (nlr_push(&nlr) == 0) {
    mp_obj_t file = mp_vfs_open(MP_ARRAY_SIZE(args), args, (mp_map_t *)&mp_const_empty_map);
    nlr_pop();
    return file;
  }
  return MP_OBJ_NULL;
}

static void vfs_close_quiet(mp_obj_t file) {
  if (file == MP_OBJ_NULL || file == mp_const_none) {
    return;
  }
  nlr_buf_t nlr;
  if (nlr_push(&nlr) == 0) {
    mp_stream_close(file);
    nlr_pop();
  }
}

static bool vfs_read_exact(mp_obj_t file, void *dst, size_t len) {
  int errcode = 0;
  mp_uint_t got = mp_stream_rw(file, dst, len, &errcode, MP_STREAM_RW_READ);
  return errcode == 0 && got == len;
}

static bool resident_slot_prepare_load(ResidentSlot *slot, uint32_t map_token, uint32_t tileset_token,
                                       const char *tileset_path, const char *tilemap_path,
                                       int tile_size, int map_w, int map_h) {
  if (!slot || !tileset_path || !tilemap_path || tile_size <= 0 || map_w <= 0 || map_h <= 0) {
    return tile_fail(TILE_LOAD_ERR_ARGS);
  }

  size_t map_cells = (size_t)map_w * (size_t)map_h;
  size_t expected_tilemap_len = map_cells * sizeof(uint16_t);
  size_t tilemap_bytes = 0;
  size_t tileset_bytes = 0;
  if (!vfs_file_size(tilemap_path, &tilemap_bytes)) {
    return tile_fail(TILE_LOAD_ERR_MAP_OPEN);
  }
  if (tilemap_bytes != expected_tilemap_len) {
    return tile_fail(TILE_LOAD_ERR_MAP_READ);
  }
  if (!vfs_file_size(tileset_path, &tileset_bytes)) {
    return tile_fail(TILE_LOAD_ERR_TILESET_OPEN);
  }
  size_t tile_pixels = (size_t)tile_size * (size_t)tile_size;
  size_t tile_bytes = tile_pixels * sizeof(uint16_t);
  if (tile_bytes == 0 || (tileset_bytes % tile_bytes) != 0) {
    return tile_fail(TILE_LOAD_ERR_TILESET_FORMAT);
  }
  size_t tile_count = tileset_bytes / tile_bytes;
  if (tile_count == 0) {
    return tile_fail(TILE_LOAD_ERR_TILESET_FORMAT);
  }

  resident_slot_release_resources(slot);
  slot->state = SLOT_STATE_LOADING;
  slot->load_stage = SLOT_STAGE_VALIDATE;
  slot->map_token = map_token;
  slot->tileset_token = tileset_token;
  slot->tile_size = tile_size;
  slot->map_w = map_w;
  slot->map_h = map_h;
  slot->tilemap_bytes = tilemap_bytes;
  slot->tilemap_offset = 0;
  slot->loaded_bytes = 0;
  slot->total_bytes = tilemap_bytes + tileset_bytes;
  slot->use_psram = true;
  slot->invalid_tile_logged = false;
  if (!copy_cstr(slot->tileset_path, sizeof(slot->tileset_path), tileset_path) ||
      !copy_cstr(slot->tilemap_path, sizeof(slot->tilemap_path), tilemap_path)) {
    resident_slot_release_resources(slot);
    return tile_fail(TILE_LOAD_ERR_ARGS);
  }

  slot->tilemap_ptr = static_cast<uint16_t *>(lgfx_alloc(tilemap_bytes, slot->use_psram));
  if (!slot->tilemap_ptr) {
    resident_slot_release_resources(slot);
    return tile_fail(TILE_LOAD_ERR_CACHE_ALLOC);
  }
  memset(slot->tilemap_ptr, 0, tilemap_bytes);
  slot->load_stage = SLOT_STAGE_ACQUIRE_TILESET;

  int cache_index = tileset_cache_attach(tileset_token, tileset_path, tileset_bytes, tile_bytes, true, slot);
  if (cache_index < 0) {
    resident_slot_release_resources(slot);
    return tile_fail(TILE_LOAD_ERR_CACHE_ALLOC);
  }

  TilesetCacheEntry *cache = &tileset_cache[cache_index];
  if (cache->state == CACHE_STATE_READY) {
    slot->load_stage = SLOT_STAGE_LOAD_TILEMAP;
  } else if (cache->load_offset == 0) {
    slot->load_stage = SLOT_STAGE_LOAD_TILESET;
  } else {
    slot->load_stage = SLOT_STAGE_WAIT_TILESET;
  }
  return true;
}

static int tileset_cache_pump(TilesetCacheEntry *cache, size_t max_bytes) {
  if (!cache || cache->state != CACHE_STATE_LOADING || !cache->ptr) {
    return 0;
  }
  size_t remain = cache->total_bytes - cache->load_offset;
  if (remain == 0) {
    cache->state = CACHE_STATE_READY;
    return 0;
  }
  size_t budget = max_bytes == 0 ? remain : max_bytes;
  if (budget > remain) {
    budget = remain;
  }
  if (!resident_read_chunk(cache->tileset_path, cache->load_offset,
                           reinterpret_cast<uint8_t *>(cache->ptr) + cache->load_offset,
                           budget,
                           TILE_LOAD_ERR_TILESET_OPEN,
                           TILE_LOAD_ERR_TILESET_SEEK,
                           TILE_LOAD_ERR_TILESET_SIZE)) {
    cache->state = CACHE_STATE_FAILED;
    return -1;
  }
  cache->load_offset += budget;
  if (cache->load_offset >= cache->total_bytes) {
    cache->load_offset = cache->total_bytes;
    cache->state = CACHE_STATE_READY;
  }
  return (int)budget;
}

static bool resident_slot_promote_tileset_ready(ResidentSlot *slot) {
  if (!slot || slot->cache_index < 0 || slot->cache_index >= TILESET_CACHE_COUNT) {
    return tile_fail(TILE_LOAD_ERR_TILESET_REF);
  }
  TilesetCacheEntry *cache = &tileset_cache[slot->cache_index];
  if (cache->state == CACHE_STATE_FAILED) {
    resident_slot_release_resources(slot);
    slot->state = SLOT_STATE_FAILED;
    slot->load_stage = SLOT_STAGE_NONE;
    return tile_fail(TILE_LOAD_ERR_TILESET_SIZE);
  }
  if (cache->state != CACHE_STATE_READY) {
    return false;
  }
  if (slot->cache_waiting) {
    if (cache->waiter_count > 0) {
      cache->waiter_count -= 1;
    }
    cache->ref_count += 1;
    slot->cache_waiting = false;
  }
  slot->load_stage = SLOT_STAGE_LOAD_TILEMAP;
  return true;
}

static int resident_slot_pump(ResidentSlot *slot, size_t max_bytes, bool sync_complete) {
  if (!slot || slot->state != SLOT_STATE_LOADING) {
    return 0;
  }
  size_t budget = max_bytes;
  int pumped_total = 0;

  while (slot->state == SLOT_STATE_LOADING) {
    if (slot->load_stage == SLOT_STAGE_WAIT_TILESET) {
      if (resident_slot_promote_tileset_ready(slot)) {
        continue;
      }
      if (!sync_complete) {
        break;
      }
      TilesetCacheEntry *cache = &tileset_cache[slot->cache_index];
      int pumped = tileset_cache_pump(cache, 0);
      if (pumped < 0) {
        resident_slot_release_resources(slot);
        slot->state = SLOT_STATE_FAILED;
        slot->load_stage = SLOT_STAGE_NONE;
        return -1;
      }
      pumped_total += pumped;
      if (!resident_slot_promote_tileset_ready(slot)) {
        break;
      }
      continue;
    }

    if (slot->load_stage == SLOT_STAGE_LOAD_TILESET) {
      TilesetCacheEntry *cache = &tileset_cache[slot->cache_index];
      size_t cache_budget = budget == 0 ? 0 : budget;
      int pumped = tileset_cache_pump(cache, cache_budget);
      if (pumped < 0) {
        resident_slot_release_resources(slot);
        slot->state = SLOT_STATE_FAILED;
        slot->load_stage = SLOT_STAGE_NONE;
        return -1;
      }
      pumped_total += pumped;
      slot->loaded_bytes = slot->tilemap_offset + cache->load_offset;
      if (budget > 0) {
        if ((size_t)pumped >= budget) {
          budget = 0;
        } else {
          budget -= (size_t)pumped;
        }
      }
      if (!resident_slot_promote_tileset_ready(slot)) {
        if (!sync_complete || budget == 0) {
          break;
        }
        continue;
      }
      if (!sync_complete && budget == 0) {
        break;
      }
      continue;
    }

    if (slot->load_stage == SLOT_STAGE_LOAD_TILEMAP) {
      size_t remain = slot->tilemap_bytes - slot->tilemap_offset;
      size_t want = budget == 0 ? remain : budget;
      if (want > remain) {
        want = remain;
      }
      if (want == 0 && !sync_complete) {
        break;
      }
      if (want == 0) {
        want = remain;
      }
      if (!resident_read_chunk(slot->tilemap_path, slot->tilemap_offset,
                               reinterpret_cast<uint8_t *>(slot->tilemap_ptr) + slot->tilemap_offset,
                               want,
                               TILE_LOAD_ERR_MAP_OPEN,
                               TILE_LOAD_ERR_TILESET_SEEK,
                               TILE_LOAD_ERR_MAP_READ)) {
        resident_slot_release_resources(slot);
        slot->state = SLOT_STATE_FAILED;
        slot->load_stage = SLOT_STAGE_NONE;
        return -1;
      }
      slot->tilemap_offset += want;
      pumped_total += (int)want;
      TilesetCacheEntry *cache = &tileset_cache[slot->cache_index];
      slot->loaded_bytes = slot->tilemap_offset + cache->load_offset;
      if (budget > 0) {
        if (want >= budget) {
          budget = 0;
        } else {
          budget -= want;
        }
      }
      if (slot->tilemap_offset >= slot->tilemap_bytes) {
        if (!resident_validate_tilemap_ids(slot, cache)) {
          resident_slot_release_resources(slot);
          slot->state = SLOT_STATE_FAILED;
          slot->load_stage = SLOT_STAGE_NONE;
          return -1;
        }
        slot->state = SLOT_STATE_READY;
        slot->load_stage = SLOT_STAGE_READY;
        slot->loaded_bytes = slot->total_bytes;
      }
      if (!sync_complete || budget == 0) {
        break;
      }
      continue;
    }
    break;
  }

  return pumped_total;
}

static const uint16_t *tile_get_pixels(uint16_t tile_idx, mp_obj_t stream_file) {
  size_t tile_pixels = (size_t)tile_state.tile_size * (size_t)tile_state.tile_size;
  if (tile_pixels == 0 || tile_idx >= tile_state.tile_count) {
    return nullptr;
  }

  if (!tile_state.tileset_stream) {
    if (!tile_state.tileset) {
      return nullptr;
    }
    return tile_state.tileset + ((size_t)tile_idx * tile_pixels);
  }

  if (tile_state.tileset_path[0] == '\0' || !tile_state.cache_pixels || !tile_state.cache_index || !tile_state.cache_age || tile_state.cache_slots == 0) {
    return nullptr;
  }

  size_t hit_slot = tile_state.cache_slots;
  size_t free_slot = tile_state.cache_slots;
  size_t lru_slot = 0;
  uint32_t lru_age = 0xFFFFFFFFu;

  for (size_t i = 0; i < tile_state.cache_slots; ++i) {
    if (tile_state.cache_index[i] == (uint32_t)tile_idx) {
      hit_slot = i;
      break;
    }
    if (tile_state.cache_index[i] == 0xFFFFFFFFu && free_slot == tile_state.cache_slots) {
      free_slot = i;
    }
    if (tile_state.cache_age[i] < lru_age) {
      lru_age = tile_state.cache_age[i];
      lru_slot = i;
    }
  }

  if (hit_slot < tile_state.cache_slots) {
    tile_state.cache_age[hit_slot] = ++tile_state.cache_tick;
    return tile_state.cache_pixels + (hit_slot * tile_pixels);
  }

  size_t slot = (free_slot < tile_state.cache_slots) ? free_slot : lru_slot;
  mp_obj_t file = stream_file;
  bool own_file = false;
  if (file == MP_OBJ_NULL) {
    file = vfs_open_rb(tile_state.tileset_path);
    own_file = true;
  }
  if (file == MP_OBJ_NULL) {
    return nullptr;
  }

  uint8_t *dst = reinterpret_cast<uint8_t *>(tile_state.cache_pixels + (slot * tile_pixels));
  bool ok = false;
  mp_off_t offset = (mp_off_t)((size_t)tile_idx * tile_state.tile_bytes);

  for (int attempt = 0; attempt < 2 && !ok; ++attempt) {
    mp_obj_t cur = file;
    bool close_cur = false;

    // Retry with a fresh handle to tolerate transient SD/VFS stream errors.
    if (attempt > 0 && !own_file) {
      cur = vfs_open_rb(tile_state.tileset_path);
      close_cur = true;
      if (cur == MP_OBJ_NULL) {
        continue;
      }
    }

    int errcode = 0;
    mp_off_t seek_res = mp_stream_seek(cur, offset, MP_SEEK_SET, &errcode);
    if (seek_res >= 0 && errcode == 0) {
      ok = vfs_read_exact(cur, dst, tile_state.tile_bytes);
    }

    if (close_cur) {
      vfs_close_quiet(cur);
    }
  }

  if (own_file) {
    vfs_close_quiet(file);
  }
  if (!ok) {
    return nullptr;
  }

  tile_state.cache_index[slot] = (uint32_t)tile_idx;
  tile_state.cache_age[slot] = ++tile_state.cache_tick;
  return tile_state.cache_pixels + (slot * tile_pixels);
}

static void tile_free_buffers(void) {
  tile_close_stream();
  tile_free_cache();
  if (tile_state.dirty) {
    heap_caps_free(tile_state.dirty);
    tile_state.dirty = nullptr;
    tile_state.dirty_len = 0;
  }
  tile_state.tileset = nullptr;
  tile_state.tilemap = nullptr;
  tile_state.tileset_len = 0;
  tile_state.tile_count = 0;
  tile_state.tile_bytes = 0;
  tile_state.loaded = false;
  tile_state.has_prev_scroll = false;
  tile_state.active_slot_id = -1;
  player_overlay.valid = false;
  enemy_overlay.valid = false;
  interact_hint_reset_storage();
}

static bool ensure_sprite_size(int w, int h, bool use_psram) {
  if (sprite_ready && sprite.width() == w && sprite.height() == h) {
    return true;
  }
  sprite.deleteSprite();
  sprite.setColorDepth(16);
  sprite.setPsram(use_psram);
  sprite.createSprite(w, h);
  sprite.setSwapBytes(lcd.getSwapBytes());
  sprite_ready = sprite.width() == w && sprite.height() == h;
  return sprite_ready;
}

static inline void draw_map_tile_to_sprite(int tx, int ty, int sx, int sy, mp_obj_t stream_file) {
  int tile = tile_state.tile_size;
  if (sx >= tile_state.view_w || sy >= tile_state.view_h || sx + tile <= 0 || sy + tile <= 0) {
    return;
  }

  int dst_x0 = sx < 0 ? 0 : sx;
  int dst_y0 = sy < 0 ? 0 : sy;
  int dst_x1 = sx + tile;
  int dst_y1 = sy + tile;
  if (dst_x1 > tile_state.view_w) {
    dst_x1 = tile_state.view_w;
  }
  if (dst_y1 > tile_state.view_h) {
    dst_y1 = tile_state.view_h;
  }
  if (dst_x0 >= dst_x1 || dst_y0 >= dst_y1) {
    return;
  }

  int clip_w = dst_x1 - dst_x0;
  int clip_h = dst_y1 - dst_y0;
  int src_x = dst_x0 - sx;
  int src_y = dst_y0 - sy;

  if (tx < 0 || ty < 0 || tx >= tile_state.map_w || ty >= tile_state.map_h) {
    sprite.fillRect(dst_x0, dst_y0, clip_w, clip_h, 0x0000);
    return;
  }
  size_t map_idx = (size_t)ty * (size_t)tile_state.map_w + (size_t)tx;
  uint16_t tile_idx = tile_state.tilemap[map_idx];
  if (tile_idx >= tile_state.tile_count) {
    if (slot_id_valid(tile_state.active_slot_id)) {
      ResidentSlot *slot = &resident_slots[tile_state.active_slot_id];
      if (!slot->invalid_tile_logged) {
        slot->invalid_tile_logged = true;
        printf("tile_id_oob: slot=%d idx=%u count=%u\n", tile_state.active_slot_id, (unsigned)tile_idx, (unsigned)tile_state.tile_count);
      }
    }
    sprite.fillRect(dst_x0, dst_y0, clip_w, clip_h, 0x0000);
    return;
  }
  const uint16_t *src = tile_get_pixels(tile_idx, stream_file);
  if (!src) {
    sprite.fillRect(dst_x0, dst_y0, clip_w, clip_h, 0x0000);
    return;
  }

  if (clip_w == tile && clip_h == tile) {
    sprite.pushImage(sx, sy, tile, tile, src);
    return;
  }

  for (int yy = 0; yy < clip_h; ++yy) {
    const uint16_t *row = src + (size_t)(src_y + yy) * (size_t)tile + (size_t)src_x;
    sprite.pushImage(dst_x0, dst_y0 + yy, clip_w, 1, row);
  }
}

static void redraw_map_rect_to_sprite(int x, int y, int w, int h, mp_obj_t stream_file, int scroll_x, int scroll_y) {
  if (w <= 0 || h <= 0) {
    return;
  }
  int x0 = x < 0 ? 0 : x;
  int y0 = y < 0 ? 0 : y;
  int x1 = x + w - 1;
  int y1 = y + h - 1;
  if (x1 >= tile_state.view_w) {
    x1 = tile_state.view_w - 1;
  }
  if (y1 >= tile_state.view_h) {
    y1 = tile_state.view_h - 1;
  }
  if (x0 > x1 || y0 > y1) {
    return;
  }

  int tile = tile_state.tile_size;
  int wx0 = scroll_x + x0;
  int wy0 = scroll_y + y0;
  int wx1 = scroll_x + x1;
  int wy1 = scroll_y + y1;

  int tx0 = wx0 / tile;
  int ty0 = wy0 / tile;
  int tx1 = wx1 / tile;
  int ty1 = wy1 / tile;

  for (int ty = ty0; ty <= ty1; ++ty) {
    int sy = ty * tile - scroll_y;
    for (int tx = tx0; tx <= tx1; ++tx) {
      int sx = tx * tile - scroll_x;
      draw_map_tile_to_sprite(tx, ty, sx, sy, stream_file);
    }
  }
}

static inline bool rect_intersects(int x0, int y0, int x1, int y1, int rx, int ry, int rw, int rh) {
  if (rw <= 0 || rh <= 0) {
    return false;
  }
  int rx1 = rx + rw;
  int ry1 = ry + rh;
  return x0 < rx1 && x1 > rx && y0 < ry1 && y1 > ry;
}

static void push_rect_from_sprite_to_lcd_locked(int x, int y, int w, int h);
static bool enemy_draw_sheet_frame(int center_x, int center_y, int *out_x, int *out_y, int *out_w, int *out_h, bool has_active_write);
static bool player_draw_sheet_frame(int center_x, int center_y, int *out_x, int *out_y, int *out_w, int *out_h, bool has_active_write);

static void interact_hint_reset_storage(void) {
  interact_hint_prev_count = 0;
  interact_hint_pending_count = 0;
  interact_hint_prev_scene_epoch = scene_epoch;
  interact_hint_write_active = false;
  for (int i = 0; i < MAX_INTERACT_HINTS; ++i) {
    interact_hint_prev[i].valid = false;
    interact_hint_pending[i].valid = false;
  }
}

static int interact_hint_phase_wave(int phase_step) {
  int phase = phase_step & 7;
  return phase < 4 ? phase : 7 - phase;
}

static bool clip_rect_to_view(int *x, int *y, int *w, int *h) {
  if (!x || !y || !w || !h) {
    return false;
  }
  int nx = *x;
  int ny = *y;
  int nw = *w;
  int nh = *h;
  if (nw <= 0 || nh <= 0) {
    return false;
  }
  if (nx < 0) {
    nw += nx;
    nx = 0;
  }
  if (ny < 0) {
    nh += ny;
    ny = 0;
  }
  if (nx + nw > tile_state.view_w) {
    nw = tile_state.view_w - nx;
  }
  if (ny + nh > tile_state.view_h) {
    nh = tile_state.view_h - ny;
  }
  if (nw <= 0 || nh <= 0) {
    return false;
  }
  *x = nx;
  *y = ny;
  *w = nw;
  *h = nh;
  return true;
}

static void redraw_player_overlay_locked(void) {
  if (!player_overlay.valid || player_overlay.scene_epoch != scene_epoch) {
    return;
  }
  int draw_x = 0;
  int draw_y = 0;
  int draw_w = 0;
  int draw_h = 0;
  if (!player_draw_sheet_frame(player_overlay.center_x, player_overlay.center_y, &draw_x, &draw_y, &draw_w, &draw_h, true)) {
    lcd.fillCircle(player_overlay.center_x, player_overlay.center_y, player_overlay.radius, player_overlay.color);
  }
}

static void redraw_enemy_overlay_locked(void) {
  if (!enemy_overlay.valid || enemy_overlay.scene_epoch != scene_epoch) {
    return;
  }
  int draw_x = 0;
  int draw_y = 0;
  int draw_w = 0;
  int draw_h = 0;
  enemy_draw_sheet_frame(enemy_overlay.center_x, enemy_overlay.center_y, &draw_x, &draw_y, &draw_w, &draw_h, true);
}

static inline bool player_overlay_intersects_rect(int x, int y, int w, int h) {
  return player_overlay.valid &&
         player_overlay.scene_epoch == scene_epoch &&
         rect_intersects(x, y, x + w, y + h, player_overlay.x, player_overlay.y, player_overlay.w, player_overlay.h);
}

static inline bool enemy_overlay_intersects_rect(int x, int y, int w, int h) {
  return enemy_overlay.valid &&
         enemy_overlay.scene_epoch == scene_epoch &&
         rect_intersects(x, y, x + w, y + h, enemy_overlay.x, enemy_overlay.y, enemy_overlay.w, enemy_overlay.h);
}

static void interact_hint_restore_previous_locked(void) {
  if (interact_hint_prev_count <= 0 || interact_hint_prev_scene_epoch != scene_epoch) {
    interact_hint_prev_count = 0;
    return;
  }
  bool redraw_player = false;
  bool redraw_enemy = false;
  for (int i = 0; i < interact_hint_prev_count; ++i) {
    InteractHintState *hint = &interact_hint_prev[i];
    if (!hint->valid) {
      continue;
    }
    push_rect_from_sprite_to_lcd_locked(hint->x, hint->y, hint->w, hint->h);
    if (
      player_overlay.valid &&
      player_overlay.scene_epoch == scene_epoch &&
      rect_intersects(
        hint->x, hint->y, hint->x + hint->w, hint->y + hint->h,
        player_overlay.x, player_overlay.y, player_overlay.w, player_overlay.h
      )
    ) {
      redraw_player = true;
    }
    if (
      enemy_overlay.valid &&
      enemy_overlay.scene_epoch == scene_epoch &&
      rect_intersects(
        hint->x, hint->y, hint->x + hint->w, hint->y + hint->h,
        enemy_overlay.x, enemy_overlay.y, enemy_overlay.w, enemy_overlay.h
      )
    ) {
      redraw_enemy = true;
    }
  }
  if (redraw_enemy) {
    redraw_enemy_overlay_locked();
  }
  if (redraw_player) {
    redraw_player_overlay_locked();
  }
}

static void interact_hint_ensure_write(void) {
  if (interact_hint_write_active) {
    return;
  }
  lcd.startWrite();
  interact_hint_write_active = true;
}

static void interact_hint_finish_write(void) {
  if (!interact_hint_write_active) {
    return;
  }
  lcd.endWrite();
  interact_hint_write_active = false;
}

static void interact_hint_draw_corner(int x, int y, int dx, int dy, int len, uint16_t color) {
  if (len <= 0) {
    return;
  }
  int hx = dx < 0 ? x - len + 1 : x;
  int vy = dy < 0 ? y - len + 1 : y;
  lcd.fillRect(hx, y, len, 1, color);
  lcd.fillRect(x, vy, 1, len, color);
}

static void interact_hint_draw_sparkle(int cx, int cy, int arm, uint16_t color) {
  if (arm <= 0) {
    arm = 1;
  }
  lcd.fillRect(cx - arm, cy, arm * 2 + 1, 1, color);
  lcd.fillRect(cx, cy - arm, 1, arm * 2 + 1, color);
}

static void interact_hint_store_pending(
  int slot_id, int shape, int x, int y, int w, int h,
  int p0, int p1, int p2, int p3, int phase_step
) {
  if (interact_hint_pending_count < 0 || interact_hint_pending_count >= MAX_INTERACT_HINTS) {
    return;
  }
  InteractHintState *hint = &interact_hint_pending[interact_hint_pending_count++];
  hint->valid = true;
  hint->slot_id = slot_id;
  hint->shape = shape;
  hint->x = x;
  hint->y = y;
  hint->w = w;
  hint->h = h;
  hint->p0 = p0;
  hint->p1 = p1;
  hint->p2 = p2;
  hint->p3 = p3;
  hint->phase = phase_step & 7;
  hint->scene_epoch = scene_epoch;
}

static inline int iabs(int v) {
  return v < 0 ? -v : v;
}

static inline bool rgb565_is_near_white(uint16_t c) {
  uint8_t r = (c >> 11) & 0x1F;
  uint8_t g = (c >> 5) & 0x3F;
  uint8_t b = c & 0x1F;
  return r >= 30 && g >= 58 && b >= 30;
}

static inline bool player_pixel_is_transparent(uint16_t c) {
  if (rgb565_is_near_white(c)) {
    return true;
  }
  // Support both byte orders so keying works even if sheet endianness changes.
  uint16_t swapped = (uint16_t)((c << 8) | (c >> 8));
  return rgb565_is_near_white(swapped);
}

static inline bool rgb565_is_bg_fringe(uint16_t c) {
  uint8_t r = (c >> 11) & 0x1F;
  uint8_t g = (c >> 5) & 0x3F;
  uint8_t b = c & 0x1F;
  return r >= 28 && g >= 56 && b >= 28;
}

static inline bool player_pixel_is_bg_fringe(uint16_t c) {
  if (rgb565_is_bg_fringe(c)) {
    return true;
  }
  uint16_t swapped = (uint16_t)((c << 8) | (c >> 8));
  return rgb565_is_bg_fringe(swapped);
}

static inline bool mask_bit_get(const uint8_t *mask, size_t index) {
  return (mask[index >> 3] & (uint8_t)(1u << (index & 7))) != 0;
}

static inline void mask_bit_set(uint8_t *mask, size_t index) {
  mask[index >> 3] |= (uint8_t)(1u << (index & 7));
}

static uint8_t *player_alloc_bytes(size_t len) {
  uint8_t *buf = static_cast<uint8_t *>(heap_caps_malloc(len, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
  if (!buf) {
    buf = static_cast<uint8_t *>(std::malloc(len));
  }
  if (!buf) {
    buf = static_cast<uint8_t *>(heap_caps_malloc(len, MALLOC_CAP_8BIT));
  }
  return buf;
}

static bool player_build_bg_mask(const uint16_t *sheet_pixels, int sheet_w, int sheet_h, int frame_w, int frame_h, int frame_count,
                                 uint8_t **out_mask, size_t *out_mask_len) {
  if (!sheet_pixels || !out_mask || !out_mask_len || sheet_w <= 0 || sheet_h <= 0 || frame_w <= 0 || frame_h <= 0 || frame_count <= 0) {
    return false;
  }

  size_t frame_pixels = (size_t)frame_w * (size_t)frame_h;
  if (frame_pixels == 0) {
    return false;
  }
  size_t total_pixels = frame_pixels * (size_t)frame_count;
  size_t mask_len = (total_pixels + 7) / 8;
  uint8_t *mask = player_alloc_bytes(mask_len);
  if (!mask) {
    return false;
  }
  memset(mask, 0, mask_len);

  uint32_t *queue = static_cast<uint32_t *>(std::malloc(frame_pixels * sizeof(uint32_t)));
  if (!queue) {
    heap_caps_free(mask);
    return false;
  }

  int frames_per_row = sheet_w / frame_w;
  bool ok = true;

  for (int frame_index = 0; frame_index < frame_count; ++frame_index) {
    int src_col = frame_index % frames_per_row;
    int src_row = frame_index / frames_per_row;
    int src_x = src_col * frame_w;
    int src_y = src_row * frame_h;
    if (src_x < 0 || src_y < 0 || src_x + frame_w > sheet_w || src_y + frame_h > sheet_h) {
      ok = false;
      break;
    }

    size_t frame_offset = (size_t)frame_index * frame_pixels;
    size_t q_head = 0;
    size_t q_tail = 0;

    auto try_enqueue = [&](int lx, int ly) {
      if (lx < 0 || ly < 0 || lx >= frame_w || ly >= frame_h) {
        return;
      }
      size_t local_idx = (size_t)ly * (size_t)frame_w + (size_t)lx;
      size_t mask_idx = frame_offset + local_idx;
      if (mask_bit_get(mask, mask_idx)) {
        return;
      }
      size_t sheet_idx = (size_t)(src_y + ly) * (size_t)sheet_w + (size_t)(src_x + lx);
      if (!player_pixel_is_transparent(sheet_pixels[sheet_idx])) {
        return;
      }
      mask_bit_set(mask, mask_idx);
      queue[q_tail++] = (uint32_t)local_idx;
    };

    for (int x = 0; x < frame_w; ++x) {
      try_enqueue(x, 0);
      if (frame_h > 1) {
        try_enqueue(x, frame_h - 1);
      }
    }
    for (int y = 1; y < frame_h - 1; ++y) {
      try_enqueue(0, y);
      if (frame_w > 1) {
        try_enqueue(frame_w - 1, y);
      }
    }

    while (q_head < q_tail) {
      uint32_t local = queue[q_head++];
      int lx = (int)(local % (uint32_t)frame_w);
      int ly = (int)(local / (uint32_t)frame_w);
      if (lx > 0) {
        try_enqueue(lx - 1, ly);
      }
      if (lx + 1 < frame_w) {
        try_enqueue(lx + 1, ly);
      }
      if (ly > 0) {
        try_enqueue(lx, ly - 1);
      }
      if (ly + 1 < frame_h) {
        try_enqueue(lx, ly + 1);
      }
    }

    constexpr int kFringeGrowPasses = 3;
    for (int pass = 0; pass < kFringeGrowPasses; ++pass) {
      q_tail = 0;
      for (int ly = 0; ly < frame_h; ++ly) {
        for (int lx = 0; lx < frame_w; ++lx) {
          size_t local_idx = (size_t)ly * (size_t)frame_w + (size_t)lx;
          size_t mask_idx = frame_offset + local_idx;
          if (mask_bit_get(mask, mask_idx)) {
            continue;
          }

          size_t sheet_idx = (size_t)(src_y + ly) * (size_t)sheet_w + (size_t)(src_x + lx);
          if (!player_pixel_is_bg_fringe(sheet_pixels[sheet_idx])) {
            continue;
          }

          bool touch_bg = false;
          if (lx > 0 && mask_bit_get(mask, frame_offset + local_idx - 1)) {
            touch_bg = true;
          } else if (lx + 1 < frame_w && mask_bit_get(mask, frame_offset + local_idx + 1)) {
            touch_bg = true;
          } else if (ly > 0 && mask_bit_get(mask, frame_offset + local_idx - (size_t)frame_w)) {
            touch_bg = true;
          } else if (ly + 1 < frame_h && mask_bit_get(mask, frame_offset + local_idx + (size_t)frame_w)) {
            touch_bg = true;
          } else if (lx > 0 && ly > 0 && mask_bit_get(mask, frame_offset + local_idx - (size_t)frame_w - 1)) {
            touch_bg = true;
          } else if (lx + 1 < frame_w && ly > 0 && mask_bit_get(mask, frame_offset + local_idx - (size_t)frame_w + 1)) {
            touch_bg = true;
          } else if (lx > 0 && ly + 1 < frame_h && mask_bit_get(mask, frame_offset + local_idx + (size_t)frame_w - 1)) {
            touch_bg = true;
          } else if (lx + 1 < frame_w && ly + 1 < frame_h && mask_bit_get(mask, frame_offset + local_idx + (size_t)frame_w + 1)) {
            touch_bg = true;
          }

          if (touch_bg) {
            queue[q_tail++] = (uint32_t)local_idx;
          }
        }
      }
      if (q_tail == 0) {
        break;
      }
      for (size_t i = 0; i < q_tail; ++i) {
        mask_bit_set(mask, frame_offset + (size_t)queue[i]);
      }
    }
  }

  std::free(queue);
  if (!ok) {
    heap_caps_free(mask);
    return false;
  }

  *out_mask = mask;
  *out_mask_len = mask_len;
  return true;
}

static void push_rect_from_sprite_to_lcd_locked(int x, int y, int w, int h) {
  if (!sprite_ready || w <= 0 || h <= 0) {
    return;
  }
  if (x < 0) {
    w += x;
    x = 0;
  }
  if (y < 0) {
    h += y;
    y = 0;
  }
  if (x + w > tile_state.view_w) {
    w = tile_state.view_w - x;
  }
  if (y + h > tile_state.view_h) {
    h = tile_state.view_h - y;
  }
  if (w <= 0 || h <= 0) {
    return;
  }
  uint16_t *buf = static_cast<uint16_t *>(sprite.getBuffer());
  int stride = sprite.width();
  for (int yy = 0; yy < h; ++yy) {
    const lgfx::swap565_t *line = reinterpret_cast<const lgfx::swap565_t *>(buf + (y + yy) * stride + x);
    // Sprite buffers are rgb565_2Byte (swap565) regardless of lcd swap settings.
    lcd.pushImage(x, y + yy, w, 1, line);
  }
}

static void push_rect_from_sprite_to_lcd(int x, int y, int w, int h) {
  lcd.startWrite();
  push_rect_from_sprite_to_lcd_locked(x, y, w, h);
  lcd.endWrite();
}

static void enemy_overlay_clear_state(bool has_active_write) {
  if (!enemy_overlay.valid) {
    return;
  }
  if (sprite_ready && enemy_overlay.scene_epoch == scene_epoch) {
    if (has_active_write) {
      push_rect_from_sprite_to_lcd_locked(enemy_overlay.x, enemy_overlay.y, enemy_overlay.w, enemy_overlay.h);
    } else {
      push_rect_from_sprite_to_lcd(enemy_overlay.x, enemy_overlay.y, enemy_overlay.w, enemy_overlay.h);
    }
  }
  enemy_overlay.valid = false;
}

static void player_sheet_release(void) {
  if (player_sprite.pixels) {
    heap_caps_free(player_sprite.pixels);
    player_sprite.pixels = nullptr;
  }
  if (player_sprite.bg_mask) {
    heap_caps_free(player_sprite.bg_mask);
    player_sprite.bg_mask = nullptr;
  }
  player_sprite.pixels_len = 0;
  player_sprite.bg_mask_len = 0;
  player_sprite.sheet_w = 0;
  player_sprite.sheet_h = 0;
  player_sprite.frame_w = 0;
  player_sprite.frame_h = 0;
  player_sprite.frame_count = 0;
  player_sprite.current_frame = 0;
  player_sprite.flip_x = false;
  player_sprite.enabled = false;
}

static void enemy_sheet_release(void) {
  enemy_overlay_clear_state(false);
  if (enemy_sprite.pixels) {
    heap_caps_free(enemy_sprite.pixels);
    enemy_sprite.pixels = nullptr;
  }
  if (enemy_sprite.bg_mask) {
    heap_caps_free(enemy_sprite.bg_mask);
    enemy_sprite.bg_mask = nullptr;
  }
  enemy_sprite.pixels_len = 0;
  enemy_sprite.bg_mask_len = 0;
  enemy_sprite.sheet_w = 0;
  enemy_sprite.sheet_h = 0;
  enemy_sprite.frame_w = 0;
  enemy_sprite.frame_h = 0;
  enemy_sprite.frame_count = 0;
  enemy_sprite.current_frame = 0;
  enemy_sprite.enabled = false;
}

static bool enemy_draw_sheet_frame(int center_x, int center_y, int *out_x, int *out_y, int *out_w, int *out_h, bool has_active_write) {
  if (!enemy_sprite.enabled || !enemy_sprite.pixels || enemy_sprite.frame_count <= 0) {
    return false;
  }

  int frame_w = enemy_sprite.frame_w;
  int frame_h = enemy_sprite.frame_h;
  if (frame_w <= 0 || frame_h <= 0 || enemy_sprite.sheet_w <= 0 || enemy_sprite.sheet_h <= 0) {
    return false;
  }

  int frames_per_row = enemy_sprite.sheet_w / frame_w;
  if (frames_per_row <= 0) {
    return false;
  }

  int frame_index = enemy_sprite.current_frame;
  if (frame_index < 0 || frame_index >= enemy_sprite.frame_count) {
    frame_index %= enemy_sprite.frame_count;
    if (frame_index < 0) {
      frame_index += enemy_sprite.frame_count;
    }
  }

  int src_col = frame_index % frames_per_row;
  int src_row = frame_index / frames_per_row;
  int src_x = src_col * frame_w;
  int src_y = src_row * frame_h;
  if (src_x < 0 || src_y < 0 || src_x + frame_w > enemy_sprite.sheet_w || src_y + frame_h > enemy_sprite.sheet_h) {
    return false;
  }

  int dst_x = center_x - frame_w / 2;
  int dst_y = center_y - frame_h / 2;
  int clip_x0 = dst_x < 0 ? 0 : dst_x;
  int clip_y0 = dst_y < 0 ? 0 : dst_y;
  int clip_x1 = dst_x + frame_w;
  int clip_y1 = dst_y + frame_h;
  if (clip_x1 > tile_state.view_w) {
    clip_x1 = tile_state.view_w;
  }
  if (clip_y1 > tile_state.view_h) {
    clip_y1 = tile_state.view_h;
  }
  if (clip_x0 >= clip_x1 || clip_y0 >= clip_y1) {
    if (out_x) {
      *out_x = dst_x;
    }
    if (out_y) {
      *out_y = dst_y;
    }
    if (out_w) {
      *out_w = frame_w;
    }
    if (out_h) {
      *out_h = frame_h;
    }
    return true;
  }

  int src_clip_x = clip_x0 - dst_x;
  int src_clip_y = clip_y0 - dst_y;
  int draw_w = clip_x1 - clip_x0;
  int draw_h = clip_y1 - clip_y0;
  const uint16_t *base = enemy_sprite.pixels + (size_t)src_y * (size_t)enemy_sprite.sheet_w + (size_t)src_x;

  bool opened_write = false;
  if (!has_active_write) {
    lcd.startWrite();
    opened_write = true;
  }
  size_t frame_pixels = (size_t)frame_w * (size_t)frame_h;
  size_t frame_offset = (size_t)frame_index * frame_pixels;
  for (int yy = 0; yy < draw_h; ++yy) {
    const uint16_t *row_base = base + (size_t)(src_clip_y + yy) * (size_t)enemy_sprite.sheet_w;
    const uint16_t *line = row_base + (size_t)src_clip_x;
    int run_start = -1;
    for (int xx = 0; xx < draw_w; ++xx) {
      size_t local_x = (size_t)(src_clip_x + xx);
      bool transparent = false;
      if (enemy_sprite.bg_mask && enemy_sprite.bg_mask_len > 0) {
        size_t local_y = (size_t)(src_clip_y + yy);
        size_t mask_idx = frame_offset + local_y * (size_t)frame_w + local_x;
        if (mask_idx < frame_pixels * (size_t)enemy_sprite.frame_count) {
          transparent = mask_bit_get(enemy_sprite.bg_mask, mask_idx);
        }
      } else {
        transparent = player_pixel_is_transparent(row_base[local_x]);
      }
      if (!transparent) {
        if (run_start < 0) {
          run_start = xx;
        }
      } else if (run_start >= 0) {
        int run_len = xx - run_start;
        lcd.pushImage(clip_x0 + run_start, clip_y0 + yy, run_len, 1, line + run_start);
        run_start = -1;
      }
    }
    if (run_start >= 0) {
      int run_len = draw_w - run_start;
      lcd.pushImage(clip_x0 + run_start, clip_y0 + yy, run_len, 1, line + run_start);
    }
  }
  if (opened_write) {
    lcd.endWrite();
  }

  if (out_x) {
    *out_x = dst_x;
  }
  if (out_y) {
    *out_y = dst_y;
  }
  if (out_w) {
    *out_w = frame_w;
  }
  if (out_h) {
    *out_h = frame_h;
  }
  return true;
}

static bool player_draw_sheet_frame(int center_x, int center_y, int *out_x, int *out_y, int *out_w, int *out_h, bool has_active_write) {
  if (!player_sprite.enabled || !player_sprite.pixels || player_sprite.frame_count <= 0) {
    return false;
  }

  int frame_w = player_sprite.frame_w;
  int frame_h = player_sprite.frame_h;
  if (frame_w <= 0 || frame_h <= 0 || player_sprite.sheet_w <= 0 || player_sprite.sheet_h <= 0) {
    return false;
  }

  int frames_per_row = player_sprite.sheet_w / frame_w;
  if (frames_per_row <= 0) {
    return false;
  }

  int frame_index = player_sprite.current_frame;
  if (frame_index < 0 || frame_index >= player_sprite.frame_count) {
    frame_index %= player_sprite.frame_count;
    if (frame_index < 0) {
      frame_index += player_sprite.frame_count;
    }
  }

  int src_col = frame_index % frames_per_row;
  int src_row = frame_index / frames_per_row;
  int src_x = src_col * frame_w;
  int src_y = src_row * frame_h;
  if (src_x < 0 || src_y < 0 || src_x + frame_w > player_sprite.sheet_w || src_y + frame_h > player_sprite.sheet_h) {
    return false;
  }

  int dst_x = center_x - frame_w / 2;
  int dst_y = center_y - frame_h / 2;
  int clip_x0 = dst_x < 0 ? 0 : dst_x;
  int clip_y0 = dst_y < 0 ? 0 : dst_y;
  int clip_x1 = dst_x + frame_w;
  int clip_y1 = dst_y + frame_h;
  if (clip_x1 > tile_state.view_w) {
    clip_x1 = tile_state.view_w;
  }
  if (clip_y1 > tile_state.view_h) {
    clip_y1 = tile_state.view_h;
  }
  if (clip_x0 >= clip_x1 || clip_y0 >= clip_y1) {
    if (out_x) {
      *out_x = dst_x;
    }
    if (out_y) {
      *out_y = dst_y;
    }
    if (out_w) {
      *out_w = frame_w;
    }
    if (out_h) {
      *out_h = frame_h;
    }
    return true;
  }

  int src_clip_x = clip_x0 - dst_x;
  int src_clip_y = clip_y0 - dst_y;
  int draw_w = clip_x1 - clip_x0;
  int draw_h = clip_y1 - clip_y0;
  const uint16_t *base = player_sprite.pixels + (size_t)src_y * (size_t)player_sprite.sheet_w + (size_t)src_x;

  bool opened_write = false;
  if (!has_active_write) {
    lcd.startWrite();
    opened_write = true;
  }
  size_t frame_pixels = (size_t)frame_w * (size_t)frame_h;
  size_t frame_offset = (size_t)frame_index * frame_pixels;
  bool flip_x = player_sprite.flip_x;
  uint16_t *flip_buf = nullptr;
  if (flip_x) {
    flip_buf = static_cast<uint16_t *>(std::malloc((size_t)draw_w * sizeof(uint16_t)));
    if (!flip_buf) {
      flip_x = false;
    }
  }
  for (int yy = 0; yy < draw_h; ++yy) {
    const uint16_t *row_base = base + (size_t)(src_clip_y + yy) * (size_t)player_sprite.sheet_w;
    const uint16_t *line = row_base + (size_t)src_clip_x;
    int run_start = -1;
    for (int xx = 0; xx < draw_w; ++xx) {
      size_t local_x = (size_t)(src_clip_x + xx);
      if (flip_x) {
        local_x = (size_t)(frame_w - 1) - local_x;
      }
      bool transparent = false;
      if (player_sprite.bg_mask && player_sprite.bg_mask_len > 0) {
        size_t local_y = (size_t)(src_clip_y + yy);
        size_t mask_idx = frame_offset + local_y * (size_t)frame_w + local_x;
        if (mask_idx < frame_pixels * (size_t)player_sprite.frame_count) {
          transparent = mask_bit_get(player_sprite.bg_mask, mask_idx);
        }
      } else {
        transparent = player_pixel_is_transparent(row_base[local_x]);
      }
      if (!transparent) {
        if (run_start < 0) {
          run_start = xx;
        }
      } else if (run_start >= 0) {
        int run_len = xx - run_start;
        if (!flip_x) {
          lcd.pushImage(clip_x0 + run_start, clip_y0 + yy, run_len, 1, line + run_start);
        } else {
          for (int i = 0; i < run_len; ++i) {
            size_t src_local_x = (size_t)(src_clip_x + run_start + i);
            src_local_x = (size_t)(frame_w - 1) - src_local_x;
            flip_buf[i] = row_base[src_local_x];
          }
          lcd.pushImage(clip_x0 + run_start, clip_y0 + yy, run_len, 1, flip_buf);
        }
        run_start = -1;
      }
    }
    if (run_start >= 0) {
      int run_len = draw_w - run_start;
      if (!flip_x) {
        lcd.pushImage(clip_x0 + run_start, clip_y0 + yy, run_len, 1, line + run_start);
      } else {
        for (int i = 0; i < run_len; ++i) {
          size_t src_local_x = (size_t)(src_clip_x + run_start + i);
          src_local_x = (size_t)(frame_w - 1) - src_local_x;
          flip_buf[i] = row_base[src_local_x];
        }
        lcd.pushImage(clip_x0 + run_start, clip_y0 + yy, run_len, 1, flip_buf);
      }
    }
  }
  if (flip_buf) {
    std::free(flip_buf);
  }
  if (opened_write) {
    lcd.endWrite();
  }

  if (out_x) {
    *out_x = dst_x;
  }
  if (out_y) {
    *out_y = dst_y;
  }
  if (out_w) {
    *out_w = frame_w;
  }
  if (out_h) {
    *out_h = frame_h;
  }
  return true;
}

static bool player_draw_sheet_frame_to_sprite(int center_x, int center_y, int *out_x, int *out_y, int *out_w, int *out_h) {
  if (!player_sprite.enabled || !player_sprite.pixels || player_sprite.frame_count <= 0) {
    return false;
  }

  int frame_w = player_sprite.frame_w;
  int frame_h = player_sprite.frame_h;
  if (frame_w <= 0 || frame_h <= 0 || player_sprite.sheet_w <= 0 || player_sprite.sheet_h <= 0) {
    return false;
  }

  int frames_per_row = player_sprite.sheet_w / frame_w;
  if (frames_per_row <= 0) {
    return false;
  }

  int frame_index = player_sprite.current_frame;
  if (frame_index < 0 || frame_index >= player_sprite.frame_count) {
    frame_index %= player_sprite.frame_count;
    if (frame_index < 0) {
      frame_index += player_sprite.frame_count;
    }
  }

  int src_col = frame_index % frames_per_row;
  int src_row = frame_index / frames_per_row;
  int src_x = src_col * frame_w;
  int src_y = src_row * frame_h;
  if (src_x < 0 || src_y < 0 || src_x + frame_w > player_sprite.sheet_w || src_y + frame_h > player_sprite.sheet_h) {
    return false;
  }

  int dst_x = center_x - frame_w / 2;
  int dst_y = center_y - frame_h / 2;
  int clip_x0 = dst_x < 0 ? 0 : dst_x;
  int clip_y0 = dst_y < 0 ? 0 : dst_y;
  int clip_x1 = dst_x + frame_w;
  int clip_y1 = dst_y + frame_h;
  if (clip_x1 > tile_state.view_w) {
    clip_x1 = tile_state.view_w;
  }
  if (clip_y1 > tile_state.view_h) {
    clip_y1 = tile_state.view_h;
  }
  if (clip_x0 >= clip_x1 || clip_y0 >= clip_y1) {
    if (out_x) {
      *out_x = dst_x;
    }
    if (out_y) {
      *out_y = dst_y;
    }
    if (out_w) {
      *out_w = frame_w;
    }
    if (out_h) {
      *out_h = frame_h;
    }
    return true;
  }

  int src_clip_x = clip_x0 - dst_x;
  int src_clip_y = clip_y0 - dst_y;
  int draw_w = clip_x1 - clip_x0;
  int draw_h = clip_y1 - clip_y0;
  const uint16_t *base = player_sprite.pixels + (size_t)src_y * (size_t)player_sprite.sheet_w + (size_t)src_x;

  size_t frame_pixels = (size_t)frame_w * (size_t)frame_h;
  size_t frame_offset = (size_t)frame_index * frame_pixels;
  bool flip_x = player_sprite.flip_x;
  uint16_t *flip_buf = nullptr;
  if (flip_x) {
    flip_buf = static_cast<uint16_t *>(std::malloc((size_t)draw_w * sizeof(uint16_t)));
    if (!flip_buf) {
      flip_x = false;
    }
  }
  for (int yy = 0; yy < draw_h; ++yy) {
    const uint16_t *row_base = base + (size_t)(src_clip_y + yy) * (size_t)player_sprite.sheet_w;
    const uint16_t *line = row_base + (size_t)src_clip_x;
    int run_start = -1;
    for (int xx = 0; xx < draw_w; ++xx) {
      size_t local_x = (size_t)(src_clip_x + xx);
      if (flip_x) {
        local_x = (size_t)(frame_w - 1) - local_x;
      }
      bool transparent = false;
      if (player_sprite.bg_mask && player_sprite.bg_mask_len > 0) {
        size_t local_y = (size_t)(src_clip_y + yy);
        size_t mask_idx = frame_offset + local_y * (size_t)frame_w + local_x;
        if (mask_idx < frame_pixels * (size_t)player_sprite.frame_count) {
          transparent = mask_bit_get(player_sprite.bg_mask, mask_idx);
        }
      } else {
        transparent = player_pixel_is_transparent(row_base[local_x]);
      }
      if (!transparent) {
        if (run_start < 0) {
          run_start = xx;
        }
      } else if (run_start >= 0) {
        int run_len = xx - run_start;
        if (!flip_x) {
          sprite.pushImage(clip_x0 + run_start, clip_y0 + yy, run_len, 1, line + run_start);
        } else {
          for (int i = 0; i < run_len; ++i) {
            size_t src_local_x = (size_t)(src_clip_x + run_start + i);
            src_local_x = (size_t)(frame_w - 1) - src_local_x;
            flip_buf[i] = row_base[src_local_x];
          }
          sprite.pushImage(clip_x0 + run_start, clip_y0 + yy, run_len, 1, flip_buf);
        }
        run_start = -1;
      }
    }
    if (run_start >= 0) {
      int run_len = draw_w - run_start;
      if (!flip_x) {
        sprite.pushImage(clip_x0 + run_start, clip_y0 + yy, run_len, 1, line + run_start);
      } else {
        for (int i = 0; i < run_len; ++i) {
          size_t src_local_x = (size_t)(src_clip_x + run_start + i);
          src_local_x = (size_t)(frame_w - 1) - src_local_x;
          flip_buf[i] = row_base[src_local_x];
        }
        sprite.pushImage(clip_x0 + run_start, clip_y0 + yy, run_len, 1, flip_buf);
      }
    }
  }
  if (flip_buf) {
    std::free(flip_buf);
  }

  if (out_x) {
    *out_x = dst_x;
  }
  if (out_y) {
    *out_y = dst_y;
  }
  if (out_w) {
    *out_w = frame_w;
  }
  if (out_h) {
    *out_h = frame_h;
  }
  return true;
}

static void player_draw_to_sprite(int center_x, int center_y, uint16_t color, int radius, int *out_x, int *out_y, int *out_w, int *out_h) {
  int new_x = 0;
  int new_y = 0;
  int new_w = 0;
  int new_h = 0;
  bool drew_sprite = player_draw_sheet_frame_to_sprite(center_x, center_y, &new_x, &new_y, &new_w, &new_h);
  if (!drew_sprite) {
    sprite.fillCircle(center_x, center_y, radius, color);
    new_x = center_x - radius;
    new_y = center_y - radius;
    new_w = radius * 2 + 1;
    new_h = radius * 2 + 1;
  }
  if (out_x) {
    *out_x = new_x;
  }
  if (out_y) {
    *out_y = new_y;
  }
  if (out_w) {
    *out_w = new_w;
  }
  if (out_h) {
    *out_h = new_h;
  }
}

static bool enemy_draw_sheet_frame_to_sprite(int center_x, int center_y, int frame_index, int *out_x, int *out_y, int *out_w, int *out_h) {
  if (!enemy_sprite.enabled || !enemy_sprite.pixels || enemy_sprite.frame_count <= 0) {
    return false;
  }

  int frame_w = enemy_sprite.frame_w;
  int frame_h = enemy_sprite.frame_h;
  if (frame_w <= 0 || frame_h <= 0 || enemy_sprite.sheet_w <= 0 || enemy_sprite.sheet_h <= 0) {
    return false;
  }

  int frames_per_row = enemy_sprite.sheet_w / frame_w;
  if (frames_per_row <= 0) {
    return false;
  }

  if (frame_index < 0 || frame_index >= enemy_sprite.frame_count) {
    frame_index %= enemy_sprite.frame_count;
    if (frame_index < 0) {
      frame_index += enemy_sprite.frame_count;
    }
  }

  int src_col = frame_index % frames_per_row;
  int src_row = frame_index / frames_per_row;
  int src_x = src_col * frame_w;
  int src_y = src_row * frame_h;
  if (src_x < 0 || src_y < 0 || src_x + frame_w > enemy_sprite.sheet_w || src_y + frame_h > enemy_sprite.sheet_h) {
    return false;
  }

  int dst_x = center_x - frame_w / 2;
  int dst_y = center_y - frame_h / 2;
  int clip_x0 = dst_x < 0 ? 0 : dst_x;
  int clip_y0 = dst_y < 0 ? 0 : dst_y;
  int clip_x1 = dst_x + frame_w;
  int clip_y1 = dst_y + frame_h;
  if (clip_x1 > tile_state.view_w) {
    clip_x1 = tile_state.view_w;
  }
  if (clip_y1 > tile_state.view_h) {
    clip_y1 = tile_state.view_h;
  }
  if (clip_x0 >= clip_x1 || clip_y0 >= clip_y1) {
    if (out_x) {
      *out_x = dst_x;
    }
    if (out_y) {
      *out_y = dst_y;
    }
    if (out_w) {
      *out_w = frame_w;
    }
    if (out_h) {
      *out_h = frame_h;
    }
    return true;
  }

  int src_clip_x = clip_x0 - dst_x;
  int src_clip_y = clip_y0 - dst_y;
  int draw_w = clip_x1 - clip_x0;
  int draw_h = clip_y1 - clip_y0;
  const uint16_t *base = enemy_sprite.pixels + (size_t)src_y * (size_t)enemy_sprite.sheet_w + (size_t)src_x;

  size_t frame_pixels = (size_t)frame_w * (size_t)frame_h;
  size_t frame_offset = (size_t)frame_index * frame_pixels;
  for (int yy = 0; yy < draw_h; ++yy) {
    const uint16_t *row_base = base + (size_t)(src_clip_y + yy) * (size_t)enemy_sprite.sheet_w;
    const uint16_t *line = row_base + (size_t)src_clip_x;
    int run_start = -1;
    for (int xx = 0; xx < draw_w; ++xx) {
      bool transparent = false;
      if (enemy_sprite.bg_mask && enemy_sprite.bg_mask_len > 0) {
        size_t local_y = (size_t)(src_clip_y + yy);
        size_t local_x = (size_t)(src_clip_x + xx);
        size_t mask_idx = frame_offset + local_y * (size_t)frame_w + local_x;
        if (mask_idx < frame_pixels * (size_t)enemy_sprite.frame_count) {
          transparent = mask_bit_get(enemy_sprite.bg_mask, mask_idx);
        }
      } else {
        transparent = player_pixel_is_transparent(line[xx]);
      }
      if (!transparent) {
        if (run_start < 0) {
          run_start = xx;
        }
      } else if (run_start >= 0) {
        sprite.pushImage(clip_x0 + run_start, clip_y0 + yy, xx - run_start, 1, line + run_start);
        run_start = -1;
      }
    }
    if (run_start >= 0) {
      sprite.pushImage(clip_x0 + run_start, clip_y0 + yy, draw_w - run_start, 1, line + run_start);
    }
  }

  if (out_x) {
    *out_x = dst_x;
  }
  if (out_y) {
    *out_y = dst_y;
  }
  if (out_w) {
    *out_w = frame_w;
  }
  if (out_h) {
    *out_h = frame_h;
  }
  return true;
}

static bool enemy_draw_to_sprite(int center_x, int center_y, int frame_index, int *out_x, int *out_y, int *out_w, int *out_h) {
  return enemy_draw_sheet_frame_to_sprite(center_x, center_y, frame_index, out_x, out_y, out_w, out_h);
}

static uint16_t *player_alloc_pixels(size_t len) {
  uint16_t *pixels = static_cast<uint16_t *>(heap_caps_malloc(len, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
  if (!pixels) {
    pixels = static_cast<uint16_t *>(std::malloc(len));
  }
  if (!pixels) {
    pixels = static_cast<uint16_t *>(heap_caps_malloc(len, MALLOC_CAP_8BIT));
  }
  return pixels;
}

static bool player_sheet_validate(size_t sheet_len, int sheet_w, int sheet_h, int frame_w, int frame_h, int *out_frame_count) {
  if (sheet_w <= 0 || sheet_h <= 0 || frame_w <= 0 || frame_h <= 0) {
    return false;
  }
  if (sheet_w % frame_w != 0 || sheet_h % frame_h != 0) {
    return false;
  }
  size_t expected_len = (size_t)sheet_w * (size_t)sheet_h * sizeof(uint16_t);
  if (expected_len != sheet_len) {
    return false;
  }
  int frames_x = sheet_w / frame_w;
  int frames_y = sheet_h / frame_h;
  int frame_count = frames_x * frames_y;
  if (frames_x <= 0 || frames_y <= 0 || frame_count <= 0) {
    return false;
  }
  if (out_frame_count) {
    *out_frame_count = frame_count;
  }
  return true;
}

struct PngSlotDecodeCtx {
  mp_obj_t file = MP_OBJ_NULL;
  uint16_t *pixels = nullptr;
  int w = 0;
  int h = 0;
};

static pngle_t *png_slot_decoder = nullptr;

static inline uint16_t rgb888_to_rgb565(uint8_t r, uint8_t g, uint8_t b) {
  return (uint16_t)(((r & 0xF8u) << 8) | ((g & 0xFCu) << 3) | (b >> 3));
}

static bool png_slot_valid_id(int slot_id) {
  return slot_id >= 0 && slot_id < MAX_PNG_SLOTS;
}

static void png_slot_reset_state(PngSlot *slot) {
  if (!slot) {
    return;
  }
  slot->pixels = nullptr;
  slot->w = 0;
  slot->h = 0;
  slot->valid = false;
}

static void png_slot_release_native(int slot_id) {
  if (!png_slot_valid_id(slot_id)) {
    return;
  }
  PngSlot *slot = &png_slots[slot_id];
  if (slot->pixels) {
    heap_caps_free(slot->pixels);
  }
  png_slot_reset_state(slot);
}

static uint32_t png_slot_read_callback(void *user_data, uint8_t *buf, uint32_t len) {
  auto *ctx = static_cast<PngSlotDecodeCtx *>(user_data);
  if (!ctx || ctx->file == MP_OBJ_NULL) {
    return 0;
  }
  if (len == 0) {
    return 0;
  }

  if (buf == nullptr) {
    int errcode = 0;
    mp_off_t seek_res = mp_stream_seek(ctx->file, len, MP_SEEK_CUR, &errcode);
    if (seek_res >= 0 && errcode == 0) {
      return len;
    }

    uint8_t scratch[32];
    uint32_t remain = len;
    while (remain) {
      uint32_t chunk = remain > sizeof(scratch) ? sizeof(scratch) : remain;
      int local_err = 0;
      mp_uint_t got = mp_stream_rw(ctx->file, scratch, chunk, &local_err, MP_STREAM_RW_READ);
      if (local_err != 0 || got == 0) {
        return len - remain;
      }
      remain -= got;
    }
    return len;
  }

  int errcode = 0;
  mp_uint_t got = mp_stream_rw(ctx->file, buf, len, &errcode, MP_STREAM_RW_READ);
  if (errcode != 0) {
    return 0;
  }
  return (uint32_t)got;
}

static void png_slot_draw_decode_callback(void *user_data, uint32_t x, uint32_t y, uint_fast8_t div_x, size_t len, const uint8_t *argb) {
  auto *ctx = static_cast<PngSlotDecodeCtx *>(user_data);
  if (!ctx || !ctx->pixels || !argb || ctx->w <= 0 || ctx->h <= 0) {
    return;
  }
  if ((int32_t)y < 0 || (int32_t)y >= ctx->h) {
    return;
  }

  size_t row_offset = (size_t)y * (size_t)ctx->w;
  for (size_t i = 0; i < len; ++i) {
    uint32_t px = x + (uint32_t)i * div_x;
    if ((int32_t)px < 0 || (int32_t)px >= ctx->w) {
      continue;
    }
    uint8_t a = argb[i * 4];
    uint8_t r = argb[i * 4 + 1];
    uint8_t g = argb[i * 4 + 2];
    uint8_t b = argb[i * 4 + 3];
    if (a != 255) {
      r = (uint8_t)((r * a + 255) >> 8);
      g = (uint8_t)((g * a + 255) >> 8);
      b = (uint8_t)((b * a + 255) >> 8);
    }
    ctx->pixels[row_offset + px] = rgb888_to_rgb565(r, g, b);
  }
}

static bool png_slot_decode_file(PngSlot *slot, const char *path) {
  if (!slot || !path) {
    return false;
  }

  mp_obj_t file = vfs_open_rb(path);
  if (file == MP_OBJ_NULL) {
    std::printf("png_slot_load_fail: open %s\n", path);
    return false;
  }

  if (png_slot_decoder == nullptr) {
    png_slot_decoder = lgfx_pngle_new();
  }
  if (png_slot_decoder == nullptr) {
    vfs_close_quiet(file);
    std::printf("png_slot_load_fail: decoder_alloc %s\n", path);
    return false;
  }

  PngSlotDecodeCtx ctx;
  ctx.file = file;
  if (lgfx_pngle_prepare(png_slot_decoder, png_slot_read_callback, &ctx) < 0) {
    vfs_close_quiet(file);
    std::printf("png_slot_load_fail: decode_prepare %s\n", path);
    return false;
  }

  int png_w = (int)lgfx_pngle_get_width(png_slot_decoder);
  int png_h = (int)lgfx_pngle_get_height(png_slot_decoder);
  if (png_w <= 0 || png_h <= 0) {
    vfs_close_quiet(file);
    std::printf("png_slot_load_fail: invalid_size %s\n", path);
    return false;
  }

  size_t pixel_count = (size_t)png_w * (size_t)png_h;
  size_t buf_len = pixel_count * sizeof(uint16_t);
  uint16_t *pixels = static_cast<uint16_t *>(heap_caps_malloc(buf_len, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
  if (!pixels) {
    pixels = static_cast<uint16_t *>(heap_caps_malloc(buf_len, MALLOC_CAP_8BIT));
  }
  if (!pixels) {
    vfs_close_quiet(file);
    std::printf("png_slot_load_fail: oom %s size=%zu\n", path, buf_len);
    return false;
  }
  memset(pixels, 0, buf_len);
  ctx.pixels = pixels;
  ctx.w = png_w;
  ctx.h = png_h;

  int res = lgfx_pngle_decomp(png_slot_decoder, png_slot_draw_decode_callback);
  vfs_close_quiet(file);
  if (res < 0) {
    heap_caps_free(pixels);
    std::printf("png_slot_load_fail: decode %s\n", path);
    return false;
  }

  slot->pixels = pixels;
  slot->w = png_w;
  slot->h = png_h;
  slot->valid = true;
  return true;
}

extern "C" void game_a_lgfx_init_impl(void) {
  lcd.init();
  lcd.setRotation(1);
  lcd.setSwapBytes(true);
  sprite.setSwapBytes(lcd.getSwapBytes());
  lcd.setBrightness(255);
  player_overlay.valid = false;
  enemy_overlay.valid = false;
  scene_epoch = 0;
  interact_hint_reset_storage();
}

extern "C" void game_a_lgfx_fill_impl(uint16_t color) {
  lcd.fillScreen(color);
}

extern "C" void game_a_lgfx_draw_text_impl(int x, int y, const char *text, uint16_t color) {
  if (!text) {
    return;
  }
  lcd.setTextFont(1);
  lcd.setTextSize(1);
  lcd.setTextColor(color, 0x0000);
  lcd.drawString(text, x, y);
}

extern "C" void game_a_lgfx_draw_rect_impl(int x, int y, int w, int h, uint16_t color) {
  if (w <= 0 || h <= 0) {
    return;
  }
  lcd.drawRect(x, y, w, h, color);
}

extern "C" void game_a_lgfx_draw_circle_impl(int x, int y, int r, uint16_t color) {
  if (r <= 0) {
    return;
  }
  lcd.fillCircle(x, y, r, color);
}

extern "C" void game_a_lgfx_clear_impl(void) {
  lcd.fillScreen(0);
}

extern "C" void game_a_lgfx_set_rotation_impl(int rotation) {
  lcd.setRotation(rotation);
}

extern "C" void game_a_lgfx_set_brightness_impl(int brightness) {
  lcd.setBrightness(brightness);
}

extern "C" void game_a_lgfx_set_swap_bytes_impl(bool swap) {
  lcd.setSwapBytes(swap);
  sprite.setSwapBytes(swap);
}

extern "C" void game_a_lgfx_sprite_create_impl(int w, int h, bool use_psram) {
  sprite.deleteSprite();
  sprite.setColorDepth(16);
  sprite.setPsram(use_psram);
  sprite.createSprite(w, h);
  sprite.setSwapBytes(lcd.getSwapBytes());
  sprite_ready = sprite.width() > 0 && sprite.height() > 0;
}

extern "C" void game_a_lgfx_sprite_fill_impl(uint16_t color) {
  if (!sprite_ready) {
    return;
  }
  sprite.fillScreen(color);
}

extern "C" void game_a_lgfx_sprite_push_impl(int x, int y) {
  if (!sprite_ready) {
    return;
  }
  sprite.pushSprite(x, y);
}

extern "C" bool game_a_lgfx_tile_setup_impl(int tile_size, int map_w, int map_h, int view_w, int view_h, bool use_psram) {
  if (tile_size <= 0 || map_w <= 0 || map_h <= 0 || view_w <= 0 || view_h <= 0) {
    return false;
  }

  tile_free_buffers();

  tile_state.tile_size = tile_size;
  tile_state.map_w = map_w;
  tile_state.map_h = map_h;
  tile_state.view_w = view_w;
  tile_state.view_h = view_h;
  tile_state.use_psram = use_psram;

  // Reserve the largest contiguous block first. This improves success rate
  // for full-screen sprite allocation when heap/PSRAM is fragmented.
  if (!ensure_sprite_size(view_w, view_h, use_psram)) {
    tile_free_buffers();
    return false;
  }

  size_t map_cells = (size_t)map_w * (size_t)map_h;
  if (!ensure_dirty_buffer(map_cells, use_psram)) {
    tile_free_buffers();
    return false;
  }

  tile_state.tileset = nullptr;
  tile_state.tilemap = nullptr;
  tile_state.loaded = false;
  tile_state.last_error = TILE_LOAD_OK;
  tile_state.has_prev_scroll = false;
  tile_state.active_slot_id = -1;

  return true;
}

extern "C" bool game_a_lgfx_tile_load_impl(const uint8_t *tileset_data, size_t tileset_len, const uint8_t *tilemap_data, size_t tilemap_len) {
  if (!tileset_data || !tilemap_data) {
    return tile_fail(TILE_LOAD_ERR_ARGS);
  }
  size_t map_cells = (size_t)tile_state.map_w * (size_t)tile_state.map_h;
  size_t expected_tilemap_len = map_cells * sizeof(uint16_t);
  if (tilemap_len != expected_tilemap_len) {
    return tile_fail(TILE_LOAD_ERR_MAP_READ);
  }
  size_t tile_pixels = (size_t)tile_state.tile_size * (size_t)tile_state.tile_size;
  size_t tile_bytes = tile_pixels * sizeof(uint16_t);
  if (tile_bytes == 0 || (tileset_len % tile_bytes) != 0) {
    return tile_fail(TILE_LOAD_ERR_TILESET_FORMAT);
  }
  size_t new_tile_count = tileset_len / tile_bytes;
  if (new_tile_count == 0) {
    return tile_fail(TILE_LOAD_ERR_TILESET_FORMAT);
  }
  if (!slot_id_valid(0)) {
    return tile_fail(TILE_LOAD_ERR_SLOT_RANGE);
  }
  if (tile_state.active_slot_id == 0) {
    tile_state.loaded = false;
    tile_state.active_slot_id = -1;
  }
  ResidentSlot *slot = &resident_slots[0];
  resident_slot_release_resources(slot);
  slot->state = SLOT_STATE_READY;
  slot->load_stage = SLOT_STAGE_READY;
  slot->role = slot->role == SLOT_ROLE_NONE ? SLOT_ROLE_ACTIVE : slot->role;
  slot->map_token = 0;
  slot->tileset_token = 0;
  slot->tile_size = tile_state.tile_size;
  slot->map_w = tile_state.map_w;
  slot->map_h = tile_state.map_h;
  slot->tilemap_bytes = tilemap_len;
  slot->tilemap_offset = tilemap_len;
  slot->loaded_bytes = tilemap_len + tileset_len;
  slot->total_bytes = slot->loaded_bytes;
  slot->use_psram = tile_state.use_psram;
  slot->tilemap_ptr = static_cast<uint16_t *>(lgfx_alloc(tilemap_len, tile_state.use_psram));
  if (!slot->tilemap_ptr) {
    resident_slot_reset(slot);
    return tile_fail(TILE_LOAD_ERR_CACHE_ALLOC);
  }
  memcpy(slot->tilemap_ptr, tilemap_data, tilemap_len);

  int cache_index = tileset_cache_find(0);
  if (cache_index >= 0 && (tileset_cache[cache_index].total_bytes != tileset_len || tileset_cache[cache_index].tile_bytes != tile_bytes)) {
    tileset_cache_reset(&tileset_cache[cache_index]);
    cache_index = -1;
  }
  if (cache_index < 0) {
    cache_index = tileset_cache_find_free();
  }
  if (cache_index < 0) {
    resident_slot_release_resources(slot);
    return tile_fail(TILE_LOAD_ERR_CACHE_ALLOC);
  }
  TilesetCacheEntry *cache = &tileset_cache[cache_index];
  if (!cache->ptr) {
    cache->ptr = static_cast<uint16_t *>(lgfx_alloc(tileset_len, tile_state.use_psram));
  }
  if (!cache->ptr) {
    resident_slot_release_resources(slot);
    tileset_cache_reset(cache);
    return tile_fail(TILE_LOAD_ERR_CACHE_ALLOC);
  }
  memcpy(cache->ptr, tileset_data, tileset_len);
  cache->tileset_token = 0;
  cache->total_bytes = tileset_len;
  cache->load_offset = tileset_len;
  cache->tile_count = new_tile_count;
  cache->tile_bytes = tile_bytes;
  cache->ref_count = 1;
  cache->waiter_count = 0;
  cache->state = CACHE_STATE_READY;
  cache->use_psram = tile_state.use_psram;
  slot->cache_index = cache_index;
  slot->cache_waiting = false;
  if (!resident_validate_tilemap_ids(slot, cache)) {
    resident_slot_release_resources(slot);
    return false;
  }
  return resident_activate_slot(0, true);
}

extern "C" bool game_a_lgfx_tile_set_impl(int tx, int ty, int tile_index) {
  if (!tile_state.loaded) {
    return false;
  }
  if (tx < 0 || ty < 0 || tx >= tile_state.map_w || ty >= tile_state.map_h) {
    return false;
  }
  if (tile_index < 0 || (size_t)tile_index >= tile_state.tile_count) {
    return false;
  }
  size_t idx = (size_t)ty * (size_t)tile_state.map_w + (size_t)tx;
  if (tile_state.tilemap[idx] != (uint16_t)tile_index) {
    tile_state.tilemap[idx] = (uint16_t)tile_index;
    tile_state.dirty[idx] = 1;
  }
  return true;
}

extern "C" bool game_a_lgfx_tile_load_files_impl(const char *tileset_path, const char *tilemap_path) {
  return game_a_lgfx_slot_load_files_impl(0, 0, 0, tileset_path, tilemap_path, tile_state.tile_size, tile_state.map_w, tile_state.map_h);
}

extern "C" int game_a_lgfx_tile_loader_mode_impl(void) {
  return 3;
}

extern "C" bool game_a_lgfx_slot_load_files_impl(int slot_id, uint32_t map_token, uint32_t tileset_token, const char *tileset_path, const char *tilemap_path, int tile_size, int map_w, int map_h) {
  if (!slot_id_valid(slot_id)) {
    return tile_fail(TILE_LOAD_ERR_SLOT_RANGE);
  }
  if (tile_state.active_slot_id == slot_id) {
    return tile_fail(TILE_LOAD_ERR_SLOT_ACTIVE);
  }
  ResidentSlot *slot = &resident_slots[slot_id];
  if (!resident_slot_prepare_load(slot, map_token, tileset_token, tileset_path, tilemap_path, tile_size, map_w, map_h)) {
    slot->state = SLOT_STATE_FAILED;
    slot->load_stage = SLOT_STAGE_NONE;
    return false;
  }
  int pumped = resident_slot_pump(slot, 0, true);
  if (pumped < 0 || slot->state != SLOT_STATE_READY) {
    slot->state = SLOT_STATE_FAILED;
    slot->load_stage = SLOT_STAGE_NONE;
    return false;
  }
  tile_state.last_error = TILE_LOAD_OK;
  return true;
}

extern "C" bool game_a_lgfx_slot_begin_load_files_impl(int slot_id, uint32_t map_token, uint32_t tileset_token, const char *tileset_path, const char *tilemap_path, int tile_size, int map_w, int map_h) {
  if (!slot_id_valid(slot_id)) {
    return tile_fail(TILE_LOAD_ERR_SLOT_RANGE);
  }
  if (tile_state.active_slot_id == slot_id) {
    return tile_fail(TILE_LOAD_ERR_SLOT_ACTIVE);
  }
  ResidentSlot *slot = &resident_slots[slot_id];
  if (!resident_slot_prepare_load(slot, map_token, tileset_token, tileset_path, tilemap_path, tile_size, map_w, map_h)) {
    slot->state = SLOT_STATE_FAILED;
    slot->load_stage = SLOT_STAGE_NONE;
    return false;
  }
  tile_state.last_error = TILE_LOAD_OK;
  return true;
}

extern "C" int game_a_lgfx_slot_pump_load_impl(int slot_id, size_t max_bytes) {
  if (!slot_id_valid(slot_id)) {
    tile_fail(TILE_LOAD_ERR_SLOT_RANGE);
    return -1;
  }
  if (tile_state.active_slot_id == slot_id) {
    tile_fail(TILE_LOAD_ERR_SLOT_ACTIVE);
    return -1;
  }
  ResidentSlot *slot = &resident_slots[slot_id];
  if (slot->state != SLOT_STATE_LOADING) {
    return 0;
  }
  int pumped = resident_slot_pump(slot, max_bytes, false);
  if (pumped < 0) {
    slot->state = SLOT_STATE_FAILED;
    slot->load_stage = SLOT_STAGE_NONE;
  }
  return pumped;
}

extern "C" bool game_a_lgfx_slot_cancel_load_impl(int slot_id) {
  if (!slot_id_valid(slot_id)) {
    return tile_fail(TILE_LOAD_ERR_SLOT_RANGE);
  }
  if (tile_state.active_slot_id == slot_id) {
    return tile_fail(TILE_LOAD_ERR_SLOT_ACTIVE);
  }
  ResidentSlot *slot = &resident_slots[slot_id];
  if (slot->state != SLOT_STATE_LOADING) {
    return tile_fail(TILE_LOAD_ERR_SLOT_STATE);
  }
  resident_slot_release_resources(slot);
  tile_state.last_error = TILE_LOAD_OK;
  return true;
}

extern "C" bool game_a_lgfx_slot_select_impl(int slot_id, bool force_full_redraw) {
  if (!slot_id_valid(slot_id)) {
    return tile_fail(TILE_LOAD_ERR_SLOT_RANGE);
  }
  if (resident_slots[slot_id].state != SLOT_STATE_READY) {
    return tile_fail(TILE_LOAD_ERR_SLOT_STATE);
  }
  if (!resident_activate_slot(slot_id, force_full_redraw)) {
    return false;
  }
  if (force_full_redraw) {
    tile_state.has_prev_scroll = false;
  }
  tile_state.last_error = TILE_LOAD_OK;
  return true;
}

extern "C" bool game_a_lgfx_slot_release_impl(int slot_id) {
  if (!slot_id_valid(slot_id)) {
    return tile_fail(TILE_LOAD_ERR_SLOT_RANGE);
  }
  if (tile_state.active_slot_id == slot_id) {
    return tile_fail(TILE_LOAD_ERR_SLOT_ACTIVE);
  }
  resident_slot_release_resources(&resident_slots[slot_id]);
  tile_state.last_error = TILE_LOAD_OK;
  return true;
}

extern "C" void game_a_lgfx_slot_release_all_impl(void) {
  tile_free_buffers();
  for (int i = 0; i < RESIDENT_SLOT_COUNT; ++i) {
    resident_slot_release_resources(&resident_slots[i]);
  }
  for (int i = 0; i < TILESET_CACHE_COUNT; ++i) {
    tileset_cache_reset(&tileset_cache[i]);
  }
  tile_state.last_error = TILE_LOAD_OK;
}

extern "C" bool game_a_lgfx_slot_has_map_impl(int slot_id, uint32_t map_token) {
  if (!slot_id_valid(slot_id)) {
    return false;
  }
  ResidentSlot *slot = &resident_slots[slot_id];
  return slot->state != SLOT_STATE_EMPTY && slot->map_token == map_token;
}

extern "C" bool game_a_lgfx_slot_info_impl(int slot_id, int *role, int *state, uint32_t *map_token, uint32_t *tileset_token, int *load_stage, size_t *loaded_bytes, size_t *total_bytes, int *ref_count, int *waiter_count, bool *is_active) {
  if (!slot_id_valid(slot_id)) {
    return false;
  }
  ResidentSlot *slot = &resident_slots[slot_id];
  TilesetCacheEntry *cache = (slot->cache_index >= 0 && slot->cache_index < TILESET_CACHE_COUNT) ? &tileset_cache[slot->cache_index] : nullptr;
  if (role) {
    *role = slot->role;
  }
  if (state) {
    *state = slot->state;
  }
  if (map_token) {
    *map_token = slot->map_token;
  }
  if (tileset_token) {
    *tileset_token = slot->tileset_token;
  }
  if (load_stage) {
    *load_stage = slot->load_stage;
  }
  if (loaded_bytes) {
    *loaded_bytes = slot->loaded_bytes;
  }
  if (total_bytes) {
    *total_bytes = slot->total_bytes;
  }
  if (ref_count) {
    *ref_count = cache ? cache->ref_count : 0;
  }
  if (waiter_count) {
    *waiter_count = cache ? cache->waiter_count : 0;
  }
  if (is_active) {
    *is_active = (tile_state.active_slot_id == slot_id);
  }
  return true;
}

extern "C" void game_a_lgfx_slot_set_role_impl(int slot_id, int role) {
  if (!slot_id_valid(slot_id)) {
    return;
  }
  resident_slots[slot_id].role = role;
}

extern "C" void game_a_lgfx_display_wait_idle_impl(void) {
  lcd.waitDMA();
  lcd.waitDisplay();
}

extern "C" int game_a_lgfx_tile_last_error_impl(void) {
  return tile_state.last_error;
}

extern "C" bool game_a_lgfx_player_sheet_load_impl(const uint8_t *sheet_data, size_t sheet_len, int sheet_w, int sheet_h, int frame_w, int frame_h) {
  if (!sheet_data) {
    return false;
  }
  int frame_count = 0;
  if (!player_sheet_validate(sheet_len, sheet_w, sheet_h, frame_w, frame_h, &frame_count)) {
    return false;
  }

  uint16_t *new_pixels = player_alloc_pixels(sheet_len);
  if (!new_pixels) {
    return false;
  }
  memcpy(new_pixels, sheet_data, sheet_len);

  uint8_t *new_mask = nullptr;
  size_t new_mask_len = 0;
  player_build_bg_mask(new_pixels, sheet_w, sheet_h, frame_w, frame_h, frame_count, &new_mask, &new_mask_len);

  if (player_sprite.pixels) {
    heap_caps_free(player_sprite.pixels);
  }
  if (player_sprite.bg_mask) {
    heap_caps_free(player_sprite.bg_mask);
  }
  player_sprite.pixels = new_pixels;
  player_sprite.pixels_len = sheet_len;
  player_sprite.bg_mask = new_mask;
  player_sprite.bg_mask_len = new_mask_len;
  player_sprite.sheet_w = sheet_w;
  player_sprite.sheet_h = sheet_h;
  player_sprite.frame_w = frame_w;
  player_sprite.frame_h = frame_h;
  player_sprite.frame_count = frame_count;
  player_sprite.current_frame = 0;
  player_sprite.enabled = true;
  return true;
}

extern "C" bool game_a_lgfx_player_sheet_load_file_impl(const char *sheet_path, int sheet_w, int sheet_h, int frame_w, int frame_h) {
  if (!sheet_path) {
    return false;
  }

  size_t expected_len = (size_t)sheet_w * (size_t)sheet_h * sizeof(uint16_t);
  int frame_count = 0;
  if (!player_sheet_validate(expected_len, sheet_w, sheet_h, frame_w, frame_h, &frame_count)) {
    return false;
  }

  mp_obj_t file = vfs_open_rb(sheet_path);
  if (file == MP_OBJ_NULL) {
    return false;
  }

  int errcode = 0;
  mp_off_t file_size = mp_stream_seek(file, 0, MP_SEEK_END, &errcode);
  if (file_size < 0 || errcode != 0 || (size_t)file_size != expected_len) {
    vfs_close_quiet(file);
    return false;
  }
  mp_off_t seek0 = mp_stream_seek(file, 0, MP_SEEK_SET, &errcode);
  if (seek0 < 0 || errcode != 0) {
    vfs_close_quiet(file);
    return false;
  }

  uint16_t *new_pixels = player_alloc_pixels(expected_len);
  if (!new_pixels) {
    vfs_close_quiet(file);
    return false;
  }
  bool read_ok = vfs_read_exact(file, new_pixels, expected_len);
  vfs_close_quiet(file);
  if (!read_ok) {
    heap_caps_free(new_pixels);
    return false;
  }

  uint8_t *new_mask = nullptr;
  size_t new_mask_len = 0;
  player_build_bg_mask(new_pixels, sheet_w, sheet_h, frame_w, frame_h, frame_count, &new_mask, &new_mask_len);

  if (player_sprite.pixels) {
    heap_caps_free(player_sprite.pixels);
  }
  if (player_sprite.bg_mask) {
    heap_caps_free(player_sprite.bg_mask);
  }
  player_sprite.pixels = new_pixels;
  player_sprite.pixels_len = expected_len;
  player_sprite.bg_mask = new_mask;
  player_sprite.bg_mask_len = new_mask_len;
  player_sprite.sheet_w = sheet_w;
  player_sprite.sheet_h = sheet_h;
  player_sprite.frame_w = frame_w;
  player_sprite.frame_h = frame_h;
  player_sprite.frame_count = frame_count;
  player_sprite.current_frame = 0;
  player_sprite.enabled = true;
  return true;
}

extern "C" void game_a_lgfx_player_frame_set_impl(int frame_index) {
  if (!player_sprite.enabled || player_sprite.frame_count <= 0) {
    return;
  }
  int norm = frame_index % player_sprite.frame_count;
  if (norm < 0) {
    norm += player_sprite.frame_count;
  }
  player_sprite.current_frame = norm;
}

extern "C" void game_a_lgfx_player_flip_x_set_impl(bool flip_x) {
  player_sprite.flip_x = flip_x;
}

extern "C" void game_a_lgfx_player_sheet_clear_impl(void) {
  player_sheet_release();
}

extern "C" bool game_a_lgfx_png_slot_load_file_impl(int slot_id, const char *path) {
  if (!png_slot_valid_id(slot_id) || !path || path[0] == '\0') {
    if (png_slot_valid_id(slot_id)) {
      png_slot_release_native(slot_id);
    }
    return false;
  }

  png_slot_release_native(slot_id);
  bool ok = png_slot_decode_file(&png_slots[slot_id], path);
  if (!ok) {
    png_slot_release_native(slot_id);
    return false;
  }

  std::printf("png_slot_load: %d %s %dx%d\n", slot_id, path, png_slots[slot_id].w, png_slots[slot_id].h);
  return true;
}

extern "C" bool game_a_lgfx_png_slot_draw_impl(int slot_id, int x, int y, int w, int h) {
  if (!png_slot_valid_id(slot_id)) {
    return false;
  }
  const PngSlot *slot = &png_slots[slot_id];
  if (!slot->valid || !slot->pixels || slot->w <= 0 || slot->h <= 0 || w <= 0 || h <= 0) {
    return false;
  }

  if (w == slot->w && h == slot->h) {
    lcd.startWrite();
    for (int yy = 0; yy < h; ++yy) {
      lcd.pushImage(x, y + yy, w, 1, slot->pixels + (size_t)yy * (size_t)slot->w);
    }
    lcd.endWrite();
    return true;
  }

  if (w > 320) {
    return false;
  }

  uint16_t line_buf[320];
  lcd.startWrite();
  for (int yy = 0; yy < h; ++yy) {
    int src_y = (yy * slot->h) / h;
    const uint16_t *src_row = slot->pixels + (size_t)src_y * (size_t)slot->w;
    for (int xx = 0; xx < w; ++xx) {
      int src_x = (xx * slot->w) / w;
      line_buf[xx] = src_row[src_x];
    }
    lcd.pushImage(x, y + yy, w, 1, line_buf);
  }
  lcd.endWrite();
  return true;
}

extern "C" void game_a_lgfx_png_slot_release_impl(int slot_id) {
  if (!png_slot_valid_id(slot_id)) {
    return;
  }
  if (png_slots[slot_id].pixels || png_slots[slot_id].valid) {
    std::printf("png_slot_release: %d\n", slot_id);
  }
  png_slot_release_native(slot_id);
}

extern "C" void game_a_lgfx_png_slot_release_all_impl(void) {
  for (int i = 0; i < MAX_PNG_SLOTS; ++i) {
    game_a_lgfx_png_slot_release_impl(i);
  }
}

extern "C" bool game_a_lgfx_enemy_sheet_load_file_impl(const char *sheet_path, int sheet_w, int sheet_h, int frame_w, int frame_h) {
  if (!sheet_path) {
    enemy_sheet_release();
    return false;
  }

  size_t expected_len = (size_t)sheet_w * (size_t)sheet_h * sizeof(uint16_t);
  int frame_count = 0;
  if (!player_sheet_validate(expected_len, sheet_w, sheet_h, frame_w, frame_h, &frame_count)) {
    enemy_sheet_release();
    return false;
  }

  mp_obj_t file = vfs_open_rb(sheet_path);
  if (file == MP_OBJ_NULL) {
    enemy_sheet_release();
    return false;
  }

  int errcode = 0;
  mp_off_t file_size = mp_stream_seek(file, 0, MP_SEEK_END, &errcode);
  if (file_size < 0 || errcode != 0 || (size_t)file_size != expected_len) {
    vfs_close_quiet(file);
    enemy_sheet_release();
    return false;
  }
  mp_off_t seek0 = mp_stream_seek(file, 0, MP_SEEK_SET, &errcode);
  if (seek0 < 0 || errcode != 0) {
    vfs_close_quiet(file);
    enemy_sheet_release();
    return false;
  }

  uint16_t *new_pixels = player_alloc_pixels(expected_len);
  if (!new_pixels) {
    vfs_close_quiet(file);
    enemy_sheet_release();
    return false;
  }
  bool read_ok = vfs_read_exact(file, new_pixels, expected_len);
  vfs_close_quiet(file);
  if (!read_ok) {
    heap_caps_free(new_pixels);
    enemy_sheet_release();
    return false;
  }

  uint8_t *new_mask = nullptr;
  size_t new_mask_len = 0;
  player_build_bg_mask(new_pixels, sheet_w, sheet_h, frame_w, frame_h, frame_count, &new_mask, &new_mask_len);

  enemy_sheet_release();
  enemy_sprite.pixels = new_pixels;
  enemy_sprite.pixels_len = expected_len;
  enemy_sprite.bg_mask = new_mask;
  enemy_sprite.bg_mask_len = new_mask_len;
  enemy_sprite.sheet_w = sheet_w;
  enemy_sprite.sheet_h = sheet_h;
  enemy_sprite.frame_w = frame_w;
  enemy_sprite.frame_h = frame_h;
  enemy_sprite.frame_count = frame_count;
  enemy_sprite.current_frame = 0;
  enemy_sprite.enabled = true;
  return true;
}

extern "C" void game_a_lgfx_enemy_frame_set_impl(int frame_index) {
  if (!enemy_sprite.enabled || enemy_sprite.frame_count <= 0) {
    return;
  }
  int norm = frame_index % enemy_sprite.frame_count;
  if (norm < 0) {
    norm += enemy_sprite.frame_count;
  }
  enemy_sprite.current_frame = norm;
}

extern "C" void game_a_lgfx_enemy_sheet_clear_impl(void) {
  enemy_sheet_release();
}

extern "C" void game_a_lgfx_enemy_overlay_clear_impl(void) {
  enemy_overlay_clear_state(false);
}

extern "C" bool game_a_lgfx_draw_png_file_impl(const char *path, int x, int y, int w, int h) {
  if (!path || w <= 0 || h <= 0) {
    return false;
  }

  mp_obj_t file = vfs_open_rb(path);
  if (file == MP_OBJ_NULL) {
    return false;
  }

  int errcode = 0;
  mp_off_t file_size = mp_stream_seek(file, 0, MP_SEEK_END, &errcode);
  if (file_size <= 0 || errcode != 0) {
    vfs_close_quiet(file);
    return false;
  }
  mp_off_t seek0 = mp_stream_seek(file, 0, MP_SEEK_SET, &errcode);
  if (seek0 < 0 || errcode != 0) {
    vfs_close_quiet(file);
    return false;
  }

  size_t png_len = (size_t)file_size;
  uint8_t *png_data = player_alloc_bytes(png_len);
  if (!png_data) {
    vfs_close_quiet(file);
    return false;
  }

  bool read_ok = vfs_read_exact(file, png_data, png_len);
  vfs_close_quiet(file);
  if (!read_ok) {
    heap_caps_free(png_data);
    return false;
  }

  bool ok = lcd.drawPng(png_data, (uint32_t)png_len, x, y, w, h, 0, 0, -1.0f, -1.0f);
  heap_caps_free(png_data);
  return ok;
}

extern "C" int game_a_lgfx_tile_render_impl(int scroll_x, int scroll_y, bool force_full) {
  if (!tile_state.loaded || !sprite_ready) {
    return 0;
  }

  render_compose_applied = false;

  mp_obj_t stream_file = MP_OBJ_NULL;
  if (tile_state.tileset_stream && tile_state.tileset_path[0] != '\0') {
    stream_file = vfs_open_rb(tile_state.tileset_path);
  }

  int64_t t0 = esp_timer_get_time();
  render_stats.last_tiles = 0;

  int prev_scroll_x = tile_state.prev_scroll_x;
  int prev_scroll_y = tile_state.prev_scroll_y;
  int dx_scroll = scroll_x - prev_scroll_x;
  int dy_scroll = scroll_y - prev_scroll_y;
  bool camera_scrolled = (dx_scroll != 0 || dy_scroll != 0);
  bool full_redraw = force_full || !tile_state.has_prev_scroll;
  bool try_scroll_opt = !full_redraw && camera_scrolled;
  bool compose_player = render_compose_player;
  bool compose_enemy = render_compose_enemy;
  int compose_rect_x = 0;
  int compose_rect_y = 0;
  int compose_rect_w = 0;
  int compose_rect_h = 0;
  int compose_enemy_rect_x = 0;
  int compose_enemy_rect_y = 0;
  int compose_enemy_rect_w = 0;
  int compose_enemy_rect_h = 0;
  int tile = tile_state.tile_size;
  int tiles_x = (tile_state.view_w + tile - 1) / tile + 1;
  int tiles_y = (tile_state.view_h + tile - 1) / tile + 1;
  int base_tx = scroll_x / tile;
  int base_ty = scroll_y / tile;
  int off_x = -(scroll_x % tile);
  int off_y = -(scroll_y % tile);

  if (full_redraw) {
    sprite.fillScreen(0x0000);
    for (int vy = 0; vy < tiles_y; ++vy) {
        int ty = base_ty + vy;
        int sy = off_y + vy * tile;
      for (int vx = 0; vx < tiles_x; ++vx) {
        int tx = base_tx + vx;
        int sx = off_x + vx * tile;
        draw_map_tile_to_sprite(tx, ty, sx, sy, stream_file);
        render_stats.last_tiles += 1;
      }
    }
    if (compose_enemy) {
      render_compose_enemy_applied = enemy_draw_to_sprite(render_compose_enemy_x, render_compose_enemy_y, render_compose_enemy_frame,
                                                          &compose_enemy_rect_x, &compose_enemy_rect_y, &compose_enemy_rect_w, &compose_enemy_rect_h);
    }
    if (compose_player) {
      player_draw_to_sprite(render_compose_player_x, render_compose_player_y, render_compose_player_color, render_compose_player_radius,
                            &compose_rect_x, &compose_rect_y, &compose_rect_w, &compose_rect_h);
      render_compose_applied = true;
    }
    sprite.pushSprite(0, 0);
    if (render_compose_applied) {
      redraw_map_rect_to_sprite(compose_rect_x, compose_rect_y, compose_rect_w, compose_rect_h, stream_file, scroll_x, scroll_y);
    }
    if (render_compose_enemy_applied) {
      redraw_map_rect_to_sprite(compose_enemy_rect_x, compose_enemy_rect_y, compose_enemy_rect_w, compose_enemy_rect_h, stream_file, scroll_x, scroll_y);
    }
    scene_epoch += 1;
    size_t map_cells = (size_t)tile_state.map_w * (size_t)tile_state.map_h;
    memset(tile_state.dirty, 0, map_cells);
    render_stats.full_frames += 1;
    player_overlay.valid = false;
    enemy_overlay.valid = false;
  } else if (try_scroll_opt && iabs(dx_scroll) < tile_state.view_w && iabs(dy_scroll) < tile_state.view_h) {
    // Scroll current sprite contents, then redraw only newly exposed strips + dirty tiles.
    if (enemy_overlay.valid) {
      redraw_map_rect_to_sprite(enemy_overlay.x, enemy_overlay.y, enemy_overlay.w, enemy_overlay.h, stream_file,
                                tile_state.prev_scroll_x, tile_state.prev_scroll_y);
      enemy_overlay.valid = false;
    }
    if (player_overlay.valid) {
      redraw_map_rect_to_sprite(player_overlay.x, player_overlay.y, player_overlay.w, player_overlay.h, stream_file,
                                tile_state.prev_scroll_x, tile_state.prev_scroll_y);
      player_overlay.valid = false;
      enemy_overlay.valid = false;
    }
    sprite.scroll(-dx_scroll, -dy_scroll);

    int exp_l = dx_scroll < 0 ? -dx_scroll : 0;
    int exp_r = dx_scroll > 0 ? dx_scroll : 0;
    int exp_t = dy_scroll < 0 ? -dy_scroll : 0;
    int exp_b = dy_scroll > 0 ? dy_scroll : 0;

    for (int vy = 0; vy < tiles_y; ++vy) {
      int ty = base_ty + vy;
      int sy = off_y + vy * tile;
      int y0 = sy;
      int y1 = sy + tile;
      for (int vx = 0; vx < tiles_x; ++vx) {
        int tx = base_tx + vx;
        int sx = off_x + vx * tile;
        int x0 = sx;
        int x1 = sx + tile;

        bool redraw = false;
        if (rect_intersects(x0, y0, x1, y1, 0, 0, exp_l, tile_state.view_h)) {
          redraw = true;
        } else if (rect_intersects(x0, y0, x1, y1, tile_state.view_w - exp_r, 0, exp_r, tile_state.view_h)) {
          redraw = true;
        } else if (rect_intersects(x0, y0, x1, y1, 0, 0, tile_state.view_w, exp_t)) {
          redraw = true;
        } else if (rect_intersects(x0, y0, x1, y1, 0, tile_state.view_h - exp_b, tile_state.view_w, exp_b)) {
          redraw = true;
        }

        if (tx >= 0 && ty >= 0 && tx < tile_state.map_w && ty < tile_state.map_h) {
          size_t map_idx = (size_t)ty * (size_t)tile_state.map_w + (size_t)tx;
          if (tile_state.dirty[map_idx]) {
            redraw = true;
          }
          if (redraw) {
            draw_map_tile_to_sprite(tx, ty, sx, sy, stream_file);
            tile_state.dirty[map_idx] = 0;
            render_stats.last_tiles += 1;
          }
        } else if (redraw) {
          draw_map_tile_to_sprite(tx, ty, sx, sy, stream_file);
          render_stats.last_tiles += 1;
        }
      }
    }
    if (compose_enemy) {
      render_compose_enemy_applied = enemy_draw_to_sprite(render_compose_enemy_x, render_compose_enemy_y, render_compose_enemy_frame,
                                                          &compose_enemy_rect_x, &compose_enemy_rect_y, &compose_enemy_rect_w, &compose_enemy_rect_h);
    }
    if (compose_player) {
      player_draw_to_sprite(render_compose_player_x, render_compose_player_y, render_compose_player_color, render_compose_player_radius,
                            &compose_rect_x, &compose_rect_y, &compose_rect_w, &compose_rect_h);
      render_compose_applied = true;
    }
    sprite.pushSprite(0, 0);
    if (render_compose_applied) {
      redraw_map_rect_to_sprite(compose_rect_x, compose_rect_y, compose_rect_w, compose_rect_h, stream_file, scroll_x, scroll_y);
    }
    if (render_compose_enemy_applied) {
      redraw_map_rect_to_sprite(compose_enemy_rect_x, compose_enemy_rect_y, compose_enemy_rect_w, compose_enemy_rect_h, stream_file, scroll_x, scroll_y);
    }
    scene_epoch += 1;
    render_stats.full_frames += 1;
    player_overlay.valid = false;
    enemy_overlay.valid = false;
  } else {
    int min_x = tile_state.view_w;
    int min_y = tile_state.view_h;
    int max_x = -1;
    int max_y = -1;
    for (int vy = 0; vy < tiles_y; ++vy) {
      int ty = base_ty + vy;
      if (ty < 0 || ty >= tile_state.map_h) {
        continue;
      }
      int sy = off_y + vy * tile;
      for (int vx = 0; vx < tiles_x; ++vx) {
        int tx = base_tx + vx;
        if (tx < 0 || tx >= tile_state.map_w) {
          continue;
        }
        size_t map_idx = (size_t)ty * (size_t)tile_state.map_w + (size_t)tx;
        if (!tile_state.dirty[map_idx]) {
          continue;
        }
        int sx = off_x + vx * tile;
        draw_map_tile_to_sprite(tx, ty, sx, sy, stream_file);
        tile_state.dirty[map_idx] = 0;
        render_stats.last_tiles += 1;

        int x0 = sx < 0 ? 0 : sx;
        int y0 = sy < 0 ? 0 : sy;
        int x1 = sx + tile > tile_state.view_w ? tile_state.view_w : sx + tile;
        int y1 = sy + tile > tile_state.view_h ? tile_state.view_h : sy + tile;
        if (x0 < x1 && y0 < y1) {
          if (x0 < min_x) {
            min_x = x0;
          }
          if (y0 < min_y) {
            min_y = y0;
          }
          if (x1 > max_x) {
            max_x = x1;
          }
          if (y1 > max_y) {
            max_y = y1;
          }
        }
      }
    }
    if (max_x > min_x && max_y > min_y) {
      push_rect_from_sprite_to_lcd(min_x, min_y, max_x - min_x, max_y - min_y);
      scene_epoch += 1;
    }
    render_stats.dirty_frames += 1;
  }

  tile_state.prev_scroll_x = scroll_x;
  tile_state.prev_scroll_y = scroll_y;
  tile_state.has_prev_scroll = true;
  render_stats.last_us = (uint32_t)(esp_timer_get_time() - t0);
  if (stream_file != MP_OBJ_NULL) {
    vfs_close_quiet(stream_file);
  }
  return full_redraw ? 2 : 1;
}

extern "C" int game_a_lgfx_tile_render_player_impl(int scroll_x, int scroll_y, int player_x, int player_y, uint16_t color, int radius, bool force_full) {
  if (radius <= 0) {
    radius = 1;
  }
  render_compose_player = true;
  render_compose_player_x = player_x;
  render_compose_player_y = player_y;
  render_compose_player_color = color;
  render_compose_player_radius = radius;

  int mode = game_a_lgfx_tile_render_impl(scroll_x, scroll_y, force_full);
  bool composed = render_compose_applied;

  render_compose_player = false;
  render_compose_applied = false;

  if (!composed) {
    game_a_lgfx_draw_player_impl(player_x, player_y, color, radius);
  }
  return mode;
}

extern "C" int game_a_lgfx_tile_render_player_enemy_impl(int scroll_x, int scroll_y, int player_x, int player_y, uint16_t color, int radius,
                                                  int enemy_x, int enemy_y, int enemy_frame, bool enemy_enabled, bool force_full) {
  if (radius <= 0) {
    radius = 1;
  }
  render_compose_player = true;
  render_compose_player_x = player_x;
  render_compose_player_y = player_y;
  render_compose_player_color = color;
  render_compose_player_radius = radius;
  render_compose_enemy = enemy_enabled;
  render_compose_enemy_x = enemy_x;
  render_compose_enemy_y = enemy_y;
  render_compose_enemy_frame = enemy_frame;
  render_compose_enemy_applied = false;

  int mode = game_a_lgfx_tile_render_impl(scroll_x, scroll_y, force_full);
  bool composed_player = render_compose_applied;

  render_compose_player = false;
  render_compose_applied = false;
  render_compose_enemy_applied = false;
  render_compose_enemy = false;

  if (!composed_player) {
    game_a_lgfx_draw_player_impl(player_x, player_y, color, radius);
  }
  return mode;
}

extern "C" void game_a_lgfx_draw_player_impl(int x, int y, uint16_t color, int radius) {
  if (radius <= 0) {
    return;
  }
  bool can_use_sprite = player_sprite.enabled && player_sprite.pixels && player_sprite.frame_count > 0;
  int frame_index = player_sprite.current_frame;
  bool flip_x = player_sprite.flip_x;
  if (player_overlay.valid &&
      player_overlay.center_x == x &&
      player_overlay.center_y == y &&
      player_overlay.radius == radius &&
      player_overlay.color == color &&
      player_overlay.used_sprite == can_use_sprite &&
      player_overlay.scene_epoch == scene_epoch) {
    bool same_frame = !can_use_sprite ||
      (player_overlay.frame_index == frame_index && player_overlay.flip_x == flip_x);
    if (same_frame) {
      return;
    }
  }
  if (!sprite_ready) {
    lcd.fillCircle(x, y, radius, color);
    return;
  }
  lcd.startWrite();
  if (player_overlay.valid) {
    bool redraw_enemy = enemy_overlay_intersects_rect(player_overlay.x, player_overlay.y, player_overlay.w, player_overlay.h);
    push_rect_from_sprite_to_lcd_locked(player_overlay.x, player_overlay.y, player_overlay.w, player_overlay.h);
    if (redraw_enemy) {
      redraw_enemy_overlay_locked();
    }
  }

  int new_x = 0;
  int new_y = 0;
  int new_w = 0;
  int new_h = 0;
  bool drew_sprite = player_draw_sheet_frame(x, y, &new_x, &new_y, &new_w, &new_h, true);
  if (!drew_sprite) {
    lcd.fillCircle(x, y, radius, color);
    new_x = x - radius;
    new_y = y - radius;
    new_w = radius * 2 + 1;
    new_h = radius * 2 + 1;
  }
  lcd.endWrite();

  player_overlay.valid = true;
  player_overlay.x = new_x;
  player_overlay.y = new_y;
  player_overlay.w = new_w;
  player_overlay.h = new_h;
  player_overlay.center_x = x;
  player_overlay.center_y = y;
  player_overlay.radius = radius;
  player_overlay.color = color;
  player_overlay.used_sprite = can_use_sprite;
  player_overlay.frame_index = frame_index;
  player_overlay.flip_x = flip_x;
  player_overlay.scene_epoch = scene_epoch;
}

extern "C" void game_a_lgfx_enemy_draw_impl(int x, int y) {
  bool can_use_sprite = enemy_sprite.enabled && enemy_sprite.pixels && enemy_sprite.frame_count > 0;
  int frame_index = enemy_sprite.current_frame;
  bool had_overlay = enemy_overlay.valid && enemy_overlay.scene_epoch == scene_epoch;
  int prev_x = enemy_overlay.x;
  int prev_y = enemy_overlay.y;
  int prev_w = enemy_overlay.w;
  int prev_h = enemy_overlay.h;
  if (enemy_overlay.valid &&
      enemy_overlay.center_x == x &&
      enemy_overlay.center_y == y &&
      enemy_overlay.used_sprite == can_use_sprite &&
      enemy_overlay.scene_epoch == scene_epoch) {
    bool same_frame = !can_use_sprite || (enemy_overlay.frame_index == frame_index);
    if (same_frame) {
      return;
    }
  }
  if (!sprite_ready || !can_use_sprite) {
    return;
  }

  lcd.startWrite();
  if (enemy_overlay.valid) {
    if (enemy_overlay.scene_epoch == scene_epoch) {
      push_rect_from_sprite_to_lcd_locked(enemy_overlay.x, enemy_overlay.y, enemy_overlay.w, enemy_overlay.h);
    }
    enemy_overlay.valid = false;
  }

  int new_x = 0;
  int new_y = 0;
  int new_w = 0;
  int new_h = 0;
  bool drew_sprite = enemy_draw_sheet_frame(x, y, &new_x, &new_y, &new_w, &new_h, true);
  if (!drew_sprite) {
    lcd.endWrite();
    enemy_overlay.valid = false;
    return;
  }
  bool redraw_player = false;
  if (had_overlay && player_overlay_intersects_rect(prev_x, prev_y, prev_w, prev_h)) {
    redraw_player = true;
  }
  if (player_overlay_intersects_rect(new_x, new_y, new_w, new_h)) {
    redraw_player = true;
  }
  if (redraw_player) {
    redraw_player_overlay_locked();
  }
  lcd.endWrite();

  enemy_overlay.valid = true;
  enemy_overlay.x = new_x;
  enemy_overlay.y = new_y;
  enemy_overlay.w = new_w;
  enemy_overlay.h = new_h;
  enemy_overlay.center_x = x;
  enemy_overlay.center_y = y;
  enemy_overlay.used_sprite = can_use_sprite;
  enemy_overlay.frame_index = frame_index;
  enemy_overlay.scene_epoch = scene_epoch;
}

extern "C" void game_a_lgfx_interact_hint_begin_impl(void) {
  interact_hint_finish_write();
  interact_hint_pending_count = 0;
  for (int i = 0; i < MAX_INTERACT_HINTS; ++i) {
    interact_hint_pending[i].valid = false;
  }
  if (!tile_state.loaded || !sprite_ready) {
    interact_hint_prev_count = 0;
    interact_hint_prev_scene_epoch = scene_epoch;
    return;
  }
  interact_hint_ensure_write();
  interact_hint_restore_previous_locked();
}

extern "C" void game_a_lgfx_interact_hint_rect_impl(int slot_id, int x, int y, int w, int h, int phase_step) {
  if (!tile_state.loaded || !sprite_ready || slot_id < 0 || slot_id >= MAX_INTERACT_HINTS || w <= 0 || h <= 0) {
    return;
  }
  if (interact_hint_pending_count >= MAX_INTERACT_HINTS) {
    return;
  }
  interact_hint_ensure_write();

  int pulse = interact_hint_phase_wave(phase_step);
  int outer_inset = 2 + (pulse / 2);
  int outer_x = x - outer_inset;
  int outer_y = y - outer_inset;
  int outer_w = w + outer_inset * 2;
  int outer_h = h + outer_inset * 2;
  int store_x = outer_x - 1;
  int store_y = outer_y - 1;
  int store_w = outer_w + 2;
  int store_h = outer_h + 2;
  if (!clip_rect_to_view(&store_x, &store_y, &store_w, &store_h)) {
    return;
  }

  const uint16_t gold_outer = 0xA3A0;
  const uint16_t gold_main = 0xFEA0;
  const uint16_t gold_inner = 0xFF6C;
  int corner_len = (w < h ? w : h) / 4;
  if (corner_len < 6) {
    corner_len = 6;
  }
  if (corner_len > 16) {
    corner_len = 16;
  }

  lcd.drawRect(outer_x, outer_y, outer_w, outer_h, gold_outer);
  lcd.drawRect(x, y, w, h, gold_main);
  if ((pulse & 1) == 1 && w > 4 && h > 4) {
    lcd.drawRect(x + 1, y + 1, w - 2, h - 2, gold_inner);
  }
  interact_hint_draw_corner(x, y, 1, 1, corner_len, gold_inner);
  interact_hint_draw_corner(x + w - 1, y, -1, 1, corner_len, gold_inner);
  interact_hint_draw_corner(x, y + h - 1, 1, -1, corner_len, gold_inner);
  interact_hint_draw_corner(x + w - 1, y + h - 1, -1, -1, corner_len, gold_inner);

  interact_hint_store_pending(slot_id, INTERACT_HINT_SHAPE_RECT, store_x, store_y, store_w, store_h, x, y, w, h, phase_step);
}

extern "C" void game_a_lgfx_interact_hint_circle_impl(int slot_id, int cx, int cy, int r, int phase_step) {
  if (!tile_state.loaded || !sprite_ready || slot_id < 0 || slot_id >= MAX_INTERACT_HINTS || r <= 0) {
    return;
  }
  if (interact_hint_pending_count >= MAX_INTERACT_HINTS) {
    return;
  }
  interact_hint_ensure_write();

  int pulse = interact_hint_phase_wave(phase_step);
  int inner_r = r + 1;
  int outer_r = r + 3 + (pulse / 2);
  int sparkle_gap = outer_r + 4;
  int sparkle_arm = 1 + (pulse / 2);
  int bbox_r = sparkle_gap + sparkle_arm + 1;
  int store_x = cx - bbox_r;
  int store_y = cy - bbox_r;
  int store_w = bbox_r * 2 + 1;
  int store_h = bbox_r * 2 + 1;
  if (!clip_rect_to_view(&store_x, &store_y, &store_w, &store_h)) {
    return;
  }

  const uint16_t gold_outer = 0xA3A0;
  const uint16_t gold_main = 0xFEA0;
  const uint16_t gold_inner = 0xFF6C;
  lcd.drawCircle(cx, cy, outer_r, gold_outer);
  lcd.drawCircle(cx, cy, inner_r, gold_main);
  if ((pulse & 1) == 0) {
    lcd.drawCircle(cx, cy, r, gold_inner);
  }
  interact_hint_draw_sparkle(cx, cy - sparkle_gap, sparkle_arm, gold_inner);
  interact_hint_draw_sparkle(cx + sparkle_gap, cy, sparkle_arm, gold_inner);
  interact_hint_draw_sparkle(cx, cy + sparkle_gap, sparkle_arm, gold_inner);
  interact_hint_draw_sparkle(cx - sparkle_gap, cy, sparkle_arm, gold_inner);

  interact_hint_store_pending(slot_id, INTERACT_HINT_SHAPE_CIRCLE, store_x, store_y, store_w, store_h, cx, cy, r, outer_r, phase_step);
}

extern "C" void game_a_lgfx_interact_hint_end_impl(void) {
  interact_hint_finish_write();
  interact_hint_prev_count = interact_hint_pending_count;
  interact_hint_prev_scene_epoch = scene_epoch;
  for (int i = 0; i < MAX_INTERACT_HINTS; ++i) {
    interact_hint_prev[i].valid = false;
  }
  for (int i = 0; i < interact_hint_pending_count; ++i) {
    interact_hint_prev[i] = interact_hint_pending[i];
  }
}

extern "C" void game_a_lgfx_interact_hint_clear_impl(void) {
  interact_hint_finish_write();
  if (tile_state.loaded && sprite_ready && interact_hint_prev_count > 0) {
    lcd.startWrite();
    interact_hint_write_active = true;
    interact_hint_restore_previous_locked();
    interact_hint_finish_write();
  }
  interact_hint_reset_storage();
}

extern "C" void game_a_lgfx_get_stats_impl(uint32_t *full_frames, uint32_t *dirty_frames, uint32_t *last_us, uint32_t *last_tiles) {
  if (full_frames) {
    *full_frames = render_stats.full_frames;
  }
  if (dirty_frames) {
    *dirty_frames = render_stats.dirty_frames;
  }
  if (last_us) {
    *last_us = render_stats.last_us;
  }
  if (last_tiles) {
    *last_tiles = render_stats.last_tiles;
  }
}

#endif
