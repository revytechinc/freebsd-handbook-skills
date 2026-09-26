#!/bin/sh
# Independent check for ports/poudriere-repo (test input JAIL=testjail,
# TREE=testtree, PACKAGE=tree): pkg's merged view of the repository
# "poudriere" has the local file:// URL and says it is enabled; pkg itself
# was not replaced by the local build; tree is installed and pkg
# records it as coming from that repository, with the version that repository
# holds; the file's contents are exactly what the skill writes.
# Exit 0 / 1.
f=/usr/local/etc/pkg/repos/poudriere.conf
want=$(printf '%s\n' 'poudriere: {' '    url: "file:///usr/local/poudriere/data/packages/testjail-testtree",' '    enabled: yes' '}')
[ "$(cat $f 2>/dev/null)" = "$want" ] || { echo "FAIL: $f is not as the skill writes it"; exit 1; }
c=$(pkg -vv) || { echo "FAIL: pkg -vv failed"; exit 1; }
printf '%s\n' "$c" | grep -A3 '^  poudriere: {' | grep -q 'url *: "file:///usr/local/poudriere/data/packages/testjail-testtree"' || { echo "FAIL: pkg does not see the poudriere repository"; exit 1; }
printf '%s\n' "$c" | grep -A6 '^  poudriere: {' | grep -q 'enabled *: yes' || { echo "FAIL: pkg does not see the poudriere repository as enabled"; exit 1; }
[ "$(pkg query %R pkg)" != "poudriere" ] || { echo "FAIL: pkg itself was replaced from the poudriere repository"; exit 1; }
q=$(pkg query '%v %R' tree) || { echo "FAIL: tree is not installed"; exit 1; }
rv=$(pkg rquery -r poudriere '%v' tree) || { echo "FAIL: tree not in the poudriere repository"; exit 1; }
[ "$q" = "$rv poudriere" ] || { echo "FAIL: tree is '$q', want '$rv poudriere'"; exit 1; }
/usr/local/bin/tree --version >/dev/null 2>&1 || { echo "FAIL: tree does not run"; exit 1; }
echo "OK: tree $q installed from the local poudriere repository"; exit 0
