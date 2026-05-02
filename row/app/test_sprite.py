import time
import lgfx

lgfx.init()
lgfx.sprite_create(240, 320, True)

t0 = time.ticks_ms()
for _ in range(20):
    lgfx.sprite_fill(0xF800)
    lgfx.sprite_push(0, 0)

t1 = time.ticks_ms()
print("FPS:", 1000 / ((t1 - t0) / 20))
