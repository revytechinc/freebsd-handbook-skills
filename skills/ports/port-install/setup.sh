#!/bin/sh
# Preconditions for ports/port-install: pkg installed; the ports tree in
# /usr/ports on the branch matching pkg (as ports/ports-tree-git does it);
# sysutils/tree (the test port, not the skill's example) not installed.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y git >/dev/null || exit 1
case "$(pkg -vv | grep -m1 url)" in
    *'/latest",'*) b= ;;
    *) b=$(git ls-remote --heads https://git.FreeBSD.org/ports.git '20*Q*' </dev/null | tail -1 | sed 's#.*refs/heads/##')
       [ -n "$b" ] || exit 1; b="-b $b" ;;
esac
git clone --quiet --depth 1 $b https://git.FreeBSD.org/ports.git /usr/ports </dev/null || exit 1
! pkg info -e tree
