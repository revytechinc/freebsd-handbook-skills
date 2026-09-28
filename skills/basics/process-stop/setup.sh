#!/bin/sh
# Preconditions for basics/process-stop (test input NAME=hbworker,
# OWNER=hbtest7, FORCE=yes): ordinary accounts hbtest7 and hbtest8, each
# running one program named hbworker (a copy of /bin/sh) that ignores TERM.
# hbtest8's must survive.
rm -f /var/db/hb-procstop || exit 1
for u in hbtest7 hbtest8; do pw usershow $u >/dev/null 2>&1 && { echo "setup: $u exists"; exit 1; }; done
[ -e /usr/local/bin/hbworker ] && { echo "setup: hbworker exists"; exit 1; }
mkdir -p /usr/local/bin && cp /bin/sh /usr/local/bin/hbworker || exit 1
for u in hbtest7 hbtest8; do
    pw useradd -n $u -d /home/$u -m -s /bin/sh -w no || exit 1
    env -i PATH=/bin:/usr/bin su -m $u -c '/usr/sbin/daemon -f /usr/local/bin/hbworker -c "trap \"\" TERM; while :; do sleep 1; done"' || exit 1
done
sleep 1
p7=$(pgrep -x -j none -u hbtest7 -U hbtest7 hbworker) && p8=$(pgrep -x -j none -u hbtest8 -U hbtest8 hbworker) || { echo "setup: workers not running"; exit 1; }
[ "$(echo $p7 | wc -w)" -eq 1 ] && [ "$(echo $p8 | wc -w)" -eq 1 ] || exit 1
# Recorded for verify.sh: both PIDs and both UIDs.
u7=$(id -u hbtest7) && u8=$(id -u hbtest8) || exit 1
(set -C; echo "$p7 $p8 $u7 $u8" > /var/db/hb-procstop) || exit 1
