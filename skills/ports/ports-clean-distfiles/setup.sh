#!/bin/sh
# Preconditions for ports/ports-clean-distfiles: pkg and git installed; the
# ports tree in /usr/ports on the branch matching pkg (as ports/ports-tree-git
# does it); portmaster and tree installed from packages; in distfiles: the
# source of tree (installed: must stay), of figlet (not installed: stale), and
# two made-up stale files, one in a subdirectory.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y git >/dev/null || exit 1
case "$(pkg -vv | grep -m1 url)" in
    *'/latest",'*) b= ;;
    *) b=$(git ls-remote --heads https://git.FreeBSD.org/ports.git '20*Q*' </dev/null | tail -1 | sed 's#.*refs/heads/##')
       case "$b" in 20[0-9][0-9]Q[1-4]) ;; *) exit 1 ;; esac   # a branch name, nothing else
       b="-b $b" ;;
esac
git clone --quiet --depth 1 $b https://git.FreeBSD.org/ports.git /usr/ports </dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y portmaster tree >/dev/null || exit 1
v=$(freebsd-version -u)
case "$v" in 14.[0-3]-*) a=ALLOW_UNSUPPORTED_SYSTEM=yes ;; *) a= ;; esac
make -C /usr/ports/sysutils/tree $a fetch >/dev/null 2>&1 || exit 1
make -C /usr/ports/misc/figlet $a fetch >/dev/null 2>&1 || exit 1
mkdir /usr/ports/distfiles/oldstuff || exit 1
: > /usr/ports/distfiles/stale-1.0.tar.gz || exit 1
: > /usr/ports/distfiles/oldstuff/older-0.9.tgz || exit 1
! pkg info -e figlet
