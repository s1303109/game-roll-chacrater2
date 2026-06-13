/*
 * Minimal ILI9341 TFT Display Driver for MicroPython on ESP32-S3
 * Uses ESP-IDF SPI driver directly
 */

#include "py/runtime.h"
#include "py/mphal.h"
#include "extmod/machine_spi.h"

#include <string.h>
#include <stdio.h>

// ILI9341 Commands
#define ILI9341_NOP         0x00
#define ILI9341_SLEEP_IN    0x10
#define ILI9341_SLEEP_OUT   0x11
#define ILI9341_PTLON       0x12
#define ILI9341_NORM_OFF    0x13
#define ILI9341_INV_ON      0x21
#define ILI9341_INV_OFF     0x20
#define ILI9341_GAMMA_SET   0x26
#define ILI9341_DISPLAY_OFF 0x28
#define ILI9341_DISPLAY_ON  0x29
#define ILI9341_COL_ADDR    0x2A
#define ILI9341_PAGE_ADDR   0x2B
#define ILI9341_GRAM        0x2C
#define ILI9341_MADCTL      0x36
#define ILI9341_PIX_FMT     0x3A
#define ILI9341_FRM_CTRL1   0xB1
#define ILI9341_DISP_FUNC   0xB6
#define ILI9341_ENTRY_MODE  0xB7
#define ILI9341_POWER_CTRL1 0xC0
#define ILI9341_POWER_CTRL2 0xC1
#define ILI9341_VCOM_CTRL1  0xC5
#define ILI9341_VCOM_CTRL2  0xC7
#define ILI9341_PWR_CTLA    0xD0
#define ILI9341_PWR_CTLB    0xD1
#define ILI9341_TIM_CTRL    0xD9
#define ILI9341_VCOM        0xDE
#define ILI9341_PWR_SEQ     0xE8
#define ILI9341_DGAM_SLICE 0xE2
#define ILI9341_HORZ_START 0x2A
#define ILI9341_HORZ_END    0x2B
#define ILI9341_VERT_START 0x2C
#define ILI9341_VERT_END    0x2D

// Display dimensions
#define ILI9341_WIDTH  240
#define ILI9341_HEIGHT 320

// Pin definitions (customizable)
#define TFT_CS_PIN   15
#define TFT_DC_PIN   16
#define TFT_RST_PIN  17
#define TFT_MOSI_PIN 13
#define TFT_MISO_PIN 12
#define TFT_CLK_PIN  14

// SPI handle (will be initialized)
static void *spi_handle = NULL;
static uint16_t framebuffer[ILI9341_WIDTH * ILI9341_HEIGHT];

// Forward declarations
static void ili9341_write_command(uint8_t cmd);
static void ili9341_write_data(const uint8_t *data, size_t len);
static void ili9341_set_window(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2);

// SPI transaction
static void ili9341_write_command(uint8_t cmd) {
    // Set DC low for command
    mp_hal_pin_write(TFT_DC_PIN, 0);
    
    // In real implementation, use ESP-IDF SPI functions
    // For now, this is a placeholder
}

static void ili9341_write_data(const uint8_t *data, size_t len) {
    // Set DC high for data
    mp_hal_pin_write(TFT_DC_PIN, 1);
    
    // In real implementation, use ESP-IDF SPI functions
}

static void ili9341_set_window(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2) {
    uint8_t data[4];
    
    data[0] = (x1 >> 8) & 0xFF;
    data[1] = x1 & 0xFF;
    data[2] = (x2 >> 8) & 0xFF;
    data[3] = x2 & 0xFF;
    ili9341_write_command(ILI9341_COL_ADDR);
    ili9341_write_data(data, 4);
    
    data[0] = (y1 >> 8) & 0xFF;
    data[1] = y1 & 0xFF;
    data[2] = (y2 >> 8) & 0xFF;
    data[3] = y2 & 0xFF;
    ili9341_write_command(ILI9341_PAGE_ADDR);
    ili9341_write_data(data, 4);
}

// MicroPython bindings
typedef struct {
    mp_obj_base_t base;
    uint16_t width;
    uint16_t height;
} ILI9341_obj;

STATIC mp_obj_t ili9341_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) {
    ILI9341_obj *self = m_new_obj(ILI9341_obj);
    self->base.type = type;
    self->width = ILI9341_WIDTH;
    self->height = ILI9341_HEIGHT;
    return MP_OBJ_FROM_PTR(self);
}

STATIC mp_obj_t ili9341_init(mp_obj_t self_obj) {
    // Initialize SPI and display
    uint8_t init_seq[] = {
        0x01, 0x00,  // SWRESET
        0x11, 0x00,  // SLPOUT
        0x3A, 0x01, 0x55,  // PIXFMT (16-bit)
        0x36, 0x01, 0x00,  // MADCTL
        0x29, 0x00,  // DISPON
    };
    
    // Send initialization sequence
    for (size_t i = 0; i < sizeof(init_seq); i += 2) {
        ili9341_write_command(init_seq[i]);
        if (i + 1 < sizeof(init_seq)) {
            uint8_t data = init_seq[i + 1];
            ili9341_write_data(&data, 1);
        }
    }
    
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(ili9341_init_obj, ili9341_init);

STATIC mp_obj_t ili9341_fill(mp_obj_t self_obj, mp_obj_t color_obj) {
    mp_int_t color = mp_obj_get_int(color_obj);
    
    // Set full window
    ili9341_set_window(0, 0, ILI9341_WIDTH - 1, ILI9341_HEIGHT - 1);
    ili9341_write_command(ILI9341_GRAM);
    
    // Fill with color (RGB565)
    uint8_t hi = (color >> 8) & 0xFF;
    uint8_t lo = color & 0xFF;
    
    // In real implementation, send pixel data via SPI
    // For now, update framebuffer
    for (size_t i = 0; i < ILI9341_WIDTH * ILI9341_HEIGHT; i++) {
        framebuffer[i] = color;
    }
    
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(ili9341_fill_obj, ili9341_fill);

STATIC mp_obj_t ili9341_pixel(mp_obj_t self_obj, mp_obj_t x_obj, mp_obj_t y_obj, mp_obj_t color_obj) {
    mp_int_t x = mp_obj_get_int(x_obj);
    mp_int_t y = mp_obj_get_int(y_obj);
    mp_int_t color = mp_obj_get_int(color_obj);
    
    if (x >= 0 && x < ILI9341_WIDTH && y >= 0 && y < ILI9341_HEIGHT) {
        framebuffer[y * ILI9341_WIDTH + x] = color;
    }
    
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_4(ili9341_pixel_obj, ili9341_pixel);

STATIC mp_obj_t ili9341_width_func(mp_obj_t self_obj) {
    return MP_OBJ_NEW_SMALL_INT(ILI9341_WIDTH);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(ili9341_width_obj, ili9341_width_func);

STATIC mp_obj_t ili9341_height_func(mp_obj_t self_obj) {
    return MP_OBJ_NEW_SMALL_INT(ILI9341_HEIGHT);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(ili9341_height_obj, ili9341_height_func);

STATIC const mp_rom_map_elem_t ili9341_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_init), MP_ROM_PTR(&ili9341_init_obj) },
    { MP_ROM_QSTR(MP_QSTR_fill), MP_ROM_PTR(&ili9341_fill_obj) },
    { MP_ROM_QSTR(MP_QSTR_pixel), MP_ROM_PTR(&ili9341_pixel_obj) },
    { MP_ROM_QSTR(MP_QSTR_width), MP_ROM_PTR(&ili9341_width_obj) },
    { MP_ROM_QSTR(MP_QSTR_height), MP_ROM_PTR(&ili9341_height_obj) },
};

STATIC MP_DEFINE_CONST_DICT(ili9341_locals_dict, ili9341_locals_dict_table);

STATIC const mp_obj_type_t ili9341_type = {
    { &mp_type_type },
    .name = MP_QSTR_ILI9341,
    .make_new = ili9341_make_new,
    .locals_dict = (mp_obj_t)&ili9341_locals_dict,
};

// Module globals
STATIC const mp_rom_map_elem_t ili9341_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_ili9341) },
    { MP_ROM_QSTR(MP_QSTR_ILI9341), MP_ROM_PTR(&ili9341_type) },
};

STATIC MP_DEFINE_CONST_DICT(ili9341_module_globals, ili9341_module_globals_table);

const mp_obj_module_t ili9341_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_t)&ili9341_module_globals,
};

// Register module
MP_REGISTER_MODULE(MP_QSTR_ili9341, ili9341_module);