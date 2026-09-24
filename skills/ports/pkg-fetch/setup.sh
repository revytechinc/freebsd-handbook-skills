#!/bin/sh
# Precondition for ports/pkg-fetch: pkg is installed (ports/pkg-bootstrap).
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
pkg -N >/dev/null 2>&1
