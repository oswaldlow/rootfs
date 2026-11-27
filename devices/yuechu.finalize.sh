# shellcheck shell=bash
# yuechu rootfs finalize hook, sourced by distro_finalize (distros/common.sh).
#
# Units live in overlay/yuechu; the overlay only copies regular files, so the
# enable/mask symlinks and the resolv.conf link are made here.  The baseband
# stays off until yuechu-baseband-setup is run on the device.

device_finalize() {
	local root="$1"

	# No suspend path is validated on this board yet.
	systemctl --root="$root" mask sleep.target suspend.target hibernate.target \
		hybrid-sleep.target suspend-then-hibernate.target

	# USB NCM gadget (169.254.42.1) for first access before WiFi is set up.
	systemctl --root="$root" enable yuechu-usbnet.service

	# NetworkManager hands DNS to systemd-resolved (98-yuechu-dns.conf), so
	# the WiFi and cellular servers stay per link.
	rm -f "$root/etc/resolv.conf"
	ln -s /run/systemd/resolve/stub-resolv.conf "$root/etc/resolv.conf"
}
