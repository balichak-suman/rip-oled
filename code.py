import time
import board
import busio
import psutil
import socket
import subprocess
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

# Initialize I2C and OLED
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

# Load fonts
font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)

# Function to get Wi-Fi IP (wlan0 or adapter with internet)
def get_ip():
    try:
        ip = subprocess.check_output("hostname -I", shell=True).decode().split()
        for address in ip:
            if address.startswith("10.") or address.startswith("192.") or address.startswith("172."):
                return address
        return "No WiFi"
    except Exception:
        return "No IP"

# Function to get CPU temperature
def get_temp():
    try:
        output = subprocess.check_output("vcgencmd measure_temp", shell=True).decode()
        return output.replace("temp=", "").strip()
    except Exception:
        return "N/A"

# Function to get CPU usage %
def get_cpu():
    return str(psutil.cpu_percent(interval=1)) + "%"

# Function to get Storage %
def get_storage():
    usage = psutil.disk_usage('/')
    return f"{usage.percent}%"

# Function to display centered text
def show_text(title, value):
    oled.fill(0)
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)

    # Title
    w_title, h_title = font_small.getbbox(title)[2:]
    draw.text(((oled.width - w_title) // 2, 5), title, font=font_small, fill=255)

    # Adjust font for long IPs only
    if title.lower().startswith("wi-fi") and len(value) > 12:
        font_used = font_medium
    else:
        font_used = font_large

    # Value
    w_value, h_value = font_used.getbbox(value)[2:]
    draw.text(((oled.width - w_value) // 2, (oled.height - h_value) // 2 + 10), value, font=font_used, fill=255)

    oled.image(image)
    oled.show()

# Main loop (cycle every 3 seconds)
while True:
    show_text("Wi-Fi IP", get_ip())
    time.sleep(3)
    show_text("CPU Temp", get_temp())
    time.sleep(3)
    show_text("CPU Usage", get_cpu())
    time.sleep(3)
    show_text("Storage", get_storage())
    time.sleep(3)
