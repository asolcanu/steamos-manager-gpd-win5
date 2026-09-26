# steamos-manager-gpd-win5

Steam Game Mode TDP slider, battery time estimates and a quiet fan curve for
the GPD Win 5 on non-SteamOS distributions (e.g. CachyOS Handheld).

> [!WARNING]
> These services change power limits (up to 85 W) and control the fans
> directly. A wrong setting or fan curve can overheat the device, and higher
> power limits add heat and battery wear. They are only tested on one GPD Win 5
> (G1618-05) running CachyOS, and are not affiliated with GPD or Valve.
> Use at your own risk; the software comes without warranty (see
> [LICENSE](LICENSE)).

## Services

- **tdp**: steamos-manager `TdpLimit1` backend using ryzenadj (5–85 W).
  Restores the limit when `amd_pmf` resets it after AC/DC changes or resume.
  Steam's "TDP Limit" off (85 W) returns control to the firmware.
- **battery**: mirrors UPower time estimates to `/run/vpower`, where Steam
  reads them.
- **fan**: fan curve from `/etc/steamos-manager-gpd-win5/fan-curve.toml`, in
  Game Mode and on the desktop. Both fans follow the curve: through `pwm1`
  with the stock driver, or `pwm1` and `pwm2` with the two-channel driver.
  On exit the fans go back to the EC; with the stock driver, the second fan
  needs [gpd-fan-duo-fix](https://github.com/asolcanu/gpd-fan-duo-fix) for
  that.

## Install

Work in progress. For now:

```
git clone https://github.com/asolcanu/steamos-manager-gpd-win5.git
cd steamos-manager-gpd-win5
./install.sh
```

Update with `./update.sh`, remove with `./uninstall.sh`.
