#!/bin/sh
# Preconditions for ports/poudriere-jail: poudriere installed from packages,
# its configuration as the package installed it (so, on ZFS, poudriere
# refuses to run until step 3), and no jails yet.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y poudriere >/dev/null || exit 1
grep -q '^FREEBSD_HOST=_PROTO_://_CHANGE_THIS_' /usr/local/etc/poudriere.conf || exit 1
[ ! -e /usr/local/etc/poudriere.d/testjail-make.conf ] || exit 1
for d in /usr/local/poudriere/jails /usr/local/etc/poudriere.d/jails; do
    [ ! -e $d ] || [ -z "$(ls $d)" ] || exit 1
done
