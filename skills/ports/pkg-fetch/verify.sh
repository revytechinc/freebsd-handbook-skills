#!/bin/sh
# Independent check for ports/pkg-fetch (test inputs PACKAGE=nginx-lite,
# DIR=/root/packages): the package file and its dependency (pcre2) were
# downloaded, and nothing was installed. Exit 0 when verified, 1 otherwise.
d=/root/packages/All/Hashed
ls "$d"/nginx-lite-[0-9]*.pkg >/dev/null 2>&1 || { echo "FAIL: no nginx-lite file in $d"; exit 1; }
ls "$d"/pcre2-[0-9]*.pkg >/dev/null 2>&1 || { echo "FAIL: dependency pcre2 not downloaded to $d"; exit 1; }
pkg info -e nginx-lite && { echo "FAIL: nginx-lite was installed, not only downloaded"; exit 1; }
pkg info -e pcre2 && { echo "FAIL: pcre2 was installed, not only downloaded"; exit 1; }
echo "OK: $(ls "$d" | tr '\n' ' ')"; exit 0
