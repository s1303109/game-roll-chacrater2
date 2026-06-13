include(${CMAKE_CURRENT_LIST_DIR}/shared_lovyangfx_core/micropython.cmake)
include(${CMAKE_CURRENT_LIST_DIR}/game_a_native/micropython.cmake)

if(EXISTS ${CMAKE_CURRENT_LIST_DIR}/game_b_native/micropython.cmake)
  include(${CMAKE_CURRENT_LIST_DIR}/game_b_native/micropython.cmake)
endif()

if(EXISTS ${CMAKE_CURRENT_LIST_DIR}/game_c_native/micropython.cmake)
  include(${CMAKE_CURRENT_LIST_DIR}/game_c_native/micropython.cmake)
endif()
