# shellcheck shell=bash
# yuechu rootfs finalize hook, sourced by distro_finalize (distros/common.sh).
#
# Units live in overlay/yuechu; the overlay only copies regular files, so the
# enable/mask symlinks are made here.

device_finalize() {
	local root="$1"

	# Phone: no suspend path is validated yet (the MD and WiFi do not resume).
	systemctl --root="$root" mask sleep.target suspend.target hibernate.target 		hybrid-sleep.target suspend-then-hibernate.target

	# The distro ModemManager has no mtk-soc plugin; mm-mtk.service replaces
	# it and takes over the D-Bus alias (enable fails while the distro alias
	# still points at ModemManager.service).
	systemctl --root="$root" mask ModemManager.service
	rm -f "$root/etc/systemd/system/dbus-org.freedesktop.ModemManager1.service"

	# USB NCM gadget for first access, then the baseband chain:
	# prep (data-path HIF modules, NV mounts) -> CCCI owner -> mm-mtk -> IMS.
	# The owner and mm-mtk skip themselves (ConditionPathExists) until the
	# baseband userspace is installed.
	systemctl --root="$root" enable yuechu-usbnet.service yuechu-modem-prep.service 		mtk-ccci-owner.service mm-mtk.service yuechu-ims.service

	# NetworkManager hands DNS to systemd-resolved (98-yuechu-dns.conf) so the
	# WiFi and cellular servers stay per link.
	rm -f "$root/etc/resolv.conf"
	ln -s /run/systemd/resolve/stub-resolv.conf "$root/etc/resolv.conf"
}
