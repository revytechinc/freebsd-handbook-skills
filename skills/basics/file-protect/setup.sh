#!/bin/sh
# Preconditions for basics/file-protect (test input
# FILE=/home/hbtest6/contract.txt): an ordinary account hbtest6 whose home
# holds contract.txt and a second file, other.txt, neither with any flag.
rm -f /var/db/hb-fileprot || exit 1
pw usershow hbtest6 >/dev/null 2>&1 && exit 1
pw useradd -n hbtest6 -d /home/hbtest6 -m -s /bin/sh -w no || exit 1
printf 'signed contract\n' > /home/hbtest6/contract.txt || exit 1
printf 'other\n' > /home/hbtest6/other.txt || exit 1
chown hbtest6:hbtest6 /home/hbtest6/contract.txt /home/hbtest6/other.txt || exit 1
# Recorded for verify.sh: contract.txt's flags (none, or "uarch" on ZFS),
# mode, owner and content checksum.
s=$(stat -f '%Sf %Mp%Lp %Su:%Sg' /home/hbtest6/contract.txt) || exit 1
c=$(sha256 -q /home/hbtest6/contract.txt) || exit 1
out="$s $c" && (set -C; echo "$out" > /var/db/hb-fileprot)
