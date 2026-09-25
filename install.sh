#!/bin/bash
# Install from this git checkout and enable the services.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

sudo install -Dm755 tdp/steamos-manager-gpd-win5-tdp.py /usr/bin/steamos-manager-gpd-win5-tdp
sudo install -Dm755 battery/steamos-manager-gpd-win5-battery.py /usr/bin/steamos-manager-gpd-win5-battery
sudo install -Dm755 fan/steamos-manager-gpd-win5-fan.py /usr/bin/steamos-manager-gpd-win5-fan
sudo install -Dm644 -t /usr/lib/systemd/system \
  tdp/steamos-manager-gpd-win5-tdp.service battery/steamos-manager-gpd-win5-battery.service \
  fan/steamos-manager-gpd-win5-fan.service
# Keep an existing (possibly edited) config
[ -e /etc/steamos-manager-gpd-win5/fan-curve.toml ] ||
  sudo install -Dm644 -t /etc/steamos-manager-gpd-win5 fan/fan-curve.toml
sudo install -Dm644 -t /usr/share/steamos-manager/remotes.d tdp/steamos-manager-gpd-win5.toml
sudo install -Dm644 -t /usr/share/dbus-1/system.d tdp/io.github.asolcanu.SteamOSManagerGpdWin5.conf
sudo install -Dm644 -t /usr/share/licenses/steamos-manager-gpd-win5 LICENSE

sudo systemctl daemon-reload
sudo systemctl reload dbus
sudo systemctl enable --now steamos-manager-gpd-win5-tdp.service steamos-manager-gpd-win5-battery.service \
  steamos-manager-gpd-win5-fan.service
systemctl --user restart steamos-manager
