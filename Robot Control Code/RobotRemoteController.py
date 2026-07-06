import socket
import keyboard
import time
import csv
from datetime import datetime

PORT = 80
LOG_FILE = "commandlog.csv"

# Tuning values
SPEED_STEP = 5       # How much W/S changes current speed per command tick
SEND_INTERVAL = 0.05 # Seconds between commands
SERVO_ANGLE = 50     # Servo offset sent to robot: -15, 0, or +15 degrees

# Drive mode values sent to the ESP:
#   0  = both motors forward at currentSpeed
#  -1  = soft left:  motor 1 off, motor 2 forward
#   1  = soft right: motor 1 forward, motor 2 off
#  -2  = differential left:  motor 1 backward, motor 2 forward
#   2  = differential right: motor 1 forward, motor 2 backward


def get_laptop_ip():
    temp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        temp.connect(("8.8.8.8", 80))
        return temp.getsockname()[0]
    finally:
        temp.close()


def find_esp():
    laptop_ip = get_laptop_ip()
    subnet = ".".join(laptop_ip.split(".")[:3])

    print("Laptop IP:", laptop_ip)
    print(f"Searching for ESP on {subnet}.x ...")

    for i in range(1, 255):
        ip = f"{subnet}.{i}"

        if ip == laptop_ip:
            continue

        try:
            test = socket.create_connection((ip, PORT), timeout=0.5)
            test.close()
            print("Found ESP:", ip)
            return ip
        except Exception:
            pass

    return None


ESP_IP = find_esp()

if ESP_IP is None:
    print("Could not find ESP")
    exit()

s = socket.create_connection((ESP_IP, PORT), timeout=3)
s.settimeout(None)

log_file = open(LOG_FILE, "a", newline="")
csv_writer = csv.writer(log_file)

if log_file.tell() == 0:
    csv_writer.writerow(["timestamp", "command"])

print("Connected to:", ESP_IP)
print("Controls:")
print("  W = speed up forward")
print("  S = slow down")
print("  A/D = soft turn by turning off one drive motor")
print("  Q/E = servo steering -15/+15 degrees")
print("  Z/C = differential turn")
print("  SPACE = stop")


def send(cmd):
    try:
        s.sendall((cmd + "\n").encode())

        csv_writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            cmd,
        ])
        log_file.flush()

    except Exception as e:
        print("Error sending data:", e)


try:
    while True:
        speed_delta = 0
        drive_mode = 0
        servo_offset = 0

        # Speed control: W increases current forward speed, S decreases it.
        if keyboard.is_pressed("w"):
            speed_delta = SPEED_STEP
        elif keyboard.is_pressed("s"):
            speed_delta = -SPEED_STEP

        # Soft turn: one motor off, the other motor powered by currentSpeed.
        # I used A/D here because E is used for servo steering below.
        if keyboard.is_pressed("a"):
            drive_mode = -1
        elif keyboard.is_pressed("d"):
            drive_mode = 1

        # Differential turn: one motor forward, the other backward.
        if keyboard.is_pressed("z"):
            drive_mode = -2
        elif keyboard.is_pressed("c"):
            drive_mode = 2

        # Servo steering: centered unless Q or E is held.
        if keyboard.is_pressed("q"):
            servo_offset = -SERVO_ANGLE
        elif keyboard.is_pressed("e"):
            servo_offset = SERVO_ANGLE

        if keyboard.is_pressed("space"):
            send("STOP")
            time.sleep(0.1)
            continue

        send(f"DRIVE:{speed_delta},{drive_mode},{servo_offset}")
        time.sleep(SEND_INTERVAL)

finally:
    s.close()
    log_file.close()
