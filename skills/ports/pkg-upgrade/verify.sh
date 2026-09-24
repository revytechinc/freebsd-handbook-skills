#!/bin/sh
# Independent check for ports/pkg-upgrade: nothing is left to upgrade; if the
# kernel was upgraded, the machine has been restarted since; and on a ZFS root
# the boot environment before-pkg-upgrade exists. Exit 0 when verified, 1 otherwise.
# -U: judge the catalogue the model worked with, not one refreshed now.
out=$(env IGNORE_OSVERSION=yes pkg upgrade -n -U 2>&1)
echo "$out" | grep -q 'Your packages are up to date.' || { echo "FAIL: upgrades still pending:"; echo "$out" | tail -5; exit 1; }
stamp=$(cat /var/db/hbskills-pkg-upgrade.stamp 2>/dev/null)
newest=$(pkg query %t 2>/dev/null | sort -n | tail -1)
case "$stamp" in ''|*[!0-9]*) echo "FAIL: no test stamp from setup.sh"; exit 1 ;; esac
case "$newest" in ''|*[!0-9]*) echo "FAIL: cannot read the package install times"; exit 1 ;; esac
[ "$newest" -gt "$stamp" ] || { echo "FAIL: no package was installed or upgraded after setup"; exit 1; }
k=$(pkg query -g %t 'FreeBSD-kernel*' 2>/dev/null | sort -n | tail -1)
b=$(sysctl -n kern.boottime | sed 's/^{ sec = \([0-9]*\),.*/\1/')
case "$b" in ''|*[!0-9]*) echo "FAIL: cannot read the boot time"; exit 1 ;; esac
case "$(freebsd-version -u)" in
    14.*) ;;
    *) [ -n "$k" ] || { echo "FAIL: no FreeBSD-kernel package found on a pkgbase release"; exit 1; } ;;
esac
case "$k" in ''|*[!0-9]*) [ -z "$k" ] || { echo "FAIL: cannot read the kernel install time ($k)"; exit 1; } ;; esac
case "$(freebsd-version -u)" in
    14.*) ;;
    *) pkg -vv 2>/dev/null | awk 'index($0, "  FreeBSD-base:")==1 {s=1; next} /^  [A-Za-z-]+:/ {s=0} s && $1=="enabled" {print $3; exit}' | grep -qx 'yes,' \
           || { echo "FAIL: FreeBSD-base is missing or no longer enabled"; exit 1; } ;;
esac
if [ "$(cat /var/db/hbskills-pkg-upgrade.kernel 2>/dev/null)" = yes ]; then
    [ -n "$k" ] && [ "$k" -gt "$stamp" ] || { echo "FAIL: a kernel upgrade was waiting but the kernel packages were not upgraded"; exit 1; }
fi
note=""
if [ -n "$k" ]; then
    [ "$k" -gt "$b" ] && { echo "FAIL: the kernel was upgraded but the machine was not restarted"; exit 1; }
    note=", kernel packages installed before the last start"
fi
if [ "$(df -T / | awk 'NR==2{print $2}')" = zfs ]; then
    bectl list -H | awk '{print $1}' | grep -qx before-pkg-upgrade || { echo "FAIL: no boot environment before-pkg-upgrade"; exit 1; }
    # The snapshot must be older than the upgrade. setup.sh guarantees that
    # something was waiting, so the newest package install time is the upgrade.
    # Boot environments live next to the root dataset (e.g. zroot/ROOT/default).
    root=$(zfs list -H -o name / 2>/dev/null)
    be=$(zfs get -Hp -o value creation "${root%/*}/before-pkg-upgrade" 2>/dev/null)
    up=$(pkg query %t 2>/dev/null | sort -n | tail -1)
    case "$be" in ''|*[!0-9]*) echo "FAIL: cannot read the creation time of ${root%/*}/before-pkg-upgrade"; exit 1 ;; esac
    case "$up" in ''|*[!0-9]*) echo "FAIL: cannot read the package install times"; exit 1 ;; esac
    [ "$be" -le "$up" ] || { echo "FAIL: boot environment created after the upgrade ($be > $up)"; exit 1; }
fi
echo "OK: up to date$note"; exit 0
