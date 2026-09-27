#!/bin/sh
# Preconditions for basics/users-change (test input USER=hbtest3): an ordinary
# account hbtest3 with no full name given (pw sets "User &") and shell /bin/sh.
grep -qx /bin/tcsh /etc/shells || exit 1
pw usershow hbtest3 >/dev/null 2>&1 && exit 1
pw useradd -n hbtest3 -d /home/hbtest3 -m -s /bin/sh -w no || exit 1
# Recorded for verify.sh: checksums of every other account's entry (not the
# entries, which hold password hashes) and of /etc/shells, and hbtest3's uid:gid.
m=$(grep -v '^hbtest3:' /etc/master.passwd) && [ -n "$m" ] || exit 1
uid=$(id -u hbtest3) && gid=$(id -g hbtest3) && sh=$(sha256 -q /etc/shells) || exit 1
rm -f /var/db/hb-userschg && out="$(printf '%s\n' "$m" | sha256) $sh $uid:$gid" && (set -C; echo "$out" > /var/db/hb-userschg)
