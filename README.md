# steamos-manager-gpd-win5

Steam Game Mode TDP slider, battery time estimates and a quiet fan curve for
the GPD Win 5 on non-SteamOS distributions (e.g. CachyOS Handheld).

## Services

- **tdp**: steamos-manager `TdpLimit1` backend using ryzenadj (5–85 W).
  Restores the limit when `amd_pmf` resets it after AC/DC changes or resume.
  Steam's "TDP Limit" off (85 W) returns control to the firmware.
- **battery**: mirrors UPower time estimates to `/run/vpower`, where Steam
  reads them.
- **fan**: fan curve from `/etc/steamos-manager-gpd-win5/fan-curve.toml`, in
  Game Mode and on the desktop. On exit the fans go back to the EC, which
  needs [gpd-fan-duo-fix](https://github.com/asolcanu/gpd-fan-duo-fix) for
  the second fan.

## Install

Work in progress. For now:

```
git clone https://github.com/asolcanu/steamos-manager-gpd-win5.git
cd steamos-manager-gpd-win5
./install.sh
```

Remove with `./uninstall.sh`.
