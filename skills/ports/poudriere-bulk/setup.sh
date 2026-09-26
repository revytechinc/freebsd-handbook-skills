#!/bin/sh
# Preconditions for ports/poudriere-bulk: poudriere configured, a jail
# testjail of this release (made as ports/poudriere-jail makes it, with
# ALLOW_UNSUPPORTED_SYSTEM on 14.0 to 14.3) and a ports tree testtree (as
# ports/poudriere-ports-tree makes it); no package list and no repository yet.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y poudriere git >/dev/null || exit 1
C=/usr/local/etc/poudriere.conf
if r=$(zfs list -H -o name / 2>/dev/null); then sysrc -f $C FREEBSD_HOST=https://download.FreeBSD.org ZPOOL="${r%%/*}" >/dev/null; else sysrc -f $C FREEBSD_HOST=https://download.FreeBSD.org NO_ZFS=yes >/dev/null; fi || exit 1
mkdir -p /usr/ports/distfiles
v=$(freebsd-version -u | sed 's/-p[0-9]*$//')
case "$v" in
14.[0-3]-RELEASE) poudriere jail -c -j testjail -v $v -m url=https://archive.freebsd.org/old-releases/amd64/amd64/$v/ >/dev/null 2>&1 || exit 1
    printf '%s\n' 'ALLOW_UNSUPPORTED_SYSTEM=yes' > /usr/local/etc/poudriere.d/testjail-make.conf ;;
*) poudriere jail -c -j testjail -v $v >/dev/null 2>&1 || exit 1 ;;
esac
case "$(pkg -vv | grep -e '/quarterly"' -e '/latest"')" in
*'/latest",') B= ;;
*) b=$(git ls-remote --heads https://git.FreeBSD.org/ports.git '20*Q*' </dev/null | sed 's#.*refs/heads/##' | sort | tail -1)
   case "$b" in 20[0-9][0-9]Q[1-4]) ;; *) exit 1 ;; esac; B="-B $b" ;;
esac
poudriere ports -c -p testtree -m git+https $B >/dev/null 2>&1 || exit 1
[ ! -e /usr/local/etc/poudriere.d/testjail-testtree-pkglist ] && [ ! -e /usr/local/poudriere/data/packages/testjail-testtree ]
