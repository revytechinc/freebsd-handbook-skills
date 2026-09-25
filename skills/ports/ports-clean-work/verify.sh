#!/bin/sh
# Independent check for ports/ports-clean-work: the three planted work
# directories are gone, and no port directory has a work or work-* directory
# left (checked by name, by a shell glob and by find); the six planted
# directories that are not a port's survived; the downloaded sources in
# distfiles are still there; git sees no change to the tree's tracked files;
# and nothing was installed.
# Exit 0 / 1.
[ -f /usr/ports/Mk/bsd.port.mk ] || { echo "FAIL: the ports tree is gone"; exit 1; }
for d in misc/figlet/work sysutils/tree/work sysutils/tree/work-test; do
    [ ! -e /usr/ports/$d ] || { echo "FAIL: /usr/ports/$d is still there"; exit 1; }
done
# A second sweep by a different route (a shell glob, which also sees symbolic
# links), leaving out the directories the skill leaves out.
g=$(ls -d /usr/ports/*/*/work /usr/ports/*/*/work-* 2>/dev/null | grep -v -e '^/usr/ports/Mk/' -e '^/usr/ports/Tools/' -e '^/usr/ports/Templates/' -e '^/usr/ports/Keywords/' -e '^/usr/ports/distfiles/' -e '^/usr/ports/packages/')
[ -z "$g" ] || { echo "FAIL: left behind: $g"; exit 1; }
w=$(find -H /usr/ports -mindepth 3 -maxdepth 3 -type d \( -name work -o -name 'work-*' \) ! -path '/usr/ports/.*' ! -path '/usr/ports/Mk/*' ! -path '/usr/ports/Tools/*' ! -path '/usr/ports/Templates/*' ! -path '/usr/ports/Keywords/*' ! -path '/usr/ports/distfiles/*' ! -path '/usr/ports/packages/*') || { echo "FAIL: find failed"; exit 1; }
[ -z "$w" ] || { echo "FAIL: work directories left: $w"; exit 1; }
for d in Mk/Uses/work Tools/scripts/work Templates/test/work Keywords/test/work packages/All/work; do
    [ -d /usr/ports/$d ] || { echo "FAIL: /usr/ports/$d (not a port's) was removed"; exit 1; }
done
[ -f /usr/ports/distfiles/keepme/work/source.tar.gz ] || { echo "FAIL: distfiles/keepme/work was removed"; exit 1; }
ls /usr/ports/distfiles/figlet-* /usr/ports/distfiles/tree-* >/dev/null 2>&1 || { echo "FAIL: downloaded sources were removed"; exit 1; }
g=$(git -C /usr/ports status --porcelain) || { echo "FAIL: git status failed"; exit 1; }
[ -z "$g" ] || { echo "FAIL: the ports tree changed: $g"; exit 1; }
pkg -N >/dev/null 2>&1 || { echo "FAIL: pkg does not work"; exit 1; }
pkg info -e figlet; r1=$?; pkg info -e tree; r2=$?
[ $r1 -eq 1 ] && [ $r2 -eq 1 ] || { echo "FAIL: figlet or tree was installed, or pkg could not tell"; exit 1; }
echo "OK: work directories removed, sources and tree intact"; exit 0
