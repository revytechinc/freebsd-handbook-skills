#!/bin/sh
# Preconditions for basics/groups-add (test input GROUP=hbteam, USER=hbtest4):
# ordinary accounts hbtest4 and hbother, and an existing group hbteam whose
# only member is hbother, so the skill must add hbtest4 without removing
# hbother (the Handbook's -M would replace the member list).
pw usershow hbtest4 >/dev/null 2>&1 && exit 1
pw usershow hbother >/dev/null 2>&1 && exit 1
pw groupshow hbteam >/dev/null 2>&1 && exit 1
pw useradd -n hbtest4 -d /home/hbtest4 -m -s /bin/sh -w no || exit 1
pw useradd -n hbother -d /home/hbother -m -s /bin/sh -w no || exit 1
pw groupadd hbteam -M hbother || exit 1
# Recorded for verify.sh: hbteam's GID, and checksums of every other group's
# entry and of the accounts file (not shown: it holds password hashes).
g=$(grep -v '^hbteam:' /etc/group) && [ -n "$g" ] || exit 1
m=$(cat /etc/master.passwd) && [ -n "$m" ] || exit 1
gid=$(pw groupshow hbteam | cut -d: -f3) && [ -n "$gid" ] || exit 1
rm -f /var/db/hb-groupsadd && out="$gid $(printf '%s\n' "$g" | sha256) $(printf '%s\n' "$m" | sha256)" && (set -C; echo "$out" > /var/db/hb-groupsadd)
