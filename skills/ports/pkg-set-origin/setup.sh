#!/bin/sh
# Preconditions for ports/pkg-set-origin: nginx-lite installed (its dependency
# pcre2 has origin devel/pcre2); TEST ONLY: pcre2's recorded origin changed to
# devel/pcre2-old, as if the port had moved; a stamp for verify.sh.
rm -f /var/db/hbskills-origin.stamp
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y nginx-lite >/dev/null || exit 1
pkg set -y -o devel/pcre2:devel/pcre2-old >/dev/null || exit 1
[ "$(pkg query '%o' pcre2)" = devel/pcre2-old ] || exit 1
sleep 1; date +%s > /var/db/hbskills-origin.stamp
