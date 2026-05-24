import os
from machine import Pin, SDCard, SPI

# Fixed bus assignment for this project.
TFT_SPI_HOST = 2  # SPI2 / HSPI
SD_SPI_HOST = 3   # SPI3 / VSPI

# On MicroPython ESP32 port, SPI SDCard slots map as:
# slot=2 -> SPI3(VSPI), slot=3 -> SPI2(HSPI)
SD_SLOT = 2

SD_PIN_SCK = 5
SD_PIN_MOSI = 6
SD_PIN_MISO = 7
SD_PIN_CS = 4

# Keep mounted SDCard handles alive; otherwise GC may reclaim them and
# break /sd access mid-session on some boards/firmware builds.
_MOUNTED_SD = {}


def _is_busy_error(err):
    try:
        if err.errno == 16:
            return True
    except AttributeError:
        pass
    try:
        return bool(err.args) and err.args[0] == 16
    except Exception:
        return False


def _is_invalid_state_error(err):
    try:
        if err.errno in (-259, 259):
            return True
    except AttributeError:
        pass
    try:
        return bool(err.args) and err.args[0] in (-259, 259)
    except Exception:
        pass
    return "ESP_ERR_INVALID_STATE" in str(err)


def _mount_ready(mount_point):
    try:
        os.listdir(mount_point)
        return True
    except OSError:
        return False


def _deinit_sd_spi():
    try:
        spi = SPI(SD_SPI_HOST)
        spi.deinit()
        return True
    except Exception:
        return False


def _create_sd(freq):
    return SDCard(
        slot=SD_SLOT,
        sck=Pin(SD_PIN_SCK),
        mosi=Pin(SD_PIN_MOSI),
        miso=Pin(SD_PIN_MISO),
        cs=Pin(SD_PIN_CS),
        freq=freq,
    )


def mount_sd(mount_point="/sd", freq=8_000_000, return_ok=False):
    global _MOUNTED_SD
    if mount_point in _MOUNTED_SD and _mount_ready(mount_point):
        if return_ok:
            return True
        return _MOUNTED_SD[mount_point]
    try:
        sd = _create_sd(freq)
    except OSError as err:
        if _is_invalid_state_error(err):
            if _deinit_sd_spi():
                try:
                    sd = _create_sd(freq)
                except OSError as err2:
                    if _is_invalid_state_error(err2):
                        if return_ok:
                            return _mount_ready(mount_point)
                        return None
                    raise
            else:
                if return_ok:
                    return _mount_ready(mount_point)
                return None
        raise
    try:
        os.stat(mount_point)
    except OSError:
        os.mkdir(mount_point)
    mounted = False
    try:
        os.mount(sd, mount_point)
        mounted = True
    except OSError as err:
        # Already mounted in current REPL session.
        if _is_busy_error(err) or _is_invalid_state_error(err):
            mounted = _mount_ready(mount_point)
    if mounted:
        _MOUNTED_SD[mount_point] = sd
    if return_ok:
        return mounted
    return _MOUNTED_SD.get(mount_point, sd)
