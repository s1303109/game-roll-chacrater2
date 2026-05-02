import gc
import time
import lgfx


TEST_SECONDS = 120

lgfx.init()
lgfx.sprite_create(240, 320, True)

t0 = time.ticks_ms()
frames = 0
colors = (0xF800, 0x07E0, 0x001F, 0xFFFF, 0x0000)
ci = 0

while time.ticks_diff(time.ticks_ms(), t0) < TEST_SECONDS * 1000:
    lgfx.sprite_fill(colors[ci])
    lgfx.sprite_push(0, 0)
    ci = (ci + 1) % len(colors)
    frames += 1
    if frames % 300 == 0:
        gc.collect()
        print("frames", frames, "mem_free", gc.mem_free(), "stats", lgfx.stats())

elapsed = time.ticks_diff(time.ticks_ms(), t0)
print("stability done")
print("elapsed_ms:", elapsed)
print("frames:", frames)
print("fps:", (frames * 1000 / elapsed) if elapsed else 0)
print("final stats:", lgfx.stats())
