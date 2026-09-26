#!/bin/sh
# Independent check for basics/users-add (test input USER=hbtest1,
# FULLNAME=Test Account, WHEEL=yes): the account exists with that full name,
# shell /bin/sh and home /home/hbtest1; password login is disabled ("*" in
# master.passwd, so no password was set); it has its own group and is in
# wheel; its home folder exists, is owned by it and has the default files
# from /usr/share/skel.
# Exit 0 / 1.
l=$(pw usershow hbtest1) || { echo "FAIL: no user hbtest1"; exit 1; }
IFS=: read -r n p uid gid cls ch ex gecos home shell <<EOT
$l
EOT
[ "$gecos" = "Test Account" ] && [ "$home" = "/home/hbtest1" ] && [ "$shell" = "/bin/sh" ] || { echo "FAIL: account is '$l'"; exit 1; }
[ "$(awk -F: '$1=="hbtest1"{print $2}' /etc/master.passwd)" = "*" ] || { echo "FAIL: password login is not disabled"; exit 1; }
g=$(id -Gn hbtest1) || { echo "FAIL: id failed"; exit 1; }
[ "$(id -gn hbtest1)" = "hbtest1" ] || { echo "FAIL: its primary group is not hbtest1"; exit 1; }
case " $g " in *" wheel "*) ;; *) echo "FAIL: not in wheel ($g)"; exit 1 ;; esac
[ "$(stat -f %Su /home/hbtest1 2>/dev/null)" = "hbtest1" ] || { echo "FAIL: /home/hbtest1 missing or not owned by hbtest1"; exit 1; }
[ -f /home/hbtest1/.profile ] && [ -f /home/hbtest1/.shrc ] || { echo "FAIL: default files missing from the home folder"; exit 1; }
echo "OK: hbtest1 created as asked"; exit 0
