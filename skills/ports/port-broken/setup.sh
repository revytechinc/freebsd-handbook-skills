#!/bin/sh
# Preconditions for ports/port-broken (test input PORT=sysutils/lsof): pkg and
# git installed, and the ports tree in /usr/ports on the branch matching pkg (as
# ports/ports-tree-git does it). lsof will not build here: it needs kernel
# sources, which the test machines do not have.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y git >/dev/null || exit 1
case "$(pkg -vv | grep -m1 url)" in
    *'/latest",'*) b= ;;
    *) b=$(git ls-remote --heads https://git.FreeBSD.org/ports.git '20*Q*' </dev/null | tail -1 | sed 's#.*refs/heads/##')
       case "$b" in 20[0-9][0-9]Q[1-4]) ;; *) exit 1 ;; esac   # a branch name, nothing else
       b="-b $b" ;;
esac
git clone --quiet --depth 1 $b https://git.FreeBSD.org/ports.git /usr/ports </dev/null || exit 1
[ ! -d /usr/src/sys ]
