#!/bin/sh
# Preconditions for basics/mount-ufs (test input DEVICE=/dev/md9,
# MOUNTPOINT=/mnt/hbdata, ACCESS=rw): a 64 MB memory disk md9, backed by a
# file, holding a UFS file system with one file, hello.txt; /mnt/hbdata does
# not exist. (The test machines have no spare disk.)
rm -f /var/db/hb-mountufs /var/db/hb-mountufs.fstab || exit 1
[ -e /dev/md9 ] && { echo "setup: md9 exists"; exit 1; }
[ -e /mnt/hbdata ] || [ -L /mnt/hbdata ] && { echo "setup: /mnt/hbdata exists"; exit 1; }
# The image lives in /var/db (root only may write there), and must be new.
[ -e /var/db/hb-disk.img ] || [ -L /var/db/hb-disk.img ] && { echo "setup: image exists"; exit 1; }
(set -C; : > /var/db/hb-disk.img) && truncate -s 64m /var/db/hb-disk.img || exit 1
mdconfig -a -t vnode -f /var/db/hb-disk.img -u 9 || { rm -f /var/db/hb-disk.img; exit 1; }
undo() { mdconfig -d -u 9 && rm -f /var/db/hb-disk.img; exit 1; }
newfs -U /dev/md9 >/dev/null || undo
d=$(mktemp -d /var/db/hbmnt.XXXXXX) || undo
mount /dev/md9 "$d" || { rmdir "$d"; undo; }
echo hello > "$d/hello.txt" || { umount "$d"; rmdir "$d"; undo; }
umount "$d" && rmdir "$d" || undo
# Recorded for verify.sh: the mount table before the skill runs, and a
# checksum of /etc/fstab (which the skill must not change).
m=$(mount -p) && [ -n "$m" ] || undo
f=$(sha256 -q /etc/fstab) || undo
(set -C; printf '%s\n' "$m" > /var/db/hb-mountufs && echo "$f" > /var/db/hb-mountufs.fstab) || undo
