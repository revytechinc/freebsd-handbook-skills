#!/bin/sh
# Independent check for ports/portmaster-upgrade: tree was built locally (not
# from a package repository; the run's command log shows it was portmaster)
# at the newer version (2.3.2_99 style: the old version plus _99),
# portmaster sees nothing left to upgrade, and no other package changed (build
# tools portmaster installed, such as gmake, may be added).
# Exit 0 / 1.
b=/var/db/hb-portmaster-before.txt
[ -r $b ] || { echo "FAIL: no saved package list"; exit 1; }
old=$(awk '$1=="tree"{print $2}' $b)
q=$(pkg query '%v %R' tree) || { echo "FAIL: tree is not installed"; exit 1; }
[ "$q" = "${old}_99 unknown-repository" ] || { echo "FAIL: tree is '$q', not ${old}_99 built from ports"; exit 1; }
portmaster -L 2>&1 | grep -q 'There are no new versions available' || { echo "FAIL: portmaster still lists upgrades"; exit 1; }
now=$(pkg query '%n %v' | LC_ALL=C sort) || { echo "FAIL: pkg query failed"; exit 1; }
gone=$(printf '%s\n' "$now" | LC_ALL=C comm -23 $b - | grep -v '^tree ')
[ -z "$gone" ] || { echo "FAIL: packages changed or removed: $gone"; exit 1; }
added=$(printf '%s\n' "$now" | LC_ALL=C comm -13 $b - | grep -v '^tree ' | grep -v -e '^gmake ' -e '^pkgconf ')
[ -z "$added" ] || { echo "FAIL: unexpected packages added: $added"; exit 1; }
/usr/local/bin/tree --version >/dev/null 2>&1 || { echo "FAIL: tree does not run"; exit 1; }
echo "OK: tree upgraded by portmaster from ports, nothing else changed"; exit 0
