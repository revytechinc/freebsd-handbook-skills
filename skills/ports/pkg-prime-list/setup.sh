#!/bin/sh
# Preconditions for ports/pkg-prime-list: pkg installed; curl and nginx-lite
# installed on purpose (their dependencies are automatic); the test FILE does
# not exist; the expected list saved before the model runs.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y curl nginx-lite >/dev/null || exit 1
[ ! -e /root/installed-origins.txt ] || exit 1
[ "$(pkg query '%a' curl)" = 0 ] && [ "$(pkg query '%a' nginx-lite)" = 0 ] || exit 1
pkg query -e '%a = 0' '%o' > /var/db/hbskills-prime-expected.tmp || exit 1
sort /var/db/hbskills-prime-expected.tmp > /var/db/hbskills-prime-expected || exit 1
rm -f /var/db/hbskills-prime-expected.tmp
