#!/bin/sh
# Preconditions for ports/poudriere-ports-tree: poudriere and git installed,
# poudriere configured as ports/poudriere-jail step 3 leaves it (ZPOOL on a
# ZFS machine, NO_ZFS on UFS), and no ports trees yet.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y poudriere git >/dev/null || exit 1
C=/usr/local/etc/poudriere.conf
if r=$(zfs list -H -o name / 2>/dev/null); then
    sysrc -f $C FREEBSD_HOST=https://download.FreeBSD.org ZPOOL="${r%%/*}" >/dev/null || exit 1
else
    sysrc -f $C FREEBSD_HOST=https://download.FreeBSD.org NO_ZFS=yes >/dev/null || exit 1
fi
[ "$(poudriere ports -l | wc -l | tr -d ' ')" = 1 ]
