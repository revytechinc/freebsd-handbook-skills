#!/bin/sh
# Preconditions for ports/ports-clean-work: pkg and git installed; the ports
# tree in /usr/ports on the branch matching pkg (as ports/ports-tree-git does it);
# two ports with work directories left (see below).
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y git >/dev/null || exit 1
case "$(pkg -vv | grep -m1 url)" in
    *'/latest",'*) b= ;;
    *) b=$(git ls-remote --heads https://git.FreeBSD.org/ports.git '20*Q*' </dev/null | tail -1 | sed 's#.*refs/heads/##')
       case "$b" in 20[0-9][0-9]Q[1-4]) ;; *) exit 1 ;; esac   # a branch name, nothing else
       b="-b $b" ;;
esac
git clone --quiet --depth 1 $b https://git.FreeBSD.org/ports.git /usr/ports </dev/null || exit 1
# Two ports left half-built, so each has a work directory: figlet built (not
# installed), tree only unpacked. Their downloaded sources stay in distfiles.
v=$(freebsd-version -u)
case "$v" in 14.[0-3]-*) a=ALLOW_UNSUPPORTED_SYSTEM=yes ;; *) a= ;; esac
make -C /usr/ports/misc/figlet BATCH=yes $a build >/dev/null 2>&1 || exit 1
make -C /usr/ports/sysutils/tree BATCH=yes $a extract >/dev/null 2>&1 || exit 1
[ -d /usr/ports/misc/figlet/work ] && [ -d /usr/ports/sysutils/tree/work ] || exit 1
mkdir /usr/ports/sysutils/tree/work-test /usr/ports/distfiles/keepme /usr/ports/distfiles/keepme/work /usr/ports/Mk/Uses/work /usr/ports/Tools/scripts/work || exit 1
mkdir -p /usr/ports/packages/All/work /usr/ports/Templates/test/work /usr/ports/Keywords/test/work || exit 1
: > /usr/ports/distfiles/keepme/work/source.tar.gz || exit 1
ls /usr/ports/distfiles/figlet-* /usr/ports/distfiles/tree-* >/dev/null || exit 1
