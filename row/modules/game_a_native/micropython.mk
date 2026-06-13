LGFX_MOD_DIR := $(USERMOD_DIR)

SRC_USERMOD_C += $(LGFX_MOD_DIR)/lgfx_wrapper.c
SRC_USERMOD_CXX += $(LGFX_MOD_DIR)/lgfx_impl.cpp

CFLAGS_USERMOD += -I$(LGFX_MOD_DIR)
CXXFLAGS_USERMOD += -I$(LGFX_MOD_DIR) -DLGFX_USE_V1=1

# If you build via Make, add the LovyanGFX include path, for example:
# CXXFLAGS_USERMOD += -I/path/to/LovyanGFX/src
