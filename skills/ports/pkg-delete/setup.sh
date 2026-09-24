#!/bin/sh
# Preconditions for ports/pkg-delete: pkg is installed, and the test package
# (nginx-lite, deliberately not the package in the skill's examples) is installed.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y nginx-lite >/dev/null || exit 1
pkg info -e nginx-lite
