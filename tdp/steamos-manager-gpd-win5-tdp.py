#!/usr/bin/python3
# Remote TdpLimit1 implementation for steamos-manager on the GPD Win 5,
# backed by ryzenadj. Registered via steamos-manager remotes.d.

import subprocess
import sys

import dbus
import dbus.mainloop.glib
import dbus.service
from gi.repository import GLib

BUS_NAME = "io.github.asolcanu.SteamOSManagerGpdWin5"
OBJECT_PATH = "/io/github/asolcanu/SteamOSManagerGpdWin5"
IFACE = "com.steampowered.SteamOSManager1.TdpLimit1"
PROPS_IFACE = "org.freedesktop.DBus.Properties"

TDP_MIN = 5
TDP_MAX = 85
# Firmware (amd_pmf) limit on both AC and DC. Used if the current limit can't be
# read, and when Steam's TDP toggle is off: Steam then sets TdpLimitMax, which
# on a Deck means stock, so treat it as "hand control back to the firmware"
TDP_DEFAULT = 45
# amd_pmf restores its own limits ~15 s after an AC/DC change, so after a
# charger change or resume, check once a second for a while
WATCH_SECONDS = 20
RYZENADJ_TIMEOUT = 5


def read_limit():
    # Needs the ryzen_smu module; the PM table isn't readable via /dev/mem
    try:
        out = subprocess.run(
            ["/usr/bin/ryzenadj", "--info"],
            capture_output=True,
            text=True,
            check=True,
            timeout=RYZENADJ_TIMEOUT,
        ).stdout
        for line in out.splitlines():
            fields = [f.strip() for f in line.split("|")]
            if len(fields) > 2 and fields[1] == "STAPM LIMIT":
                return round(float(fields[2]))
    except (subprocess.SubprocessError, OSError, ValueError, OverflowError) as e:
        print(f"Reading current limit failed: {e}", flush=True)
    return None


def apply_limit(watts):
    mw = str(watts * 1000)
    subprocess.run(
        ["/usr/bin/ryzenadj", f"--stapm-limit={mw}", f"--fast-limit={mw}", f"--slow-limit={mw}"],
        check=True,
        stdout=subprocess.DEVNULL,
        timeout=RYZENADJ_TIMEOUT,
    )
    print(f"TDP set to {watts} W", flush=True)


class TdpLimit(dbus.service.Object):
    def __init__(self, bus):
        super().__init__(bus, OBJECT_PATH)
        limit = read_limit()
        if limit is None:
            print(f"Current limit unknown, assuming {TDP_DEFAULT} W", flush=True)
            limit = TDP_DEFAULT
        self.limit = min(max(limit, TDP_MIN), TDP_MAX)
        self.watch_left = 0

    def props(self):
        return {
            "TdpLimit": dbus.UInt32(self.limit),
            "TdpLimitMin": dbus.UInt32(TDP_MIN),
            "TdpLimitMax": dbus.UInt32(TDP_MAX),
        }

    def set_limit(self, watts):
        # dbus.Boolean subclasses int; anything else non-integral is rejected
        if not isinstance(watts, int) or isinstance(watts, dbus.Boolean):
            raise dbus.exceptions.DBusException(
                "TdpLimit must be an integer",
                name="org.freedesktop.DBus.Error.InvalidArgs",
            )
        watts = int(watts)
        if not TDP_MIN <= watts <= TDP_MAX:
            raise dbus.exceptions.DBusException(
                f"Limit {watts} outside {TDP_MIN}-{TDP_MAX}",
                name="org.freedesktop.DBus.Error.InvalidArgs",
            )
        try:
            if watts == TDP_MAX:
                print("TDP limit off, restoring firmware default", flush=True)
                apply_limit(TDP_DEFAULT)
            else:
                apply_limit(watts)
        except (subprocess.SubprocessError, OSError) as e:
            print(f"Setting limit failed: {e}", flush=True)
            raise dbus.exceptions.DBusException(
                "ryzenadj failed to set the limit", name="org.freedesktop.DBus.Error.Failed"
            )
        self.limit = watts
        self.PropertiesChanged(IFACE, {"TdpLimit": dbus.UInt32(watts)}, [])

    def prepare_for_sleep(self, sleeping):
        if not sleeping:
            self.start_watch()

    def power_changed(self, interface, changed, invalidated):
        if "OnBattery" in changed:
            self.start_watch()

    def start_watch(self):
        # A new event restarts the window; only one timer runs at a time
        if self.watch_left <= 0:
            GLib.timeout_add_seconds(1, self.watch)
        self.watch_left = WATCH_SECONDS

    def watch(self):
        # Must not raise: GLib would drop the timer while watch_left stays > 0,
        # and start_watch would never schedule another one
        try:
            # At TDP_MAX (Steam's toggle off) the firmware manages the limit
            current = read_limit() if self.limit != TDP_MAX else None
            if current is not None and current != self.limit:
                print(f"Limit changed to {current} W externally, restoring", flush=True)
                apply_limit(self.limit)
        except Exception as e:
            print(f"Restoring limit failed: {e}", flush=True)
        self.watch_left -= 1
        return self.watch_left > 0

    @dbus.service.method(PROPS_IFACE, in_signature="ss", out_signature="v")
    def Get(self, interface, prop):
        if interface != IFACE or prop not in self.props():
            raise dbus.exceptions.DBusException(
                f"Unknown property {interface}.{prop}",
                name="org.freedesktop.DBus.Error.UnknownProperty",
            )
        return self.props()[prop]

    @dbus.service.method(PROPS_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        return self.props() if interface == IFACE else {}

    @dbus.service.method(PROPS_IFACE, in_signature="ssv")
    def Set(self, interface, prop, value):
        if interface != IFACE or prop != "TdpLimit":
            raise dbus.exceptions.DBusException(
                f"Property {interface}.{prop} is not writable",
                name="org.freedesktop.DBus.Error.PropertyReadOnly",
            )
        self.set_limit(value)

    @dbus.service.signal(PROPS_IFACE, signature="sa{sv}as")
    def PropertiesChanged(self, interface, changed, invalidated):
        pass

    @dbus.service.method("org.freedesktop.DBus.Introspectable", out_signature="s")
    def Introspect(self):
        return f"""<node>
  <interface name="{IFACE}">
    <property name="TdpLimit" type="u" access="readwrite"/>
    <property name="TdpLimitMin" type="u" access="read"/>
    <property name="TdpLimitMax" type="u" access="read"/>
  </interface>
  <interface name="org.freedesktop.DBus.Introspectable">
    <method name="Introspect"><arg type="s" direction="out"/></method>
  </interface>
  <interface name="{PROPS_IFACE}">
    <method name="Get"><arg type="s" direction="in"/><arg type="s" direction="in"/><arg type="v" direction="out"/></method>
    <method name="GetAll"><arg type="s" direction="in"/><arg type="a{{sv}}" direction="out"/></method>
    <method name="Set"><arg type="s" direction="in"/><arg type="s" direction="in"/><arg type="v" direction="in"/></method>
    <signal name="PropertiesChanged"><arg type="s"/><arg type="a{{sv}}"/><arg type="as"/></signal>
  </interface>
</node>"""


def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    obj = TdpLimit(bus)
    # Keep a reference: BusName releases the name when garbage-collected
    name = dbus.service.BusName(BUS_NAME, bus, do_not_queue=True)
    bus.add_signal_receiver(
        obj.prepare_for_sleep,
        signal_name="PrepareForSleep",
        dbus_interface="org.freedesktop.login1.Manager",
        bus_name="org.freedesktop.login1",
    )
    bus.add_signal_receiver(
        obj.power_changed,
        signal_name="PropertiesChanged",
        dbus_interface=PROPS_IFACE,
        bus_name="org.freedesktop.UPower",
        path="/org/freedesktop/UPower",
    )
    print(f"{BUS_NAME} ready ({TDP_MIN}-{TDP_MAX} W, current {obj.limit} W)", flush=True)
    GLib.MainLoop().run()


if __name__ == "__main__":
    sys.exit(main())
