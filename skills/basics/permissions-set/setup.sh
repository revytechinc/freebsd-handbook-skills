#!/bin/sh
# Preconditions for basics/permissions-set (test input
# FILE=/home/hbtest5/notes.txt, MODE=600): an ordinary account hbtest5 whose
# home holds notes.txt, readable by everyone (644), and a second file, plan.txt.
rm -f /var/db/hb-permset || exit 1
pw usershow hbtest5 >/dev/null 2>&1 && exit 1
pw useradd -n hbtest5 -d /home/hbtest5 -m -s /bin/sh -w no || exit 1
printf 'private notes\n' > /home/hbtest5/notes.txt || exit 1
printf 'plan\n' > /home/hbtest5/plan.txt || exit 1
chown hbtest5:hbtest5 /home/hbtest5/notes.txt /home/hbtest5/plan.txt || exit 1
chmod 644 /home/hbtest5/notes.txt /home/hbtest5/plan.txt || exit 1
# Recorded for verify.sh: every path's mode, owner and group in the home except
# notes.txt, and notes.txt's content checksum.
f=$(find /home/hbtest5 ! -path /home/hbtest5/notes.txt -exec stat -f '%N %Mp%Lp %Su:%Sg' {} +) && [ -n "$f" ] || exit 1
l=$(printf '%s\n' "$f" | sort)
c=$(sha256 -q /home/hbtest5/notes.txt) || exit 1
out="$c $(printf '%s\n' "$l" | sha256)" && (set -C; echo "$out" > /var/db/hb-permset)
