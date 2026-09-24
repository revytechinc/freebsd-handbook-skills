#!/bin/sh
# Independent check for ports/pkg-add-offline (test input PACKAGE=nginx-lite):
# nginx-lite and its dependency pcre2 are installed, and nginx runs.
# Exit 0 when verified, 1 otherwise.
# The test runs with the network cut off by setup.sh; make sure it stayed off
# (IPv4 and IPv6 default routes, and a real request to the repository).
for fam in -4 -6; do
    if route -n get $fam default 2>/dev/null | grep -q 'gateway:'; then
        echo "FAIL: a default route ($fam) came back during the run; the test was not offline"; exit 1
    fi
done
if fetch -q -T 10 -o /dev/null https://pkg.FreeBSD.org/ 2>/dev/null; then
    echo "FAIL: the repository was reachable at the end; the test was not offline"; exit 1
fi
pkg info -e nginx-lite || { echo "FAIL: nginx-lite not installed"; exit 1; }
pkg info -e pcre2 || { echo "FAIL: dependency pcre2 not installed"; exit 1; }
v=$(/usr/local/sbin/nginx -v 2>&1)
case "$v" in
    "nginx version: nginx/"*) echo "OK: $v"; exit 0 ;;
    *) echo "FAIL: nginx -v printed '$v'"; exit 1 ;;
esac
