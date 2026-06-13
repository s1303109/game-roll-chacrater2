if(NOT DEFINED LGFX_DIR)
  set(LGFX_DIR "/workspace/LovyanGFX" CACHE PATH "Path to LovyanGFX")
endif()

add_library(usermod_game_a_native INTERFACE)

target_sources(usermod_game_a_native INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/lgfx_wrapper.c
    ${CMAKE_CURRENT_LIST_DIR}/lgfx_impl.cpp
)

target_include_directories(usermod_game_a_native INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
    ${LGFX_DIR}/src
    $ENV{IDF_PATH}/components/efuse/include
    $ENV{IDF_PATH}/components/efuse/esp32s3/include
)

target_compile_definitions(usermod_game_a_native INTERFACE
    LGFX_USE_V1=1
    ESP_PLATFORM=1
)

target_link_libraries(usermod_game_a_native INTERFACE usermod_shared_lovyangfx_core)
target_link_libraries(usermod INTERFACE usermod_game_a_native)
