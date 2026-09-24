#!/bin/sh
# Preconditions for ports/pkg-clean-all: curl installed, so the cache holds
# its package file and those of its dependencies.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y curl >/dev/null || exit 1
ls /var/cache/pkg/*.pkg >/dev/null 2>&1
