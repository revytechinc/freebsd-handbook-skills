#!/bin/sh
# Independent check for basics/users-remove (test input USER=hbtest2): the
# account, its own group and its membership of operator are gone; its home
# folder, mail file and crontab are gone; none of its processes run; and
# root, nobody and the group operator are still there.
# Exit 0 / 1.
pw usershow hbtest2 >/dev/null 2>&1; r=$?; [ $r -eq 67 ] || { echo "FAIL: hbtest2 still exists, or pw failed ($r)"; exit 1; }
pw groupshow hbtest2 >/dev/null 2>&1; r=$?; [ $r -eq 65 ] || { echo "FAIL: group hbtest2 still exists, or pw failed ($r)"; exit 1; }
o=$(pw groupshow operator) || { echo "FAIL: group operator is gone"; exit 1; }
case "$o" in *hbtest2*) echo "FAIL: still in operator: $o"; exit 1 ;; esac
if kldstat -q -m zfs; then
    z=$(zfs list -H -o name,mountpoint -t filesystem) || { echo "FAIL: zfs list failed"; exit 1; }
    ! printf '%s\n' "$z" | awk -F'\t' '$1 ~ /\/hbtest2$/ || $2 == "/home/hbtest2"' | grep -q . || { echo "FAIL: a home dataset for hbtest2 is still there"; exit 1; }
fi
for f in /home/hbtest2 /var/mail/hbtest2 /var/cron/tabs/hbtest2; do
    [ ! -e "$f" ] && [ ! -L "$f" ] || { echo "FAIL: $f still there"; exit 1; }
done
u=$(cat /var/db/hb-rmuser-uid) && [ -n "$u" ] || { echo "FAIL: no saved uid"; exit 1; }
pgrep -U "$u" >/dev/null; r=$?; [ $r -eq 1 ] || { echo "FAIL: processes of uid $u still run, or pgrep failed ($r)"; exit 1; }
pw usershow root >/dev/null && pw usershow nobody >/dev/null || { echo "FAIL: a system account is gone"; exit 1; }
echo "OK: hbtest2 removed completely"; exit 0
