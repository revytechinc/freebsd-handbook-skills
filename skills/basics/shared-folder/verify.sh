#!/bin/sh
# Independent check for basics/shared-folder (test input NAME=hbproj,
# GROUP=hbshare): /home/hbproj is a real folder, mode 1770, owner root, group
# hbshare; each member can create a file there, which gets the group hbshare;
# one member is refused ("Operation not permitted") deleting the other's
# file; the non-member, who can run commands, is refused ("Permission
# denied") listing the folder. The test files are removed afterwards.
# Exit 0 / 1.
D=/home/hbproj
E="env -i PATH=/bin:/usr/bin"
clean() { rm -f "$D/hb-a.txt" "$D/hb-b.txt"; }
s=$(stat -f '%HT %Mp%03Lp %Su:%Sg' "$D") || { echo "FAIL: no $D"; exit 1; }
[ "$s" = "Directory 1770 root:hbshare" ] || { echo "FAIL: $D is '$s'"; exit 1; }
$E su -m hbta -c "echo a > $D/hb-a.txt" || { clean; echo "FAIL: member hbta cannot create a file"; exit 1; }
g=$(stat -f '%Su:%Sg' "$D/hb-a.txt") || { clean; echo "FAIL: file not created"; exit 1; }
[ "$g" = "hbta:hbshare" ] || { clean; echo "FAIL: new file is '$g'"; exit 1; }
$E su -m hbtb -c "echo b > $D/hb-b.txt" || { clean; echo "FAIL: member hbtb cannot create a file"; exit 1; }
out=$($E su -m hbtb -c "rm -f $D/hb-a.txt" 2>&1)
case "$out" in *"Operation not permitted"*) ;; *) clean; echo "FAIL: hbtb deleting hbta's file gave '$out'"; exit 1 ;; esac
[ -e "$D/hb-a.txt" ] || { clean; echo "FAIL: hbta's file is gone"; exit 1; }
$E su -m hbtc -c "ls /home >/dev/null" || { clean; echo "FAIL: cannot run commands as hbtc"; exit 1; }
out=$($E su -m hbtc -c "ls $D" 2>&1)
case "$out" in *"Permission denied"*) ;; *) clean; echo "FAIL: non-member listing gave '$out'"; exit 1 ;; esac
clean
echo "OK: $D is a shared folder for hbshare"; exit 0
