#!/bin/sh
# Independent check for ports/pkg-delete (test input PACKAGE=nginx-lite):
# nginx-lite is gone, and nothing more was removed than asked (its dependency
# pcre2, which setup.sh installed with it, is still there). Exit 0 / 1.
pkg info -e nginx-lite && { echo "FAIL: nginx-lite is still installed"; exit 1; }
[ -e /usr/local/sbin/nginx ] && { echo "FAIL: /usr/local/sbin/nginx is still there"; exit 1; }
pkg info -e pcre2 || { echo "FAIL: pcre2 was removed too; only nginx-lite was asked for"; exit 1; }
echo "OK: nginx-lite removed, pcre2 kept"; exit 0
