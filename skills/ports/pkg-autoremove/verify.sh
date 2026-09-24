#!/bin/sh
# Independent check for ports/pkg-autoremove: the unneeded pcre2 is gone; curl,
# installed on purpose, and its dependencies still work; no base-system
# package was removed; nothing unneeded is left. Exit 0 / 1.
pkg info -e pcre2 && { echo "FAIL: pcre2 (unneeded) is still installed"; exit 1; }
pkg info -e curl || { echo "FAIL: curl was removed"; exit 1; }
/usr/local/bin/curl --version >/dev/null 2>&1 || { echo "FAIL: curl no longer runs"; exit 1; }
want=$(cat /var/db/hbskills-base-count 2>/dev/null)
have=$(pkg query -e '%n ~ FreeBSD-*' '%n' | wc -l | tr -d ' ')
[ -n "$want" ] && [ "$want" = "$have" ] || { echo "FAIL: base-system packages changed ($want -> $have)"; exit 1; }
pkg autoremove -n 2>&1 | grep -q 'Nothing to do.' || { echo "FAIL: unneeded packages are left"; exit 1; }
echo "OK: pcre2 removed; curl works; $have base packages unchanged"; exit 0
