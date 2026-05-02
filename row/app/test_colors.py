import time
import lgfx

lgfx.init()

while True:
    lgfx.fill(0xF800)
    time.sleep(1)
    lgfx.fill(0x07E0)
    time.sleep(1)
    lgfx.fill(0x001F)
    time.sleep(1)
