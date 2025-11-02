Raspberry Pi OLED System Stats Display (Full Documentation)
=====================================================

Overview
--------
This project displays real-time system information (Wi-Fi IP, CPU usage, memory, disk, and temperature)
on a 0.96” SSD1306 OLED (I²C) connected to a Raspberry Pi running Kali Linux. It updates every 3 seconds,
one stat at a time, with large readable text — and it auto-starts at boot.

Hardware Requirements
---------------------
- Raspberry Pi (Zero, Zero 2 W, 3, 4, etc.)
- SSD1306 128×64 I²C OLED display
- Jumper wires (Female–Female)
- Breadboard (optional)
- Power source:
  - 3.7V Li-ion battery
  - TP4056 charging module
  - MT3608 boost converter (for 5V output)

OLED Connections (I²C)
----------------------
OLED Pin | Connects To Raspberry Pi Pin | GPIO Name | Notes
---------|------------------------------|------------|--------
VCC      | Pin 1 (3.3V) or Pin 2 (5V)   | 3V3 / 5V   | Use 3.3V for safety
GND      | Pin 6                        | GND        | Ground
SCL      | Pin 5                        | GPIO3 (SCL) | I²C Clock
SDA      | Pin 3                        | GPIO2 (SDA) | I²C Data

Run: sudo i2cdetect -y 1
Expected address: 0x3C

Safe Battery Powering Guide
---------------------------
To power your Pi directly from a battery safely:

Components:
- 18650 Li-ion battery (3.7V)
- TP4056 — charging & protection module
- MT3608 — boost converter (steps 3.7V → 5V)

Wiring:
Battery + → TP4056 B+
Battery - → TP4056 B-
TP4056 OUT+ → MT3608 IN+
TP4056 OUT- → MT3608 IN-
MT3608 OUT+ → Pi 5V pin (Pin 2 or 4)
MT3608 OUT- → Pi GND (Pin 6)

Adjust MT3608 output to 5.1V before connecting it to the Pi.

Software Setup
---------------
1. Enable I²C
   sudo apt update
   sudo apt install -y i2c-tools
   sudo raspi-config nonint do_i2c 0

2. Create Project Folder and Virtual Environment
   cd ~
   mkdir oled_display && cd oled_display
   python3 -m venv oled-env
   source oled-env/bin/activate

3. Install Required Libraries
   pip install Adafruit-Blinka adafruit-circuitpython-ssd1306 pillow psutil RPi.GPIO

4. Create OLED Display Script
   nano system_stats_cycle.py

Paste this code:

-------------------------------------------------------
import time
import subprocess
import psutil
import board
import busio
import socket
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

# --- OLED setup ---
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
oled.fill(0)
oled.show()

# --- Font setup ---
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
font_large = ImageFont.truetype(font_path, 20)
font_small = ImageFont.load_default()

def get_text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def get_ip():
    try:
        ip = subprocess.check_output(
            "ip -4 addr show wlan0 | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}'",
            shell=True
        ).decode().strip()
        if ip:
            return ip
    except Exception:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "No IP"

def get_temp():
    try:
        temp = subprocess.check_output("vcgencmd measure_temp", shell=True).decode()
        return temp.replace("temp=", "").strip()
    except Exception:
        temps = psutil.sensors_temperatures()
        if temps:
            for _, entries in temps.items():
                if entries:
                    return f"{entries[0].current:.1f}°C"
        return "N/A"

def show_text(title, value):
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)

    w_title, h_title = get_text_size(draw, title, font_small)
    draw.text(((oled.width - w_title) / 2, 0), title, font=font_small, fill=255)

    if title.lower().startswith("wi-fi"):
        size = 22
        while True:
            dynamic_font = ImageFont.truetype(font_path, size)
            w_val, h_val = get_text_size(draw, value, dynamic_font)
            if w_val <= oled.width - 4 or size <= 10:
                break
            size -= 1
    else:
        dynamic_font = font_large
        w_val, h_val = get_text_size(draw, value, dynamic_font)

    draw.text(
        ((oled.width - w_val) / 2, (oled.height - h_val) / 2),
        value,
        font=dynamic_font,
        fill=255
    )

    oled.image(image)
    oled.show()

while True:
    show_text("Wi-Fi IP", get_ip())
    time.sleep(3)
    show_text("CPU Usage", f"{psutil.cpu_percent()}%")
    time.sleep(3)
    show_text("Memory", f"{psutil.virtual_memory().percent}%")
    time.sleep(3)
    show_text("Disk", f"{psutil.disk_usage('/').percent}%")
    time.sleep(3)
    show_text("Temp", get_temp())
    time.sleep(3)
-------------------------------------------------------

Save and exit (Ctrl + O, Enter, Ctrl + X).
Test:
   python3 system_stats_cycle.py

5. Set Up Autostart (systemd)
   sudo nano /etc/systemd/system/oled-display.service

Paste:
[Unit]
Description=OLED Display System Stats
After=network.target

[Service]
ExecStart=/home/kali/oled_display/oled-env/bin/python3 /home/kali/oled_display/system_stats_cycle.py
WorkingDirectory=/home/kali/oled_display
StandardOutput=inherit
StandardError=inherit
Restart=always
User=kali

[Install]
WantedBy=multi-user.target

Enable it:
   sudo systemctl daemon-reload
   sudo systemctl enable oled-display.service
   sudo systemctl start oled-display.service

Check status:
   sudo systemctl status oled-display.service

Testing & Maintenance
---------------------
Manual Run:
   source ~/oled_display/oled-env/bin/activate
   python3 ~/oled_display/system_stats_cycle.py

Stop/Start Service:
   sudo systemctl stop oled-display
   sudo systemctl start oled-display

Remove Autostart:
   sudo systemctl disable oled-display

Verification Checklist
----------------------
- I²C enabled
- OLED wired correctly
- Address 0x3C detected
- Python script works manually
- Autostart works on reboot
- Battery output 5.1 V
- OLED cycles stats every 3 s
