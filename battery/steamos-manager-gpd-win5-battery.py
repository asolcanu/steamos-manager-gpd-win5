#!/usr/bin/python3
# Stand-in for SteamOS's vpower: Steam reads battery time estimates from
# /run/vpower, which nothing writes on CachyOS. Copy them from UPower.

import os
import sys

import dbus
import dbus.mainloop.glib
from gi.repository import GLib

UPOWER = "org.freedesktop.UPower"
DISPLAY_DEVICE = "/org/freedesktop/UPower/devices/DisplayDevice"
DEVICE_IFACE = "org.freedesktop.UPower.Device"
PROPS_IFACE = "org.freedesktop.DBus.Properties"

VPOWER_DIR = "/run/vpower"
TIME_TO_FULL = "secs_until_battery_full"
TIME_TO_EMPTY = "secs_until_shutdown_request"
STATUS = "battery_status"

# UPower Device.State -> kernel power_supply status strings
STATES = {
    0: "Unknown",
    1: "Charging",
    2: "Discharging",
    3: "Discharging",  # Empty
    4: "Full",
    5: "Not charging",  # PendingCharge
    6: "Not charging",  # PendingDischarge
}


def write(name, value):
    path = os.path.join(VPOWER_DIR, name)
    if value is None:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        return
    content = f"{value}\n"
    try:
        with open(path) as f:
            if f.read() == content:
                return
    except FileNotFoundError:
        pass
    tmp = os.path.join(VPOWER_DIR, f".{name}.tmp")
    with open(tmp, "w") as f:
        f.write(content)
    os.replace(tmp, path)


class Bridge:
    def __init__(self, bus):
        # Follow the well-known name so a UPower restart doesn't strand us
        self.device = bus.get_object(UPOWER, DISPLAY_DEVICE, follow_name_owner_changes=True)

    def update(self, *args):
        try:
            self.mirror()
        except (dbus.DBusException, OSError) as e:
            print(f"Updating {VPOWER_DIR} failed: {e}", flush=True)

    def mirror(self):
        props = self.device.GetAll(DEVICE_IFACE, dbus_interface=PROPS_IFACE)
        state = STATES.get(int(props["State"]), "Unknown")
        to_full = int(props["TimeToFull"])
        to_empty = int(props["TimeToEmpty"])
        write(STATUS, state)
        write(TIME_TO_FULL, to_full if state == "Charging" and to_full > 0 else None)
        write(TIME_TO_EMPTY, to_empty if state == "Discharging" and to_empty > 0 else None)


def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    bridge = Bridge(bus)
    bus.add_signal_receiver(
        bridge.update,
        signal_name="PropertiesChanged",
        dbus_interface=PROPS_IFACE,
        bus_name=UPOWER,
        path=DISPLAY_DEVICE,
    )
    # Refresh when UPower starts or restarts (also fires once right away)
    bus.watch_name_owner(UPOWER, lambda owner: owner and bridge.update())
    print(f"Mirroring UPower battery estimates to {VPOWER_DIR}", flush=True)
    GLib.MainLoop().run()


if __name__ == "__main__":
    sys.exit(main())
