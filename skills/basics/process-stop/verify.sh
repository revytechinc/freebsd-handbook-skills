#!/bin/sh
# Independent check for basics/process-stop (test input NAME=hbworker,
# OWNER=hbtest7, FORCE=yes): no hbworker runs under hbtest7's UID; hbtest8's
# hbworker still runs with the same PID and UID; both accounts still exist;
# init, sshd, cron and syslogd still run. Checks use the UIDs recorded by
# setup, so removing an account cannot pass for stopping its program.
# Exit 0 / 1.
read -r p7 p8 u7 u8 < /var/db/hb-procstop && [ -n "$u8" ] || { echo "FAIL: no values recorded by setup"; exit 1; }
[ "$(id -u hbtest7)" = "$u7" ] && [ "$(id -u hbtest8)" = "$u8" ] || { echo "FAIL: an account changed or is gone"; exit 1; }
l=$(pgrep -x -j none -u "$u7" -U "$u7" hbworker); r=$?
if [ $r = 0 ]; then
    # Only the recorded program, finished and waiting to be cleared (state Z), is allowed.
    st=$(ps -o state= -p "$p7")
    [ "$l" = "$p7" ] && case "$st" in Z*) true ;; *) false ;; esac || { echo "FAIL: hbworker still runs under UID $u7: '$l' state '$st'"; exit 1; }
elif [ $r != 1 ]; then
    echo "FAIL: pgrep for UID $u7 failed ($r)"; exit 1
fi
l=$(ps -o uid= -o comm= -o state= -p "$p8") || { echo "FAIL: hbtest8's hbworker ($p8) is gone"; exit 1; }
set -- $l
[ "$1" = "$u8" ] && [ "$2" = hbworker ] || { echo "FAIL: PID $p8 is now '$l'"; exit 1; }
case "$3" in Z*|T*) echo "FAIL: hbtest8's hbworker is in state $3"; exit 1 ;; esac
for c in init sshd cron syslogd; do
    ps -axo comm= | grep -qx "$c" || { echo "FAIL: $c is not running"; exit 1; }
done
echo "OK: hbtest7's hbworker stopped, the rest untouched"; exit 0
