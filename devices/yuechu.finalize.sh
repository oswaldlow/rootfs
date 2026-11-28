# shellcheck shell=bash
# yuechu rootfs finalize hook, sourced by distro_finalize (distros/common.sh).
#
# Units live in overlay/yuechu; the overlay only copies regular files, so the
# enable/mask symlinks are made here.  The baseband stays off until
# yuechu-baseband-setup is run on the device.

device_finalize() {
	local root="$1"

	# No suspend path is validated on this board yet.
	systemctl --root="$root" mask sleep.target suspend.target hibernate.target \
		hybrid-sleep.target suspend-then-hibernate.target

	# USB NCM gadget (169.254.42.1) for first access before WiFi is set up.
	systemctl --root="$root" enable yuechu-usbnet.service

	# Recover from a USB power-on, where the bootloader skips the modem.
	# Does nothing until yuechu-baseband-setup has enabled the baseband.
	systemctl --root="$root" enable yuechu-modem-bootcheck.service
}
