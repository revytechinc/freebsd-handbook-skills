#!/bin/sh
# Independent check for ports/pkg-clean-all: no package file is left in the
# cache, and installed software (curl) still works. Exit 0 / 1.
n=$(find /var/cache/pkg -name '*.pkg' 2>/dev/null | wc -l | tr -d ' ')
[ "$n" = 0 ] || { echo "FAIL: $n package files still cached"; exit 1; }
pkg info -e curl && /usr/local/bin/curl --version >/dev/null 2>&1 || { echo "FAIL: curl is gone or broken"; exit 1; }
echo "OK: cache empty, curl works"; exit 0
