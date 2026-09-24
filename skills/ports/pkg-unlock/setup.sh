#!/bin/sh
# Preconditions for ports/pkg-unlock: pkg installed; nginx-lite (not the package in
# the skill's examples) installed, and locked; every package's lock flag
# saved before the model runs.
rm -f /var/db/hbskills-unlock-before /var/db/hbskills-unlock-before.tmp
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y nginx-lite >/dev/null || exit 1
pkg lock -y nginx-lite >/dev/null || exit 1
[ "$(pkg query '%k' nginx-lite)" = 1 ] || exit 1
pkg query '%n %k' > /var/db/hbskills-unlock-before.tmp || exit 1
LC_ALL=C sort /var/db/hbskills-unlock-before.tmp > /var/db/hbskills-unlock-before || exit 1
rm -f /var/db/hbskills-unlock-before.tmp
