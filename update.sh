#!/bin/bash
# Pull the latest version, reinstall and restart the services.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

git pull --ff-only
./install.sh
# install.sh's enable --now doesn't restart services that are already running
sudo systemctl restart steamos-manager-gpd-win5-tdp.service steamos-manager-gpd-win5-battery.service \
  steamos-manager-gpd-win5-fan.service
