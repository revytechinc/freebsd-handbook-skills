#!/bin/sh
# Preconditions for ports/pkg-add-offline: pkg is installed, the package and
# its dependencies were downloaded to /root/packages (ports/pkg-fetch), and
# then the machine is cut off from the network (default routes removed), so
# the skill is tested the way it is used: with no network at all.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg fetch -y -d -o /root/packages nginx-lite >/dev/null || exit 1
ls /root/packages/All/Hashed/nginx-lite-[0-9]*.pkg >/dev/null || exit 1
# Prove the check below can tell: the repository answers over https now ...
url=https://pkg.FreeBSD.org/
fetch -q -T 10 -o /dev/null "$url" || { echo "setup: $url not reachable even before going offline"; exit 1; }
route -q delete default >/dev/null 2>&1
route -q -6 delete default >/dev/null 2>&1
# ... and not after.
# (Look for the gateway line: on 14.0 "route get" exits 0 even when it
# prints "route has not been found".)
if route -n get default 2>/dev/null | grep -q 'gateway:'; then
    echo "setup: a default route is still present"; exit 1
fi
if fetch -q -T 10 -o /dev/null "$url" 2>/dev/null; then
    echo "setup: $url still reachable after removing the default routes"; exit 1
fi
exit 0
