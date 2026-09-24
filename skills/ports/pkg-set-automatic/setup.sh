#!/bin/sh
# Preconditions for ports/pkg-set-automatic: pkg installed; nginx-lite (not the
# package in the skill's examples) installed on purpose; every package's mark
# saved before the model runs, so verify.sh can check that only nginx-lite
# changed.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y nginx-lite >/dev/null || exit 1
[ "$(pkg query '%a' nginx-lite)" = 0 ] || exit 1
pkg query '%n %a' > /var/db/hbskills-setauto-before.tmp || exit 1
sort /var/db/hbskills-setauto-before.tmp > /var/db/hbskills-setauto-before || exit 1
rm -f /var/db/hbskills-setauto-before.tmp
