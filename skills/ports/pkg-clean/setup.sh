#!/bin/sh
# Preconditions for ports/pkg-clean: curl installed (so its current package
# file is in the cache), plus one stale file: a copy of it under a version the
# repository does not offer, which is how an outdated version looks to pkg.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y curl >/dev/null || exit 1
f=$(ls /var/cache/pkg/curl-[0-9]*~*.pkg | head -1) && [ -f "$f" ] || exit 1
cp "$f" /var/cache/pkg/curl-0.0.1~0000000000.pkg
