#!/bin/sh
# Independent check for ports/pkg-install (test input PACKAGE=curl): the curl
# package is registered as installed, and the program runs.
# Exit 0 when verified, 1 otherwise.
pkg info -e curl || { echo "FAIL: pkg does not list curl as installed"; exit 1; }
v=$(/usr/local/bin/curl --version 2>/dev/null | head -1)
case "$v" in
    "curl "[0-9]*) echo "OK: $v"; exit 0 ;;
    *) echo "FAIL: /usr/local/bin/curl --version printed '$v'"; exit 1 ;;
esac
