#!/bin/sh
# Independent check for bsdinstall/media-download (test input VERSION=14.3,
# TYPE=bootonly): /var/tmp/freebsd-media holds the image, compressed and not,
# and their SHA256 checksums equal the ones in a checksum file this script
# downloads itself from the FreeBSD archive.
# Exit 0 / 1.
D=/var/tmp/freebsd-media
N=FreeBSD-14.3-RELEASE-amd64-bootonly.iso
C=CHECKSUM.SHA256-FreeBSD-14.3-RELEASE-amd64
t=$(mktemp /tmp/hbsum.XXXXXX) || { echo "FAIL: mktemp"; exit 1; }
env -i PATH=/usr/bin:/bin fetch -q -o "$t" "https://archive.freebsd.org/old-releases/amd64/amd64/ISO-IMAGES/14.3/$C" || { rm -f "$t"; echo "FAIL: cannot fetch the checksum file"; exit 1; }
for f in $N $N.xz; do
    [ -f "$D/$f" ] && [ ! -L "$D/$f" ] || { rm -f "$t"; echo "FAIL: no $D/$f"; exit 1; }
    want=$(awk -v f="($f)" '$1 == "SHA256" && $2 == f && $3 == "=" { print $4 }' "$t")
    [ -n "$want" ] || { rm -f "$t"; echo "FAIL: $f not in the checksum file"; exit 1; }
    [ "$(sha256 -q "$D/$f")" = "$want" ] || { rm -f "$t"; echo "FAIL: $f does not match"; exit 1; }
done
rm -f "$t"
echo "OK: $N and $N.xz match"; exit 0
