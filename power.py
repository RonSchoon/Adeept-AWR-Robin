# Description : Lower power consumption at Raspberry Pi
# Author      : Ronny
# Date        : 2023/03/25

import os

def low():
  os.system("echo '1-1' | sudo tee /sys/bus/usb/drivers/usb/unbind")  # Disable USB and LAN
  os.system("sudo /opt/vc/bin/tvservice -o")  # Disable HDMI
  os.system("echo 0 | sudo tee /sys/class/leds/led0/brightness")  # Disable green Power LED
  os.system("echo 0 | sudo tee /sys/class/leds/led1/brightness")  # Disable red Activity LED

def default():
  os.system("echo '1-1' | sudo tee /sys/bus/usb/drivers/usb/bind")  # Enable USB and LAN
  os.system("sudo /opt/vc/bin/tvservice -p")  # Enable HDMI
  os.system("echo 1 | sudo tee /sys/class/leds/led0/brightness")  # Enable green Power LED
  os.system("echo 1 | sudo tee /sys/class/leds/led1/brightness")  # Enable red Activity LED

if __name__ == '__main__':
  print("Set power low")
  low()