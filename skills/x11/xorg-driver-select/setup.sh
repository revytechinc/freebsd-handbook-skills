#!/bin/sh
# Precondition for x11/xorg-driver-select: pkg and the X server are
# installed (x11/xorg-install installs the whole of xorg; the server alone is
# enough here), the VESA driver package is not (the skill installs it), and
# there is no X configuration file choosing a driver.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
pkg info -e xorg-server || pkg install -y xorg-server >/dev/null 2>&1 || exit 1
# Removing the VESA driver package also removes packages that depend on it
# (xorg-drivers and the xorg meta-package): fine on a disposable test machine.
pkg info -e xf86-video-vesa && { pkg delete -y xf86-video-vesa >/dev/null 2>&1 || exit 1; }
rm -f /usr/local/etc/X11/xorg.conf.d/20-vesa.conf
# No other file may already choose a driver, and /etc/X11/xorg.conf.d must
# hold no .conf file (X.org would read it instead).
f=$(for x in /etc/X11/xorg.conf* /usr/local/etc/X11/xorg.conf* /etc/xorg.conf* /usr/local/lib/X11/xorg.conf* /usr/local/etc/X11/xorg.conf.d/*.conf /etc/X11/xorg.conf.d/*.conf /usr/local/share/X11/xorg.conf.d/*.conf; do [ -f "$x" ] && echo "$x"; done | xargs awk 'tolower($1)=="section" && tolower($2)=="\"device\""{print FILENAME}' )
[ -z "$f" ] || { echo "setup: a file already chooses a driver: $f" >&2; exit 1; }
[ -z "$(ls /etc/X11/xorg.conf.d/*.conf 2>/dev/null)" ] || { echo "setup: /etc/X11/xorg.conf.d has files" >&2; exit 1; }
pkg info -e xorg-server && ! pkg info -e xf86-video-vesa
