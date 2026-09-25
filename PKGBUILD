pkgname=steamos-manager-gpd-win5
pkgver=0.1.0
pkgrel=1
pkgdesc="Steam TDP slider (via steamos-manager + ryzenadj) and battery time estimates for the GPD Win 5"
arch=('any')
url="https://github.com/asolcanu/steamos-manager-gpd-win5"
license=('MIT')
depends=(
  'python-dbus'
  'python-gobject'
  'ryzenadj'
  'ryzen_smu-dkms'
  'steamos-manager'
  'upower'
)
install=steamos-manager-gpd-win5.install
source=("$pkgname-$pkgver.tar.gz::$url/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('SKIP')

package() {
  cd "$pkgname-$pkgver"
  install -Dm755 tdp/steamos-manager-gpd-win5-tdp.py "$pkgdir/usr/bin/steamos-manager-gpd-win5-tdp"
  install -Dm755 battery/steamos-manager-gpd-win5-battery.py "$pkgdir/usr/bin/steamos-manager-gpd-win5-battery"
  install -Dm644 -t "$pkgdir/usr/lib/systemd/system" \
    tdp/steamos-manager-gpd-win5-tdp.service battery/steamos-manager-gpd-win5-battery.service
  install -Dm644 -t "$pkgdir/usr/share/steamos-manager/remotes.d" tdp/steamos-manager-gpd-win5.toml
  install -Dm644 -t "$pkgdir/usr/share/dbus-1/system.d" tdp/io.github.asolcanu.SteamOSManagerGpdWin5.conf
  install -Dm644 -t "$pkgdir/usr/share/licenses/$pkgname" LICENSE
}
