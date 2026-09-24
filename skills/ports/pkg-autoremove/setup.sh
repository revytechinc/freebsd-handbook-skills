#!/bin/sh
# Preconditions for ports/pkg-autoremove: pkg installed; curl installed on
# purpose (its dependencies must survive); nginx-lite installed then removed,
# which leaves its dependency pcre2 behind as an unneeded package. Records the
# number of base-system packages, which must not change.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y curl nginx-lite >/dev/null || exit 1
pkg delete -y nginx-lite >/dev/null || exit 1
pkg info -e pcre2 || exit 1
pkg query -e '%n ~ FreeBSD-*' '%n' | wc -l | tr -d ' ' > /var/db/hbskills-base-count
