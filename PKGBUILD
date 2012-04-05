# For hyperion.chaosdorf.dn42
pkgname=chaosdorf-admin-toolkit
pkgver=$(date '+%Y.%m.%d').git
pkgrel=1
pkgdesc="Chaosdorf Admin-Toolkit"
url="https://github.com/chaosdorf/chaosdorf-admin-toolkit"
arch=('any')
license='WTFPL'
depends=()
optdepends=()
makedepends=()
conflicts=()
replaces=()
backup=()
install=
source=()
md5sums=()

build() {
	mkdir "${srcdir}/${pkgname}-${pkgver}"
	cd "${srcdir}/${pkgname}-${pkgver}"
	git clone git://github.com/chaosdorf/chaosdorf-admin-toolkit.git
	sed -i \
		-e 's/^Running Process Libs.*$//' \
		-e 's/^Packages.*$//' \
		-e 's/^Kernel Image.*$//' \
		chaosdorf-admin-toolkit/nagios-passive/passive_checks.cfg
}

package() {
	cd "${srcdir}/${pkgname}-${pkgver}/chaosdorf-admin-toolkit"
	install -Dm755 backup/backup_external \
		"${pkgdir}/usr/sbin/backup_external"
	install -Dm644 backup/backup_external.1 \
		"${pkgdir}/usr/share/man/man8/backup_external.8"
	install -Dm755 nagios-checks/local/check_git_status \
		"${pkgdir}/usr/share/nagios/libexec/check_git_status"
	install -Dm755 nagios-checks/local/check_hddtemp \
		"${pkgdir}/usr/share/nagios/libexec/check_hddtemp"
	install -Dm644 nagios-passive/passive_checks.cfg \
		"${pkgdir}/etc/nagios/passive_checks.cfg"
	install -Dm755 nagios-passive/run_checks \
		"${pkgdir}/usr/lib/nagios/run_checks"
	install -Dm755 nagios-passive/submit_checks \
		"${pkgdir}/usr/lib/nagios/submit_checks"
}
