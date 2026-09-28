#!/bin/sh
# Independent check for bsdinstall/media-write-usb (test input: the 15.1
# mini-memstick image onto md7): md7 is still the memory disk setup made
# (backed by /var/db/hb-usb.img, still 1 GB); the first bytes read from md7, as
# many as the image has, have the image's published SHA256 checksum
# (recorded by setup); md7 is not in use; the image file is unchanged.
# Exit 0 / 1.
read -r want < /var/db/hb-usb.sum && [ -n "$want" ] || { echo "FAIL: no values recorded by setup"; exit 1; }
I=/var/tmp/freebsd-media/FreeBSD-15.1-RELEASE-amd64-mini-memstick.img
B=/var/db/hb-usb.img
[ "$(sha256 -q $I)" = "$want" ] || { echo "FAIL: the image file changed"; exit 1; }
f=$(mdconfig -lv -u 7 | awk '{ print $4 }'); [ -n "$f" ] || { echo "FAIL: no md7"; exit 1; }
[ "$f" = "$B" ] || { echo "FAIL: md7 is backed by '$f', not $B"; exit 1; }
sz=$(stat -f %z $I) && [ "$sz" -gt 0 ] || { echo "FAIL: cannot size the image"; exit 1; }
head -c 512 /dev/md7 > /dev/null || { echo "FAIL: cannot read md7"; exit 1; }
[ "$(stat -f %z $B)" = 1073741824 ] || { echo "FAIL: $B is no longer 1 GB"; exit 1; }
got=$(head -c "$sz" /dev/md7 | sha256)
[ "$got" = "$want" ] || { echo "FAIL: md7 does not hold the image"; exit 1; }
m=$(geom -p md7 | awk '$1 == "Mode:" { print $2 }'); [ "$m" = r0w0e0 ] || { echo "FAIL: md7 mode is '$m' (in use, or geom failed)"; exit 1; }
echo "OK: md7 holds the image"; exit 0
