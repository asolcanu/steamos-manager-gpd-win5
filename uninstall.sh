#!/bin/bash
# Stop the services and remove what install.sh installed.
set -euo pipefail

sudo systemctl disable --now steamos-manager-gpd-win5-tdp.service steamos-manager-gpd-win5-battery.service \
  steamos-manager-gpd-win5-fan.service
sudo rm -f \
  /usr/bin/steamos-manager-gpd-win5-tdp \
  /usr/bin/steamos-manager-gpd-win5-battery \
  /usr/bin/steamos-manager-gpd-win5-fan \
  /usr/lib/systemd/system/steamos-manager-gpd-win5-tdp.service \
  /usr/lib/systemd/system/steamos-manager-gpd-win5-battery.service \
  /usr/lib/systemd/system/steamos-manager-gpd-win5-fan.service \
  /usr/share/steamos-manager/remotes.d/steamos-manager-gpd-win5.toml \
  /usr/share/dbus-1/system.d/io.github.asolcanu.SteamOSManagerGpdWin5.conf
sudo rm -rf /usr/share/licenses/steamos-manager-gpd-win5
# Remove the config if unchanged, otherwise keep it as .pacsave
conf=/etc/steamos-manager-gpd-win5/fan-curve.toml
if [ -e "$conf" ]; then
  if cmp -s "$conf" "$(git rev-parse --show-toplevel 2>/dev/null)/fan/fan-curve.toml"; then
    sudo rm "$conf"
  else
    sudo mv "$conf" "$conf.pacsave"
  fi
  sudo rmdir --ignore-fail-on-non-empty /etc/steamos-manager-gpd-win5
fi

sudo systemctl daemon-reload
sudo systemctl reload dbus
systemctl --user restart steamos-manager
