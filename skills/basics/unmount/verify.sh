#!/bin/sh
# Independent check for basics/unmount (test input MOUNTPOINT=/mnt/hbdata):
# the mount table is exactly the one before, without /mnt/hbdata; md9 is
# still attached and its file system is clean (fsck -n) with hello.txt on it;
# /mnt/hbdata is still an empty folder; /etc/fstab is unchanged.
# Exit 0 / 1.
[ -s /var/db/hb-unmount ] || { echo "FAIL: no values recorded by setup"; exit 1; }
m=$(mount -p) || { echo "FAIL: mount -p failed"; exit 1; }
[ "$m" = "$(cat /var/db/hb-unmount)" ] || { echo "FAIL: mount table is now: $m"; exit 1; }
read -r f0 < /var/db/hb-unmount.fstab && [ -n "$f0" ] || { echo "FAIL: no fstab checksum recorded"; exit 1; }
[ "$(sha256 -q /etc/fstab)" = "$f0" ] || { echo "FAIL: /etc/fstab changed"; exit 1; }
[ -d /mnt/hbdata ] && [ ! -L /mnt/hbdata ] && [ -z "$(ls -A /mnt/hbdata)" ] || { echo "FAIL: /mnt/hbdata is not an empty folder"; exit 1; }
[ -c /dev/md9 ] || { echo "FAIL: md9 is gone"; exit 1; }
fsck -n -t ufs /dev/md9 >/dev/null 2>&1 || { echo "FAIL: fsck -n reports problems on md9"; exit 1; }
t=$(mktemp -d /var/db/hbchk.XXXXXX) || { echo "FAIL: mktemp"; exit 1; }
mount -t ufs -o ro /dev/md9 "$t" || { rmdir "$t"; echo "FAIL: cannot mount md9 read-only"; exit 1; }
c=$(cat "$t/hello.txt")
umount "$t" || { echo "FAIL: cannot unmount the check mount $t"; exit 1; }
rmdir "$t" || { echo "FAIL: cannot remove $t"; exit 1; }
[ "$c" = hello ] || { echo "FAIL: hello.txt is '$c'"; exit 1; }
echo "OK: /mnt/hbdata unmounted cleanly"; exit 0
