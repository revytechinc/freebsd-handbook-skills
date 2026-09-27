#!/bin/sh
# Independent check for basics/permissions-set (test input
# FILE=/home/hbtest5/notes.txt, MODE=600): notes.txt is now mode 0600, still
# owned by hbtest5:hbtest5 with the same content, and nothing else in the home
# changed mode, owner or group.
# Exit 0 / 1.
read -r c0 l0 < /var/db/hb-permset || { echo "FAIL: no values recorded by setup"; exit 1; }
s=$(stat -f '%HT %Mp%Lp %Su:%Sg' /home/hbtest5/notes.txt) || { echo "FAIL: notes.txt missing"; exit 1; }
[ "$s" = "Regular File 0600 hbtest5:hbtest5" ] || { echo "FAIL: notes.txt is '$s'"; exit 1; }
[ "$(sha256 -q /home/hbtest5/notes.txt)" = "$c0" ] || { echo "FAIL: notes.txt content changed"; exit 1; }
f=$(find /home/hbtest5 ! -path /home/hbtest5/notes.txt -exec stat -f '%N %Mp%Lp %Su:%Sg' {} +) && [ -n "$f" ] || { echo "FAIL: cannot list the home"; exit 1; }
l=$(printf '%s\n' "$f" | sort)
[ "$(printf '%s\n' "$l" | sha256)" = "$l0" ] || { echo "FAIL: something else in the home changed"; exit 1; }
echo "OK: notes.txt is 0600"; exit 0
