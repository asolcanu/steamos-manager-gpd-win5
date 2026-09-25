# steamos-manager-gpd-win5

Makes Steam Game Mode's TDP slider and battery time estimates work on the
GPD Win 5 (Ryzen AI Max+ 395 / Strix Halo) under non-SteamOS distributions
such as CachyOS Handheld.

## What it does

**TDP slider** (`steamos-manager-gpd-win5-tdp`)

steamos-manager has no built-in TDP method that works on the Win 5 (no
writable amdgpu `power1_cap`, no `firmware-attributes` driver). It can relay
its `TdpLimit1` interface to an external D-Bus service registered in
`remotes.d`, which is what this service is. It sets the STAPM, fast and slow
PPT limits together with ryzenadj, over a 5–85 W range.

The `amd_pmf` driver re-applies its own BIOS limits (45 W) about 15 seconds
after the charger is plugged or unplugged. After every AC/DC change and resume,
the service checks the limit once a second for 20 seconds and restores it.

Turning Steam's "TDP Limit" toggle off makes Steam set the maximum (85 W). As on
the Steam Deck, where the maximum is the stock limit, this is treated as "off":
the service restores the 45 W firmware default and stops enforcing a limit.

**Battery time estimates** (`steamos-manager-gpd-win5-battery`)

Steam reads charge and discharge time estimates from `/run/vpower`, which is
written by SteamOS's `vpower` daemon. Nothing writes it on other distributions,
so this service mirrors UPower's `TimeToFull`, `TimeToEmpty` and state there.

## Requirements

- `steamos-manager`
- `ryzenadj` and the `ryzen_smu` kernel module (for reading the current limit),
  both from the AUR: `ryzenadj-git` and `ryzen_smu-dkms-git`
- `upower`, `python-dbus`, `python-gobject`

## Install

Install the AUR dependencies first (for example `paru -S ryzenadj-git
ryzen_smu-dkms-git`), then build and install the package. The PKGBUILD
downloads the release archive matching `pkgver`:

```
makepkg -si
```

Then:

```
systemctl --user restart steamos-manager
```

The services are enabled on install and disabled on removal. steamos-manager
only reads `remotes.d` when it starts, so restart it (or reboot) after the
first install, and restart Steam once so it picks up `/run/vpower`.

## Check

```
busctl --user introspect com.steampowered.SteamOSManager1 \
  /com/steampowered/SteamOSManager1 com.steampowered.SteamOSManager1.TdpLimit1
journalctl -u steamos-manager-gpd-win5-tdp -u steamos-manager-gpd-win5-battery
```
