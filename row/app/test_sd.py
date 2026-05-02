from machine import Pin, SDCard
import os

sd = SDCard(slot=2, sck=Pin(5), mosi=Pin(6), miso=Pin(7), cs=Pin(4))
os.mount(sd, "/sd")

with open("/sd/test.bin", "rb") as f:
    f.read(4096)

print("sd ok")
