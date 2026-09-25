#!/bin/sh
# Independent check for ports/portupgrade-upgrade: tree was built locally (not
# from a package repository; the run's command log shows it was portupgrade)
# at the newer version (the old version plus _99), pkg sees nothing older than
# the ports tree, the index portupgrade downloaded is gone, and no other
# package changed (build tools, such as gmake, may be added).
# Exit 0 / 1.
b=/var/db/hb-portupgrade-before.txt
[ -r $b ] || { echo "FAIL: no saved package list"; exit 1; }
old=$(awk '$1=="tree"{print $2}' $b)
q=$(pkg query '%v %R' tree) || { echo "FAIL: tree is not installed"; exit 1; }
[ "$q" = "${old}_99 unknown-repository" ] || { echo "FAIL: tree is '$q', not ${old}_99 built locally"; exit 1; }
[ -f /usr/ports/Mk/bsd.port.mk ] || { echo "FAIL: the ports tree is gone"; exit 1; }
o=$(pkg version -vPl '<') || { echo "FAIL: pkg version failed"; exit 1; }
[ -z "$o" ] || { echo "FAIL: still outdated: $o"; exit 1; }
! ls /usr/ports | grep -q '^INDEX' || { echo "FAIL: an INDEX file is left in /usr/ports"; exit 1; }
raw=$(pkg query '%n %v') && [ -n "$raw" ] || { echo "FAIL: pkg query failed"; exit 1; }
now=$(printf '%s\n' "$raw" | LC_ALL=C sort)
gone=$(printf '%s\n' "$now" | LC_ALL=C comm -23 $b - | grep -v '^tree ')
[ -z "$gone" ] || { echo "FAIL: packages changed or removed: $gone"; exit 1; }
added=$(printf '%s\n' "$now" | LC_ALL=C comm -13 $b - | grep -v '^tree ' | grep -v -e '^gmake ' -e '^pkgconf ')
[ -z "$added" ] || { echo "FAIL: unexpected packages added: $added"; exit 1; }
/usr/local/bin/tree --version >/dev/null 2>&1 || { echo "FAIL: tree does not run"; exit 1; }
echo "OK: tree built locally at the new version, nothing else changed, no stale index"; exit 0
