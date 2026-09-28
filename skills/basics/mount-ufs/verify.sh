#!/bin/sh
# Independent check for basics/mount-ufs (test input DEVICE=/dev/md9,
# MOUNTPOINT=/mnt/hbdata, ACCESS=rw): the mount table is the one before the
# skill plus exactly one line, md9 on /mnt/hbdata as ufs with rw and nosuid;
# the file system's hello.txt is readable there, and it is writable;
# /etc/fstab is unchanged.
# Exit 0 / 1.
[ -s /var/db/hb-mountufs ] || { echo "FAIL: no values recorded by setup"; exit 1; }
t=$(mktemp /tmp/hbmount.XXXXXX) || { echo "FAIL: mktemp"; exit 1; }
mount -p > "$t" || { rm -f "$t"; echo "FAIL: mount -p failed"; exit 1; }
new=$(grep -vxF -f /var/db/hb-mountufs "$t")
gone=$(grep -vxF -f "$t" /var/db/hb-mountufs)
rm -f "$t"
[ -z "$gone" ] || { echo "FAIL: mounts gone: '$gone'"; exit 1; }
set -- $new
[ $# = 6 ] && [ "$1" = /dev/md9 ] && [ "$2" = /mnt/hbdata ] && [ "$3" = ufs ] || { echo "FAIL: new mounts: '$new'"; exit 1; }
case ",$4," in *,rw,*) ;; *) echo "FAIL: options '$4' lack rw"; exit 1 ;; esac
case ",$4," in *,nosuid,*) ;; *) echo "FAIL: options '$4' lack nosuid"; exit 1 ;; esac
read -r f0 < /var/db/hb-mountufs.fstab && [ -n "$f0" ] || { echo "FAIL: no fstab checksum recorded"; exit 1; }
[ "$(sha256 -q /etc/fstab)" = "$f0" ] || { echo "FAIL: /etc/fstab changed"; exit 1; }
[ "$(cat /mnt/hbdata/hello.txt)" = hello ] || { echo "FAIL: hello.txt not readable"; exit 1; }
touch /mnt/hbdata/.hbprobe && rm /mnt/hbdata/.hbprobe || { echo "FAIL: not writable"; exit 1; }
echo "OK: md9 mounted rw,nosuid on /mnt/hbdata"; exit 0
