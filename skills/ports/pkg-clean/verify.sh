#!/bin/sh
# Independent check for ports/pkg-clean: the stale file is gone, the current
# curl package file is still cached (so not everything was deleted), and curl
# still works. Exit 0 / 1.
[ -e /var/cache/pkg/curl-0.0.1~0000000000.pkg ] && { echo "FAIL: the stale file is still there"; exit 1; }
ls /var/cache/pkg/curl-[0-9]*~*.pkg >/dev/null 2>&1 || { echo "FAIL: the current curl file was deleted too"; exit 1; }
/usr/local/bin/curl --version >/dev/null 2>&1 || { echo "FAIL: curl no longer runs"; exit 1; }
echo "OK: stale file removed, current files kept"; exit 0
