#!/bin/sh
# Independent check for ports/ports-clean-distfiles: the source of the
# installed port (tree) is still in /usr/ports/distfiles; the source of the
# port that is not installed (figlet), the two made-up stale files, and the
# folder one of them was in are gone; no index file was downloaded; git sees no change to the ports tree's
# tracked files; and tree is still installed.
# Exit 0 / 1.
d=/usr/ports/distfiles
[ -f /usr/ports/Mk/bsd.port.mk ] && [ -d $d ] || { echo "FAIL: ports tree or distfiles directory is gone"; exit 1; }
ls $d/tree-* >/dev/null 2>&1 || { echo "FAIL: the source of the installed port tree was removed"; exit 1; }
for f in $d/figlet-* $d/stale-1.0.tar.gz $d/oldstuff/older-0.9.tgz $d/oldstuff; do
    [ ! -e "$f" ] || { echo "FAIL: $f is still there"; exit 1; }
done
! ls /usr/ports | grep -q '^INDEX' || { echo "FAIL: an INDEX file was downloaded"; exit 1; }
g=$(git -C /usr/ports status --porcelain) || { echo "FAIL: git status failed"; exit 1; }
[ -z "$g" ] || { echo "FAIL: the ports tree changed: $g"; exit 1; }
pkg -N >/dev/null 2>&1 || { echo "FAIL: pkg does not work"; exit 1; }
pkg info -e tree || { echo "FAIL: tree is no longer installed"; exit 1; }
echo "OK: stale sources removed, the installed port's source kept"; exit 0
