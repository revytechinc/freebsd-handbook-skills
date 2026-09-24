#!/bin/sh
# Preconditions for ports/pkg-audit: pkg installed; curl installed (with its
# dependency libssh2); TEST ONLY: libssh2's recorded version set to 1.8.0,
# which the vulnerability list covers, so there is something to find. No
# vulnerability list downloaded yet; a time stamp for verify.sh.
rm -f /var/db/pkg/vuln.xml /var/db/hbskills-audit.stamp
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y curl >/dev/null || exit 1
echo "UPDATE packages SET version='1.8.0' WHERE name='libssh2';" | pkg shell || exit 1
[ "$(pkg query '%v' libssh2)" = 1.8.0 ] || exit 1
rm -f /var/db/pkg/vuln.xml
sleep 1; date +%s > /var/db/hbskills-audit.stamp
