#!/usr/bin/python3
# Fan curve for the GPD Win 5 via the gpd_fan hwmon driver. Hands the fan
# back to the EC's automatic curve on exit or when temperatures can't be read.

import glob
import os
import signal
import sys
import time
import tomllib

DEFAULT_CONFIG = "/etc/steamos-manager-gpd-win5/fan-curve.toml"

# pwm1_enable values (drivers/hwmon/gpd-fan.c)
MANUAL = 1
AUTOMATIC = 2


def find_hwmon(name):
    for path in glob.glob("/sys/class/hwmon/hwmon*"):
        try:
            with open(os.path.join(path, "name")) as f:
                if f.read().strip() == name:
                    return path
        except OSError:
            pass
    return None


def read_int(path):
    with open(path) as f:
        return int(f.read().strip())


def write(path, value):
    with open(path, "w") as f:
        f.write(f"{value}\n")


def load_config(path):
    with open(path, "rb") as f:
        config = tomllib.load(f)
    curve = sorted((int(t), int(p)) for t, p in config["curve"].items())
    if not curve or any(not 0 <= p <= 100 for _, p in curve):
        raise ValueError("curve needs at least one point, speeds 0-100 %")
    return {
        "curve": curve,
        "interval": float(config.get("interval", 2)),
        "hysteresis": float(config.get("hysteresis", 3)),
        "critical": float(config.get("critical", 95)),
        "sensors": config.get("sensors", ["k10temp", "amdgpu"]),
    }


def speed_for(curve, temp):
    """Linear interpolation between curve points, in percent."""
    if temp <= curve[0][0]:
        return curve[0][1]
    for (t0, p0), (t1, p1) in zip(curve, curve[1:]):
        if temp <= t1:
            return p0 + (p1 - p0) * (temp - t0) / (t1 - t0)
    return curve[-1][1]


class Fan:
    def __init__(self, hwmon):
        self.pwm = os.path.join(hwmon, "pwm1")
        self.enable = os.path.join(hwmon, "pwm1_enable")
        self.last = None

    def set_percent(self, percent):
        # The EC can drop back to automatic (e.g. after resume)
        if read_int(self.enable) != MANUAL:
            write(self.enable, MANUAL)
            self.last = None
        value = round(percent * 255 / 100)
        if value != self.last:
            write(self.pwm, value)
            self.last = value

    def automatic(self):
        write(self.enable, AUTOMATIC)
        self.last = None


def read_temp(sensors):
    temps = []
    for name in sensors:
        hwmon = find_hwmon(name)
        if hwmon:
            try:
                temps.append(read_int(os.path.join(hwmon, "temp1_input")) / 1000)
            except (OSError, ValueError):
                pass
    return max(temps) if temps else None


def main():
    config = load_config(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CONFIG)
    hwmon = find_hwmon("gpdfan")
    if not hwmon:
        sys.exit("gpd_fan hwmon device not found")
    fan = Fan(hwmon)

    def stop(*_):
        fan.automatic()
        print("Fan handed back to EC automatic control", flush=True)
        sys.exit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    print(f"Fan curve {config['curve']} on {hwmon}", flush=True)

    current = None  # speed in %, and the temperature it was chosen at
    current_temp = None
    try:
        while True:
            temp = read_temp(config["sensors"])
            if temp is None:
                if fan.last is not None:
                    print("No temperature readings, using EC automatic control", flush=True)
                    fan.automatic()
                current = None
            else:
                target = 100 if temp >= config["critical"] else speed_for(config["curve"], temp)
                # Only slow down once the temperature has dropped past the hysteresis
                slow_down = current is not None and target < current
                if not slow_down or temp <= current_temp - config["hysteresis"]:
                    if current is None or abs(target - current) >= 5:
                        print(f"{temp:.0f} °C -> fan {target:.0f} %", flush=True)
                    current, current_temp = target, temp
                fan.set_percent(current)
            time.sleep(config["interval"])
    finally:
        fan.automatic()


if __name__ == "__main__":
    main()
