#!/bin/sh
# Preconditions for ports/pkg-post-install (test input PACKAGE=rsync): pkg
# installed, and rsync installed from packages (it ships an install message,
# a .sample configuration file and an rc.d script).
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y rsync >/dev/null || exit 1
pkg info -e rsync
