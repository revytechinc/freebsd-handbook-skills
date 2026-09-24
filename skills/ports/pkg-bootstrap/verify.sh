#!/bin/sh
# Independent check for ports/pkg-bootstrap: pkg is installed and reports a
# 2.x.y version. Exit 0 when verified, 1 otherwise.
pkg -N >/dev/null 2>&1 || { echo "FAIL: pkg -N says pkg is not installed"; exit 1; }
v=$(pkg -v 2>/dev/null)
case "$v" in
    2.[0-9]*.[0-9]*) echo "OK: pkg $v installed"; exit 0 ;;
    *) echo "FAIL: pkg -v printed '$v'"; exit 1 ;;
esac
