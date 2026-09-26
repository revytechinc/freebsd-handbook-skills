#!/bin/sh
# Independent check for introduction/docs-install: en-freebsd-doc is
# installed from FreeBSD's repository, and the Handbook and FAQ are readable
# on disk in both forms the skill names (PDF and HTML), with plausible sizes.
# Exit 0 / 1.
pkg -N >/dev/null 2>&1 || { echo "FAIL: pkg does not work"; exit 1; }
r=$(pkg query '%R' en-freebsd-doc) || { echo "FAIL: en-freebsd-doc is not installed"; exit 1; }
case "$r" in FreeBSD|FreeBSD-ports) ;; *) echo "FAIL: en-freebsd-doc came from '$r'"; exit 1 ;; esac
d=/usr/local/share/doc/freebsd/en/books
for f in handbook/handbook_en.pdf faq/faq_en.pdf; do
    [ "$(stat -f %z $d/$f 2>/dev/null || echo 0)" -gt 100000 ] || { echo "FAIL: $d/$f missing or too small"; exit 1; }
done
for f in handbook/index.html faq/index.html; do
    grep -qi '<html' $d/$f 2>/dev/null || { echo "FAIL: $d/$f is not an HTML page"; exit 1; }
done
echo "OK: local FreeBSD documentation installed"; exit 0
