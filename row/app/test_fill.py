import time
import lgfx

lgfx.init()

t0 = time.ticks_ms()
for _ in range(10):
    lgfx.fill(0xF800)
    lgfx.fill(0x001F)

t1 = time.ticks_ms()
print("FPS:", 1000 / ((t1 - t0) / 20))
