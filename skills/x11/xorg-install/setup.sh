#!/bin/sh
# Precondition for x11/xorg-install: pkg is installed (ports/pkg-bootstrap)
# and the test user exists.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
id hbx >/dev/null 2>&1 || pw useradd hbx -m -s /bin/sh || exit 1
pkg -N >/dev/null 2>&1 && id hbx >/dev/null 2>&1
