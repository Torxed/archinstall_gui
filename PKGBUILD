# Maintainer: Anton Hvornum anton@hvornum.se
# Contributor: Anton Hvornum anton@hvornum.se
pkgname="archinstall-gui"
pkgver="0.1rc4"
pkgdesc="Installs a graphical installer for Arch Linux."
pkgrel=2
url="https://github.com/Torxed/archinstall"
license=('GPLv3')
provides=("${pkgname}")
md5sums=('SKIP')
arch=('x86_64')
source=("${pkgname}-v${pkgver}-x86_64.tar.gz::https://github.com/Torxed/archinstall_gui/archive/v$pkgver.tar.gz")
depends=('python>=3.8' 'chromium' 'xorg-server')

package() {
	# Will add this back when I've renamed the project upstream:
	# cd "${pkgname}-${pkgver}"
	cd "archinstall_gui-${pkgver}"
	ls -l

	mkdir -p "${pkgdir}/srv/archinstall_gui"
	mkdir -p "${pkgdir}/usr/bin"
	mkdir -p "${pkgdir}/etc/systemd/system"

	mv archinstall_gui/* "${pkgdir}/var/lib/archinstall/"
	mv PKGBUILD_DATA/archinstall "${pkgdir}/usr/bin/archinstall"
	mv PKGBUILD_DATA/archinstall_gui.service "${pkgdir}/etc/systemd/system/archinstall_gui.service"

	chmod +x "${pkgdir}/var/lib/archinstall/archinstall"
	chmod +x "${pkgdir}/usr/bin/archinstall"
}
