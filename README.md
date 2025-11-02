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

2. 
    # ===============================================
# OLED System Stats Display — Full Auto Setup
# Raspberry Pi Zero 2 W (Kali Linux)
# Author: Balichak Suman
# ===============================================

# ---- Step 1: System Update & Dependencies ----
sudo apt update
sudo apt install -y python3-venv python3-pip python3-dev i2c-tools git

# ---- Step 2: Create Python Virtual Environment ----
python3 -m venv ~/oled-env
source ~/oled-env/bin/activate
pip install adafruit-circuitpython-ssd1306 psutil pillow luma.oled

# ---- Step 3: Create Main Python Script ----
sudo tee /usr/local/bin/system_stats_cycle.py > /dev/null << 'EOF'
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
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_c = int(f.read()) / 1000
        return temp_c
    except:
        return 0.0

def get_disk():
    disk = psutil.disk_usage('/')
    return (disk.used // (1024 * 1024), disk.total // (1024 * 1024))

while True:
    ip = get_ip()
    cpu = get_cpu_usage()
    temp = get_temp()
    used, total = get_disk()

    image = Image.new("1", (device.width, device.height))
    draw = ImageDraw.Draw(image)

    # Center IP heading
    ip_w, ip_h = draw.textbbox((0, 0), ip, font=font_big)[2:]
    draw.text(((device.width - ip_w) // 2, 0), ip, font=font_big, fill=255)

    # System stats
    lines = [
        f"CPU: {cpu:.1f}%",
        f"Temp: {temp:.1f}°C",
        f"Disk: {used}/{total} MB"
    ]

    y = ip_h + 4
    for line in lines:
        w, h = draw.textbbox((0, 0), line, font=font_small)[2:]
        draw.text(((device.width - w) // 2, y), line, font=font_small, fill=255)
        y += h + 1

    device.display(image)
    time.sleep(3)
EOF

# ---- Step 4: Set Permissions and Lock Script ----
sudo chmod +x /usr/local/bin/system_stats_cycle.py
sudo chattr +i /usr/local/bin/system_stats_cycle.py

# ---- Step 5: Create Systemd Service ----
sudo tee /etc/systemd/system/system_stats_cycle.service > /dev/null << 'EOF'
[Unit]
Description=OLED System Stats Display
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/home/kali/oled-env/bin/python3 /usr/local/bin/system_stats_cycle.py
Restart=always
User=kali
Environment=PATH=/home/kali/oled-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
WorkingDirectory=/home/kali

[Install]
WantedBy=multi-user.target
EOF

# ---- Step 6: Enable & Start Service ----
sudo systemctl daemon-reload
sudo systemctl enable system_stats_cycle.service
sudo systemctl start system_stats_cycle.service

# ---- Step 7: Verify Setup ----
echo ""
echo "✅ OLED System Stats Display Installed & Running!"
echo "Check status using: sudo systemctl status system_stats_cycle.service"
echo "View logs using: sudo journalctl -u system_stats_cycle.service -n 20 --no-pager"
echo "Script locked at: /usr/local/bin/system_stats_cycle.py"
echo "Virtual Env Path: /home/kali/oled-env"
echo "----------------------------------------------"
EOF
