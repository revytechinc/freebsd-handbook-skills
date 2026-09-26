#!/bin/sh
# Independent check for ports/poudriere-bulk (test input JAIL=testjail,
# TREE=testtree, PORTS=sysutils/tree devel/gmake): the list holds exactly the
# two ports; the repository has its catalogue; and among its packages, read
# with pkg itself, are ones built from sysutils/tree and devel/gmake, and pkg.
# Exit 0 / 1.
L=/usr/local/etc/poudriere.d/testjail-testtree-pkglist
[ "$(cat $L 2>/dev/null)" = "$(printf 'sysutils/tree\ndevel/gmake')" ] || { echo "FAIL: $L is not the two ports"; exit 1; }
R=/usr/local/poudriere/data/packages/testjail-testtree
[ -f $R/packagesite.pkg ] || [ -f $R/packagesite.tzst ] || { echo "FAIL: no repository catalogue in $R"; exit 1; }
o=$(for f in $R/All/*.pkg; do pkg query -F "$f" '%o' || exit 1; done) || { echo "FAIL: cannot read the packages in $R/All"; exit 1; }
for want in sysutils/tree devel/gmake ports-mgmt/pkg; do
    printf '%s\n' "$o" | grep -qx "$want" || { echo "FAIL: no package built from $want"; exit 1; }
done
echo "OK: repository with packages for sysutils/tree, devel/gmake and pkg"; exit 0
