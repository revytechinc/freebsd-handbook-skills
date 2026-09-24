#!/bin/sh
# Independent check for ports/pkg-lock (test input PACKAGE=nginx-lite): nginx-lite
# is locked, and no other package's lock flag changed. Exit 0 / 1.
[ -s /var/db/hbskills-lock-before ] || { echo "FAIL: no saved list from setup.sh"; exit 1; }
now=$(pkg query '%n %k') || { echo "FAIL: pkg query failed"; exit 1; }
now=$(printf '%s\n' "$now" | LC_ALL=C sort)
printf '%s\n' "$now" | grep -qx 'nginx-lite 1' || { echo "FAIL: nginx-lite is not locked"; exit 1; }
want=$(sed 's/^nginx-lite 0$/nginx-lite 1/' /var/db/hbskills-lock-before)
if [ "$now" != "$want" ]; then
    echo "FAIL: the package list or other lock flags changed:"
    a=$(mktemp) && b=$(mktemp) || exit 1
    printf '%s\n' "$want" > "$a"; printf '%s\n' "$now" > "$b"
    diff "$a" "$b" | grep '^[<>]'; rm -f "$a" "$b"; exit 1
fi
echo "OK: only nginx-lite changed"; exit 0
