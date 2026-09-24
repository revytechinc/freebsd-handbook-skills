#!/bin/sh
# Preconditions for ports/port-deinstall: pkg and git installed; the ports
# tree on the branch matching pkg; sysutils/tree (the test port) built and
# installed from it; the package list saved so verify.sh can see that nothing
# else was removed.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y git >/dev/null || exit 1
case "$(pkg -vv | grep -m1 url)" in
    *'/latest",'*) b= ;;
    *) b=$(git ls-remote --heads https://git.FreeBSD.org/ports.git '20*Q*' </dev/null | tail -1 | sed 's#.*refs/heads/##')
       case "$b" in 20[0-9][0-9]Q[1-4]) ;; *) exit 1 ;; esac   # a branch name, nothing else
       b="-b $b" ;;
esac
git clone --quiet --depth 1 $b https://git.FreeBSD.org/ports.git /usr/ports </dev/null || exit 1
make -C /usr/ports/sysutils/tree BATCH=yes ALLOW_UNSUPPORTED_SYSTEM=yes install clean </dev/null >/root/setup-build.log 2>&1 || exit 1
pkg info -e tree || exit 1
list=$(pkg query '%n') || exit 1
printf '%s\n' "$list" | LC_ALL=C sort > /var/db/hbskills-deinstall-before || exit 1
