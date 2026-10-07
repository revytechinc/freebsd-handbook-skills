#!/bin/sh
# Precondition for x11/keyboard-layout-file: pkg and the X server are
# installed, no keyboard layout file exists, and /etc/X11/xorg.conf.d holds
# no .conf file (X.org would read it instead).
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
pkg info -e xorg-server || pkg install -y xorg-server >/dev/null 2>&1 || exit 1
rm -f /usr/local/etc/X11/xorg.conf.d/00-keyboard.conf
[ -z "$(ls /etc/X11/xorg.conf.d/*.conf 2>/dev/null)" ] || { echo "setup: /etc/X11/xorg.conf.d has .conf files, which X.org would read instead of /usr/local/etc/X11/xorg.conf.d; move them away first" >&2; exit 1; }
pkg info -e xorg-server && [ -f /usr/local/share/X11/xkb/rules/base.lst ]
