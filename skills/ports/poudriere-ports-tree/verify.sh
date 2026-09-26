#!/bin/sh
# Independent check for ports/poudriere-ports-tree (test input TREE=testtree):
# poudriere lists testtree as a git+https tree; it is on the branch matching
# this machine's packages (the newest quarterly branch for quarterly, main for
# latest, the same rule the skill uses, applied here separately); and it is a
# real ports tree.
# Exit 0 / 1.
out=$(poudriere ports -l) || { echo "FAIL: poudriere ports -l failed"; exit 1; }
m=$(printf '%s\n' "$out" | awk '$1=="testtree"{print $2}')
[ "$m" = "git+https" ] || { echo "FAIL: testtree is not listed as git+https ('$m')"; exit 1; }
t=/usr/local/poudriere/ports/testtree
[ -f "$t/Mk/bsd.port.mk" ] && [ -f "$t/misc/figlet/Makefile" ] || { echo "FAIL: $t is not a ports tree"; exit 1; }
u=$(pkg -vv | grep -e '/quarterly"' -e '/latest"') || { echo "FAIL: cannot read pkg's repository"; exit 1; }
[ "$(printf '%s\n' "$u" | wc -l | tr -d ' ')" = 1 ] || { echo "FAIL: more than one repository url: $u"; exit 1; }
case "$u" in
*'/latest",') want=main ;;
*'/quarterly",') want=$(git ls-remote --heads https://git.FreeBSD.org/ports.git '20*Q*' </dev/null | tail -1 | sed 's#.*refs/heads/##') ;;
*) echo "FAIL: unexpected repository url: $u"; exit 1 ;;
esac
case "$want" in main|20[0-9][0-9]Q[1-4]) ;; *) echo "FAIL: could not work out the branch ('$want')"; exit 1 ;; esac
b=$(git -C "$t" rev-parse --abbrev-ref HEAD) || { echo "FAIL: git cannot read $t"; exit 1; }
[ "$b" = "$want" ] || { echo "FAIL: testtree is on '$b', want '$want'"; exit 1; }
echo "OK: ports tree testtree on $b"; exit 0
