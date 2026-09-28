#!/bin/sh
# Preconditions for basics/unmount (test input MOUNTPOINT=/mnt/hbdata): a
# 64 MB memory disk md9, backed by a file in /var/db, holding a UFS file
# system with one file, mounted rw,nosuid on /mnt/hbdata, with nothing using
# it. (The test machines have no spare disk.)
rm -f /var/db/hb-unmount /var/db/hb-unmount.fstab || exit 1
[ -e /dev/md9 ] && { echo "setup: md9 exists"; exit 1; }
[ -e /mnt/hbdata ] || [ -L /mnt/hbdata ] && { echo "setup: /mnt/hbdata exists"; exit 1; }
[ -e /var/db/hb-disk.img ] || [ -L /var/db/hb-disk.img ] && { echo "setup: image exists"; exit 1; }
(set -C; : > /var/db/hb-disk.img) && truncate -s 64m /var/db/hb-disk.img || exit 1
mdconfig -a -t vnode -f /var/db/hb-disk.img -u 9 || { rm -f /var/db/hb-disk.img; exit 1; }
made=no; mounted=no
undo() {
    [ $mounted = yes ] && mount -p | awk '$1 == "/dev/md9" && $2 == "/mnt/hbdata"' | grep -q . && umount /mnt/hbdata
    [ $made = yes ] && rmdir /mnt/hbdata
    mdconfig -d -u 9 && rm -f /var/db/hb-disk.img; exit 1
}
newfs -U /dev/md9 >/dev/null || undo
mkdir /mnt/hbdata || undo
made=yes
mount -t ufs -o nosuid,rw /dev/md9 /mnt/hbdata || undo
mounted=yes
echo hello > /mnt/hbdata/hello.txt || undo
# Recorded for verify.sh: the mount table without the test mount, and a
# checksum of /etc/fstab.
m=$(mount -p | awk '$2 != "/mnt/hbdata"') && [ -n "$m" ] || undo
f=$(sha256 -q /etc/fstab) || undo
(set -C; printf '%s\n' "$m" > /var/db/hb-unmount && echo "$f" > /var/db/hb-unmount.fstab) || undo
