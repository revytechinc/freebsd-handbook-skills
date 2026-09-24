#!/bin/sh
# Independent check for ports/port-deinstall (test input PORT=sysutils/tree):
# tree is gone, and it is the only package that went (compared with the list
# setup.sh saved; the build dependency gmake may also have been left, which
# is fine). Exit 0 / 1.
pkg info -e tree && { echo "FAIL: tree is still installed"; exit 1; }
[ -s /var/db/hbskills-deinstall-before ] || { echo "FAIL: no saved list from setup.sh"; exit 1; }
now=$(pkg query '%n') || { echo "FAIL: pkg query failed"; exit 1; }
want=$(grep -vx tree /var/db/hbskills-deinstall-before)
[ "$(printf '%s\n' "$now" | LC_ALL=C sort)" = "$want" ] || { echo "FAIL: other packages changed too"; exit 1; }
echo "OK: only tree removed"; exit 0
