#!/bin/sh
# Independent check for ports/pkg-search: the repository catalogue has been
# downloaded (it is absent on a freshly bootstrapped machine). -U: do not
# download it here. Exit 0 when verified, 1 otherwise.
v=$(env IGNORE_OSVERSION=yes pkg rquery -U '%v' curl 2>/dev/null)
[ -n "$v" ] && { echo "OK: catalogue present, curl $v"; exit 0; }
echo "FAIL: no catalogue downloaded"; exit 1
