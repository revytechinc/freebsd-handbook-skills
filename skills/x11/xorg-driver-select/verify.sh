#!/bin/sh
# Independent check for x11/xorg-driver-select (test input DRIVER=vesa): the
# VESA driver is installed, /usr/local/etc/X11/xorg.conf.d/20-vesa.conf holds
# exactly the Device section, no other file X.org reads has a Device section, and the X
# server, started once, loads only the vesa video driver (it then stops:
# the test machines have no console it can use, which is expected).
# Exit 0 when verified, 1 otherwise.
d=/usr/local/etc/X11/xorg.conf.d
[ -f /usr/local/lib/xorg/modules/drivers/vesa_drv.so ] || { echo "FAIL: vesa_drv.so not installed"; exit 1; }
want=$(printf 'Section "Device"\n\tIdentifier "Card0"\n\tDriver     "vesa"\nEndSection')
[ "$(cat "$d/20-vesa.conf" 2>/dev/null)" = "$want" ] || { echo "FAIL: $d/20-vesa.conf missing or different"; exit 1; }
# Every file X.org reads that has a Device section (any, with or without Driver).
others=$(for x in /etc/X11/xorg.conf* /usr/local/etc/X11/xorg.conf* /etc/xorg.conf* /usr/local/lib/X11/xorg.conf* /usr/local/etc/X11/xorg.conf.d/*.conf /etc/X11/xorg.conf.d/*.conf /usr/local/share/X11/xorg.conf.d/*.conf; do [ -f "$x" ] && echo "$x"; done | xargs awk 'tolower($1)=="section" && tolower($2)=="\"device\""{print FILENAME}' | sort -u | grep -vx "$d/20-vesa.conf")
[ -z "$others" ] || { echo "FAIL: other files also have a Device section: $others"; exit 1; }
log=/tmp/hbv-xorg.$$.log
timeout 60 /usr/local/bin/Xorg :7 -logfile "$log" -nolisten tcp >/dev/null 2>&1
grep -q 'Using config directory: "/usr/local/etc/X11/xorg.conf.d"' "$log" || { echo "FAIL: Xorg did not read $d"; rm -f "$log"; exit 1; }
# Every video driver X.org loaded, from its "Loading .../drivers/NAME_drv.so" lines.
loaded=$(sed -nE 's#.*Loading .*/modules/drivers/([^/]*)_drv\.so.*#\1#p' "$log" | sort -u | tr '\n' ' ')
rm -f "$log"
[ "$loaded" = "vesa " ] || { echo "FAIL: Xorg loaded video drivers '$loaded', not only vesa"; exit 1; }
echo "OK: 20-vesa.conf in place; Xorg loads only the vesa driver"
