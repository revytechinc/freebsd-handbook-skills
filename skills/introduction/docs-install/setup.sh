#!/bin/sh
# Preconditions for introduction/docs-install: pkg installed; the English
# documentation not installed.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
pkg info -e en-freebsd-doc; [ $? -eq 1 ] && [ ! -e /usr/local/share/doc/freebsd/en/books/handbook ]
