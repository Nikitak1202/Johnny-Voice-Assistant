
from gpiozero import DigitalInputDevice
from time import sleep
d = DigitalInputDevice(27)  # BCM 27 = физ. пин 13
print("Press Ctrl+C to stop. Reading D0 every 0.5 s...")
while True:
    print("D0 =", int(d.value))
    sleep(0.5)
