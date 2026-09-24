#!/bin/sh
# Preconditions for ports/ports-outdated: pkg and git installed from the
# default (Quarterly, on 14.x/15.x) packages, and a `main` ports tree, so
# some installed versions really are older than their ports.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y git nginx-lite >/dev/null || exit 1
git clone --quiet --depth 1 https://git.FreeBSD.org/ports.git /usr/ports </dev/null || exit 1
rm -f /root/outdated.txt
# TEST ONLY: where packages and ports tree are the same (16.0-CURRENT, both
# on main), nothing is older, and the answer would be the fixed text shown in
# the skill. Then raise nginx-lite's PORTREVISION in the local tree, so one
# installed package really is older than its port.
if [ -z "$(pkg version -l '<' 2>/dev/null)" ]; then
    sed -i '' 's/^PORTNAME=\tnginx$/PORTNAME=\tnginx\nPORTREVISION=\t99/' /usr/ports/www/nginx-lite/Makefile
    [ -n "$(pkg version -l '<' 2>/dev/null)" ] || exit 1
fi
