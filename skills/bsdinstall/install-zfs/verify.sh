# Independent check for bsdinstall/install-zfs, typed into /bin/sh on the
# installed system's console by the harness (logged in as root with ROOTPW):
# the test inputs HOSTNAME=hbzfs, IPADDR=10.77.0.99, USERNAME=hbadmin,
# USERPW (checked against the stored hash; root's is proven by the login).
# No tilde character may appear in this file (the console connection
# reserves it).
fail() { echo "FAIL: $1"; exit 1; }
[ "$(freebsd-version -u | cut -d- -f1-2)" = 15.1-RELEASE ] || fail "release $(freebsd-version -u)"
[ "$(hostname)" = hbzfs ] || fail "hostname $(hostname)"
[ "$(sysrc -n hostname)" = hbzfs ] || fail "rc.conf hostname $(sysrc -n hostname)"
# Root is the pool's boot environment, and the pool is on the target disk.
[ "$(mount -p | awk '$2 == "/" { print $1 " " $3 }')" = "zroot/ROOT/default zfs" ] || fail "root is not zroot/ROOT/default on ZFS"
[ "$(zpool list -H -o health zroot)" = ONLINE ] || fail "pool zroot is not ONLINE"
zpool status zroot | grep -q ' vtbd0p[0-9][0-9]* *ONLINE' || fail "zroot is not on vtbd0"
# One disk, no redundancy: exactly one device in the pool, no mirror/raidz.
[ "$(zpool list -H -v zroot | awk 'NR > 1 { n++ } END { print n + 0 }')" = 1 ] || fail "zroot does not have exactly one device"
zpool status zroot | grep -qE '^[[:space:]]+(mirror|raidz)' && fail "zroot has a mirror or raidz"
gpart show vtbd0 | grep -q ' GPT ' || fail "vtbd0 is not GPT"
gpart show vtbd0 | grep -q freebsd-swap || fail "no swap partition"
[ "$(sysrc -n zfs_enable)" = YES ] || fail "zfs_enable is not YES"
[ "$(sysrc -n ifconfig_vtnet0)" = "inet 10.77.0.99 netmask 255.255.255.0" ] || fail "ifconfig_vtnet0 is '$(sysrc -n ifconfig_vtnet0)'"
[ "$(sysrc -n defaultrouter)" = 10.77.0.1 ] || fail "defaultrouter $(sysrc -n defaultrouter)"
grep -q '^nameserver 10.77.0.1$' /etc/resolv.conf || fail "resolv.conf"
[ "$(sysrc -n sshd_enable)" = YES ] || fail "sshd not enabled"
[ "$(sysrc -n dumpdev)" = AUTO ] || fail "dumpdev is not AUTO"
# What the time zone step wrote (date +%Z also says UTC when none was set).
[ "$(cat /var/db/zoneinfo 2>/dev/null)" = UTC ] || fail "time zone not set to UTC"
# The two default extra components (downloaded during the installation).
[ -f /usr/lib/debug/boot/kernel/kernel.debug ] || fail "kernel-dbg not installed"
[ -f /usr/lib32/libc.so.7 ] || fail "lib32 not installed"
id -Gn hbadmin | tr ' ' '\n' | grep -qx wheel || fail "hbadmin missing or not in wheel"
[ "$(pw usershow hbadmin | cut -d: -f8)" = "HB Admin" ] || fail "full name"
h=$(pw usershow hbadmin | cut -d: -f2)
case "$h" in '$6$'*) ;; *) fail "hbadmin has no password hash" ;; esac
salt=$(echo "$h" | cut -d'$' -f3)
[ "$(openssl passwd -6 -salt "$salt" hbLab-5537)" = "$h" ] || fail "hbadmin's password is not USERPW"
case "$(pw usershow root | cut -d: -f2)" in '$6$'*) ;; *) fail "root has no password hash" ;; esac
echo "OK: hbzfs installed on ZFS with hbadmin"
