#!/bin/sh
# Independent check for basics/users-change (test input USER=hbtest3,
# FULLNAME=Changed Name, SHELL=/bin/tcsh): the account now has that full name
# and shell, and everything else about it is unchanged (UID, group, home,
# password field, class, change and expiry dates), and every other account
# and /etc/shells are untouched.
# Exit 0 / 1.
l=$(pw usershow hbtest3) || { echo "FAIL: no user hbtest3"; exit 1; }
IFS=: read -r n p uid gid cls ch ex gecos home shell <<EOT
$l
EOT
[ "$gecos" = "Changed Name" ] || { echo "FAIL: full name is '$gecos'"; exit 1; }
[ "$shell" = "/bin/tcsh" ] || { echo "FAIL: shell is '$shell'"; exit 1; }
[ "$home" = "/home/hbtest3" ] && [ "$p" = "*" ] && [ "$cls" = "" ] && [ "$ch" = "0" ] && [ "$ex" = "0" ] && [ "$(id -gn hbtest3)" = "hbtest3" ] || { echo "FAIL: other fields changed: '$l'"; exit 1; }
read -r othersum shellsum ids < /var/db/hb-userschg || { echo "FAIL: no values recorded by setup"; exit 1; }
m=$(grep -v '^hbtest3:' /etc/master.passwd) && [ -n "$m" ] || { echo "FAIL: cannot read the other accounts"; exit 1; }
[ "$(printf '%s\n' "$m" | sha256)" = "$othersum" ] || { echo "FAIL: another account's entry changed"; exit 1; }
sh=$(sha256 -q /etc/shells) || { echo "FAIL: cannot read /etc/shells"; exit 1; }
[ "$sh" = "$shellsum" ] || { echo "FAIL: /etc/shells changed"; exit 1; }
[ "$uid:$gid" = "$ids" ] || { echo "FAIL: uid:gid is $uid:$gid, was $ids"; exit 1; }
echo "OK: hbtest3 now 'Changed Name' with /bin/tcsh"; exit 0
