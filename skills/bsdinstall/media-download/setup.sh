#!/bin/sh
# Preconditions for bsdinstall/media-download (test input VERSION=14.3,
# TYPE=bootonly): no download folder yet, and enough free space in /var/tmp.
[ -e /var/tmp/freebsd-media ] || [ -L /var/tmp/freebsd-media ] && { echo "setup: /var/tmp/freebsd-media exists"; exit 1; }
free=$(df -k /var/tmp | awk 'NR == 2 { print $4 }') || exit 1
[ -n "$free" ] && [ "$free" -gt 2000000 ] || { echo "setup: less than 2 GB free in /var/tmp"; exit 1; }
exit 0
