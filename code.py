#!/usr/bin/env python3
import time
import psutil
import socket
from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306

# Initialize I2C and OLED
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, rotate=0)

# Fonts
font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)

def get_ip():
    """Return IP address from wlan0 or wlan1, whichever has internet"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "No IP"

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_temp():
    """Get CPU temperature in °C"""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_c = int(f.read()) / 1000
        return temp_c
    except:
        return 0.0

def get_disk():
    """Get used and total disk space in MB"""
    disk = psutil.disk_usage('/')
    return (disk.used // (1024 * 1024), disk.total // (1024 * 1024))

while True:
    ip = get_ip()
    cpu = get_cpu_usage()
    temp = get_temp()
    used, total = get_disk()

    image = Image.new("1", (device.width, device.height))
    draw = ImageDraw.Draw(image)

    # --- Center IP address at top ---
    ip_w, ip_h = draw.textbbox((0, 0), ip, font=font_big)[2:]
    draw.text(((device.width - ip_w) // 2, -2), ip, font=font_big, fill=255)

    # --- System stats below ---
    lines = [
        f"CPU: {cpu:.1f}%",
        f"Temp: {temp:.1f}°C",
        f"Disk: {used}/{total} MB"
    ]

    y = ip_h + 2
    for line in lines:
        w, h = draw.textbbox((0, 0), line, font=font_small)[2:]
        draw.text(((device.width - w) // 2, y), line, font=font_small, fill=255)
        y += h + 1

    device.display(image)
    time.sleep(3)
