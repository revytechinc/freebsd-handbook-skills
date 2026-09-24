#!/bin/sh
# Preconditions for ports/port-options: pkg and git installed; the ports tree
# in /usr/ports on the branch matching pkg (as ports/ports-tree-git does it);
# no saved options for shells/bash (the test port); an /etc/make.conf holding
# one comment line with no line break at its end, so a careless append would
# join onto it.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y git >/dev/null || exit 1
case "$(pkg -vv | grep -m1 url)" in
    *'/latest",'*) b= ;;
    *) b=$(git ls-remote --heads https://git.FreeBSD.org/ports.git '20*Q*' </dev/null | tail -1 | sed 's#.*refs/heads/##')
       case "$b" in 20[0-9][0-9]Q[1-4]) ;; *) exit 1 ;; esac   # a branch name, nothing else
       b="-b $b" ;;
esac
git clone --quiet --depth 1 $b https://git.FreeBSD.org/ports.git /usr/ports </dev/null || exit 1
[ ! -e /etc/make.conf ] && [ ! -e /var/db/ports/shells_bash/options ] || exit 1
(set -C; printf '# local settings' > /etc/make.conf) || exit 1   # never overwrite
# The test only means something if SYSLOG starts out off.
make -C /usr/ports/shells/bash showconfig | grep -qx '     SYSLOG=off: Syslog logging support'
