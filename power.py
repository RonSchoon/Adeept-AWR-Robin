# Description : Lower power consumption at Raspberry Pi
# Author      : Ronny
# Date        : 2023/03/25

import os

def low():
  print(os.system("echo '1-1' | sudo tee /sys/bus/usb/drivers/usb/unbind"))  # Disable USB and LAN
  print(os.system("sudo /opt/vc/bin/tvservice -o"))  # Disable HDMI
  print(os.system("echo 0 | sudo tee /sys/class/leds/led0/brightness"))  # Disable green Power LED
  print(os.system("echo 0 | sudo tee /sys/class/leds/led1/brightness"))  # Disable red Activity LED

def default():
  print(os.system("echo '1-1' | sudo tee /sys/bus/usb/drivers/usb/bind"))  # Enable USB and LAN
  print(os.system("sudo /opt/vc/bin/tvservice -p"))  # Enable HDMI
  print(os.system("echo 1 | sudo tee /sys/class/leds/led0/brightness"))  # Enable green Power LED
  print(os.system("echo 1 | sudo tee /sys/class/leds/led1/brightness"))  # Enable red Activity LED

if __name__ == '__main__':
  print("Set power low")
  low()