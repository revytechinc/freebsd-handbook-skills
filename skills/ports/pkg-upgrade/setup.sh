#!/bin/sh
# Preconditions for ports/pkg-upgrade: pkg is installed, and there is a real
# upgrade waiting. nginx-lite is installed from the default (Quarterly)
# branch, then the machine is switched to Latest exactly as the skill
# ports/pkg-branch-latest does it (a separate latest.conf). Latest has a newer
# nginx-lite and pcre2 than Quarterly; on 15.x and 16.0 base-system updates
# are waiting too. (16.0-CURRENT is already on Latest; its snapshots move on.)
pkg -N >/dev/null 2>&1 || env ASSUME_ALWAYS_YES=yes pkg bootstrap >/dev/null || exit 1
env IGNORE_OSVERSION=yes pkg install -y nginx-lite >/dev/null || exit 1
case "$(freebsd-version -u)" in
    14.*) R=FreeBSD ;;
    15.*) R=FreeBSD-ports ;;
    *)    R= ;;
esac
if [ -n "$R" ]; then
    mkdir -p /usr/local/etc/pkg/repos
    echo "$R: { url: \"pkg+https://pkg.FreeBSD.org/\${ABI}/latest\" }" > /usr/local/etc/pkg/repos/latest.conf || exit 1
fi
env IGNORE_OSVERSION=yes pkg update -f >/dev/null || exit 1
# The test is only meaningful if an upgrade is really waiting (on 16.0-CURRENT
# that depends on a newer snapshot having been published).
plan=$(env IGNORE_OSVERSION=yes pkg upgrade -n 2>&1); rc=$?
if [ $rc -ne 0 ]; then echo "setup: could not ask pkg for the upgrade plan (exit $rc)"; exit 1; fi
if ! echo "$plan" | grep -qE 'to be UPGRADED|New version of pkg detected'; then
    echo "setup: nothing to upgrade on this machine; the test would prove nothing"; exit 1
fi
# Record whether the kernel itself is waiting (pkgbase releases), so
# verify.sh can require that it was really upgraded.
if env IGNORE_OSVERSION=yes pkg version -R -l '<' 2>/dev/null | grep -q '^FreeBSD-kernel'; then
    echo yes > /var/db/hbskills-pkg-upgrade.kernel
else
    echo no > /var/db/hbskills-pkg-upgrade.kernel
fi
# Test stamp: verify.sh requires a package installed after this moment, so
# "up to date" can only pass if something really was upgraded.
sleep 1; date +%s > /var/db/hbskills-pkg-upgrade.stamp
