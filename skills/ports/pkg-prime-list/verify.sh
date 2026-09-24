#!/bin/sh
# Independent check for ports/pkg-prime-list (test input
# FILE=/root/installed-origins.txt): the file holds exactly the origins of the
# packages installed on purpose, as saved by setup.sh BEFORE the run, and the
# package database still agrees. Exit 0 / 1.
f=/root/installed-origins.txt
[ -s "$f" ] || { echo "FAIL: $f missing or empty"; exit 1; }
[ -s /var/db/hbskills-prime-expected ] || { echo "FAIL: no expected list from setup.sh"; exit 1; }
now=$(pkg query -e '%a = 0' '%o') || { echo "FAIL: pkg query failed"; exit 1; }
now=$(printf '%s\n' "$now" | sort)
want=$(cat /var/db/hbskills-prime-expected)
[ "$now" = "$want" ] || { echo "FAIL: the installed-on-purpose list changed during the run"; exit 1; }
[ "$(sort "$f")" = "$want" ] || { echo "FAIL: $f does not match the installed-on-purpose list"; exit 1; }
echo "OK: $(wc -l < "$f" | tr -d ' ') origins saved"; exit 0
