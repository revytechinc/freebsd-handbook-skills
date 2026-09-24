#!/bin/sh
# Independent check for ports/pkg-set-automatic (test input PACKAGE=nginx-lite):
# nginx-lite is still installed and now marked automatic, and no other
# package's mark changed (compared with the list setup.sh saved). Exit 0 / 1.
[ -s /var/db/hbskills-setauto-before ] || { echo "FAIL: no saved list from setup.sh"; exit 1; }
now=$(pkg query '%n %a') || { echo "FAIL: pkg query failed"; exit 1; }
now=$(printf '%s\n' "$now" | sort)
want=$(sed 's/^nginx-lite 0$/nginx-lite 1/' /var/db/hbskills-setauto-before)
printf '%s\n' "$now" | grep -qx 'nginx-lite 1' || { echo "FAIL: nginx-lite is not installed or not marked automatic"; exit 1; }
[ "$now" = "$want" ] || { echo "FAIL: other packages' marks changed too"; exit 1; }
echo "OK: only nginx-lite changed, now automatic"; exit 0
