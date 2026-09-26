#!/bin/sh
# Independent check for ports/poudriere-jail (test input JAIL=testjail): the
# configuration names the download server and ZFS or not, matching this
# machine; the jail testjail exists with this machine's release and amd64;
# its base system is really there; and on an end-of-life release the jail's
# make.conf allows building.
# Exit 0 / 1.
C=/usr/local/etc/poudriere.conf
[ "$(sysrc -f $C -n FREEBSD_HOST)" = "https://download.FreeBSD.org" ] || { echo "FAIL: FREEBSD_HOST not set"; exit 1; }
if r=$(zfs list -H -o name / 2>/dev/null); then
    [ "$(sysrc -f $C -n ZPOOL)" = "${r%%/*}" ] || { echo "FAIL: ZPOOL is not ${r%%/*}"; exit 1; }
    [ -z "$(sysrc -f $C -qn NO_ZFS)" ] || { echo "FAIL: NO_ZFS set on a ZFS machine"; exit 1; }
else
    [ "$(sysrc -f $C -n NO_ZFS)" = "yes" ] || { echo "FAIL: NO_ZFS is not yes on a UFS machine"; exit 1; }
    [ -z "$(sysrc -f $C -qn ZPOOL)" ] || { echo "FAIL: ZPOOL set on a UFS machine"; exit 1; }
fi
v=$(freebsd-version -u | sed 's/-p[0-9]*$//')
out=$(poudriere jail -l) || { echo "FAIL: poudriere jail -l failed"; exit 1; }
l=$(printf '%s\n' "$out" | awk '$1=="testjail"{print $2, $3}')
case "$l" in "$v amd64"|"$v"-p[0-9]*" amd64") ;; *) echo "FAIL: jail testjail is '$l', want $v amd64"; exit 1 ;; esac
j=/usr/local/poudriere/jails/testjail
[ -x "$j/bin/sh" ] && [ -f "$j/usr/include/stdio.h" ] || { echo "FAIL: the jail's base system is missing"; exit 1; }
uv=$(sed -n 's/^USERLAND_VERSION="\(.*\)"$/\1/p' "$j/bin/freebsd-version" | sed 's/-p[0-9]*$//')   # read, never run, the jail's file
[ "$uv" = "$v" ] || { echo "FAIL: the jail's base is '$uv', not $v"; exit 1; }
case "$v" in
14.[0-3]-*) grep -qx 'ALLOW_UNSUPPORTED_SYSTEM=yes' /usr/local/etc/poudriere.d/testjail-make.conf || { echo "FAIL: EoL jail without ALLOW_UNSUPPORTED_SYSTEM"; exit 1; } ;;
*) [ ! -e /usr/local/etc/poudriere.d/testjail-make.conf ] || { echo "FAIL: make.conf written on a supported release"; exit 1; } ;;
esac
echo "OK: poudriere configured and jail testjail ($l) created"; exit 0
