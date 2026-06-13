// Stub header to provide ESP-IDF compatibility macros for LovyanGFX
// This allows LovyanGFX to compile without full ESP-IDF integration

#ifndef ESP_PLATFORM_STUB_H
#define ESP_PLATFORM_STUB_H

// ESP-IDF version macros (if not already defined)
#ifndef ESP_IDF_VERSION_MAJOR
#define ESP_IDF_VERSION_MAJOR 5
#endif

#ifndef ESP_IDF_VERSION_MINOR
#define ESP_IDF_VERSION_MINOR 2
#endif

#ifndef ESP_IDF_VERSION_PATCH
#define ESP_IDF_VERSION_PATCH 0
#endif

// Common ESP-IDF types that LovyanGFX might need
#include <stdint.h>
#include <stdbool.h>

// GPIO types
typedef unsigned int gpio_num_t;
#define GPIO_NUM_NC -1

// SPI types
typedef void* spi_device_handle_t;
typedef void* spi_host_device_t;
#define SPI2_HOST 1
#define SPI3_HOST 2

// DMA types
#define DMA_MAX 4095

// Board configuration stubs
#ifndef BOARD_HAS_PSRAM
#define BOARD_HAS_PSRAM 1
#endif

#endif // ESP_PLATFORM_STUB_H