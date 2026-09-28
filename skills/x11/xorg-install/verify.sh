#!/bin/sh
# Independent check for x11/xorg-install (test input USERNAME=hbx): the xorg
# package is registered as installed, the X server program is present and
# reports its version (exit 0), and hbx is a member of the video group.
# Exit 0 when verified, 1 otherwise.
pkg info -e xorg || { echo "FAIL: pkg does not list xorg as installed"; exit 1; }
out=$(/usr/local/bin/Xorg -version 2>&1) || { echo "FAIL: Xorg -version exited non-zero"; exit 1; }
v=$(echo "$out" | grep -m1 '^X.Org X Server')
case "$v" in
    "X.Org X Server "[0-9]*) ;;
    *) echo "FAIL: /usr/local/bin/Xorg -version printed '$v'"; exit 1 ;;
esac
pw groupshow video | cut -d: -f4 | tr ',' '\n' | grep -qx hbx || { echo "FAIL: hbx is not in the video group"; exit 1; }
echo "OK: $v; hbx in video"
