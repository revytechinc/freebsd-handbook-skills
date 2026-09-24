#!/bin/sh
# Independent check for ports/pkg-kmods-repo: on 14.0/14.1 nothing was added
# (no repository exists); on every other release pkg sees kernel-module
# packages in the release's module repository. Exit 0 / 1.
case "$(freebsd-version -u)" in
    14.[01]-*) [ ! -e /usr/local/etc/pkg/repos/kmods.conf ] || { echo "FAIL: kmods.conf created where no repository exists"; exit 1; }
               echo "OK: nothing to add on this release"; exit 0 ;;
    14.*) r=FreeBSD-kmods ;;
    *)    r=FreeBSD-ports-kmods ;;
esac
n=$(env IGNORE_OSVERSION=yes pkg rquery -U -r "$r" %n 2>/dev/null | wc -l | tr -d ' ')
[ "${n:-0}" -gt 0 ] || { echo "FAIL: no kernel-module packages visible in $r"; exit 1; }
echo "OK: $r offers $n modules"; exit 0
