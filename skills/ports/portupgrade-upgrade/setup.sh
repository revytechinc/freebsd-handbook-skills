#!/bin/sh
# Preconditions for ports/portupgrade-upgrade: pkg and git installed; the ports tree
# in /usr/ports on the branch matching pkg (as ports/ports-tree-git does it);
# portupgrade installed; one installed port (sysutils/tree) older than the
# ports tree; the package list saved for verify.sh.
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y git >/dev/null || exit 1
case "$(pkg -vv | grep -m1 url)" in
    *'/latest",'*) b= ;;
    *) b=$(git ls-remote --heads https://git.FreeBSD.org/ports.git '20*Q*' </dev/null | tail -1 | sed 's#.*refs/heads/##')
       case "$b" in 20[0-9][0-9]Q[1-4]) ;; *) exit 1 ;; esac   # a branch name, nothing else
       b="-b $b" ;;
esac
git clone --quiet --depth 1 $b https://git.FreeBSD.org/ports.git /usr/ports </dev/null || exit 1
# portupgrade and tree from packages; then the ports tree is made to offer a
# newer tree (a local PORTREVISION bump) so there is exactly one upgrade to do.
env IGNORE_OSVERSION=yes pkg install -y portupgrade tree >/dev/null || exit 1
M=/usr/ports/sysutils/tree/Makefile
grep -q '^DISTVERSION=' $M && ! grep -q '^PORTREVISION' $M || exit 1
sed -i '' '/^DISTVERSION=/a\
PORTREVISION=	99
' $M || exit 1
[ "$(make -C /usr/ports/sysutils/tree -V PKGVERSION)" = "$(pkg query %v tree)_99" ] || exit 1
out=$(pkg query '%n %v') && [ -n "$out" ] && out=$(printf '%s\n' "$out" | LC_ALL=C sort) && (set -C; printf '%s\n' "$out" > /var/db/hb-portupgrade-before.txt)
