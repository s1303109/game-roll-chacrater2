if(NOT DEFINED LGFX_DIR)
  set(LGFX_DIR "/workspace/LovyanGFX" CACHE PATH "Path to LovyanGFX")
endif()

add_library(usermod_lgfx INTERFACE)

target_sources(usermod_lgfx INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/lgfx_wrapper.c
    ${CMAKE_CURRENT_LIST_DIR}/lgfx_impl.cpp
    ${LGFX_DIR}/src/lgfx/utility/lgfx_pngle.c
    ${LGFX_DIR}/src/lgfx/utility/lgfx_miniz.c
    ${CMAKE_CURRENT_LIST_DIR}/lgfx_core_lgfxbase.cpp
    ${CMAKE_CURRENT_LIST_DIR}/lgfx_core_sprite.cpp
    ${CMAKE_CURRENT_LIST_DIR}/lgfx_core_button.cpp
    ${CMAKE_CURRENT_LIST_DIR}/lgfx_core_fonts.cpp
    ${CMAKE_CURRENT_LIST_DIR}/lgfx_core_common_function.cpp
    ${CMAKE_CURRENT_LIST_DIR}/lgfx_core_pixelcopy.cpp
    ${CMAKE_CURRENT_LIST_DIR}/lgfx_core_sprite_buffer.cpp
    ${CMAKE_CURRENT_LIST_DIR}/lgfx_core_divided_frame_buffer.cpp
    ${CMAKE_CURRENT_LIST_DIR}/lgfx_core_panel_device.cpp
    ${CMAKE_CURRENT_LIST_DIR}/lgfx_core_panel_lcd.cpp
    ${CMAKE_CURRENT_LIST_DIR}/lgfx_core_esp32_common.cpp
    ${CMAKE_CURRENT_LIST_DIR}/lgfx_core_esp32_bus_spi.cpp
    ${CMAKE_CURRENT_LIST_DIR}/lgfx_core_esp32_light_pwm.cpp
)

target_include_directories(usermod_lgfx INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
    ${LGFX_DIR}/src
    $ENV{IDF_PATH}/components/efuse/include
    $ENV{IDF_PATH}/components/efuse/esp32s3/include
)

target_compile_definitions(usermod_lgfx INTERFACE
    LGFX_USE_V1=1
    ESP_PLATFORM=1
)

target_link_libraries(usermod INTERFACE usermod_lgfx)
