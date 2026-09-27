#!/bin/sh
# Independent check for basics/groups-add (test input GROUP=hbteam,
# USER=hbtest4): /etc/group has one hbteam line, with its GID and no password,
# and its members are exactly hbother and hbtest4; id shows hbtest4 in hbteam;
# every other group and every account are unchanged.
# Exit 0 / 1.
read -r gid0 gsum msum < /var/db/hb-groupsadd || { echo "FAIL: no values recorded by setup"; exit 1; }
[ "$(grep -c '^hbteam:' /etc/group)" = 1 ] || { echo "FAIL: not exactly one hbteam line in /etc/group"; exit 1; }
l=$(grep '^hbteam:' /etc/group) || { echo "FAIL: no group hbteam"; exit 1; }
IFS=: read -r n p gid members <<EOT
$l
EOT
[ "$p" = "*" ] || { echo "FAIL: hbteam password field is '$p'"; exit 1; }
[ "$gid" = "$gid0" ] || { echo "FAIL: hbteam GID is $gid, was $gid0"; exit 1; }
sorted=$(printf '%s\n' "$members" | tr ',' '\n' | sort | tr '\n' ' ')
[ "$sorted" = "hbother hbtest4 " ] || { echo "FAIL: hbteam members are '$members'"; exit 1; }
ids=$(id -Gn hbtest4) || { echo "FAIL: id hbtest4 failed"; exit 1; }
printf '%s\n' "$ids" | tr ' ' '\n' | grep -qx hbteam || { echo "FAIL: id does not show hbteam: '$ids'"; exit 1; }
g=$(grep -v '^hbteam:' /etc/group) && [ -n "$g" ] || { echo "FAIL: cannot read /etc/group"; exit 1; }
[ "$(printf '%s\n' "$g" | sha256)" = "$gsum" ] || { echo "FAIL: another group changed"; exit 1; }
m=$(cat /etc/master.passwd) && [ -n "$m" ] || { echo "FAIL: cannot read the accounts"; exit 1; }
[ "$(printf '%s\n' "$m" | sha256)" = "$msum" ] || { echo "FAIL: an account changed"; exit 1; }
echo "OK: hbteam is hbother and hbtest4"; exit 0
