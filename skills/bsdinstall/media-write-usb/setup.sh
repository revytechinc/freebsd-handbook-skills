#!/bin/sh
# Preconditions for bsdinstall/media-write-usb (test input
# IMGPATH=/var/tmp/freebsd-media/FreeBSD-15.1-RELEASE-amd64-mini-memstick.img,
# DEVNAME=md7): the checked, unpacked 15.1 mini-memstick image, and a 1 GB
# memory disk md7 (backed by a file in /var/db) standing in for a USB stick,
# filled with a pattern so a write is visible. (The test machines have no
# USB stick.)
rm -f /var/db/hb-usb.sum || exit 1
D=/var/tmp/freebsd-media I=FreeBSD-15.1-RELEASE-amd64-mini-memstick.img
C=CHECKSUM.SHA256-FreeBSD-15.1-RELEASE-amd64
U=https://download.freebsd.org/releases/amd64/amd64/ISO-IMAGES/15.1
[ -e $D ] || [ -L $D ] && { echo "setup: $D exists"; exit 1; }
[ -e /dev/md7 ] && { echo "setup: md7 exists"; exit 1; }
[ -e /var/db/hb-usb.img ] || [ -L /var/db/hb-usb.img ] && { echo "setup: backing file exists"; exit 1; }
mkdir $D && cd $D || exit 1
env -i PATH=/usr/bin:/bin fetch -q $U/$C && env -i PATH=/usr/bin:/bin fetch -q $U/$I.xz || exit 1
wantxz=$(awk -v f="($I.xz)" '$1 == "SHA256" && $2 == f && $3 == "=" { print $4 }' $C) && [ -n "$wantxz" ] || exit 1
[ "$(sha256 -q $I.xz)" = "$wantxz" ] || { echo "setup: the .xz does not match"; exit 1; }
want=$(awk -v f="($I)" '$1 == "SHA256" && $2 == f && $3 == "=" { print $4 }' $C) && [ -n "$want" ] || exit 1
xz -d $I.xz && [ "$(sha256 -q $I)" = "$want" ] || { echo "setup: image does not match"; exit 1; }
(set -C; : > /var/db/hb-usb.img) || exit 1
yes HB | head -c 1073741824 > /var/db/hb-usb.img || exit 1
[ "$(stat -f %z /var/db/hb-usb.img)" = 1073741824 ] || exit 1
mdconfig -a -t vnode -f /var/db/hb-usb.img -u 7 || exit 1
(set -C; echo "$want" > /var/db/hb-usb.sum) || exit 1
