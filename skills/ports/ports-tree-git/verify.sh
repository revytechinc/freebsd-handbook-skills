#!/bin/sh
# Independent check for ports/ports-tree-git: /usr/ports is a git checkout of
# the branch matching pkg's (newest quarterly, or main for latest), and holds
# the ports tree. Exit 0 / 1.
[ -d /usr/ports/.git ] || { echo "FAIL: /usr/ports is not a git checkout"; exit 1; }
[ -f /usr/ports/sysutils/lsof/Makefile ] || { echo "FAIL: the tree is incomplete"; exit 1; }
b=$(git -C /usr/ports branch --show-current 2>/dev/null) || { echo "FAIL: git cannot read /usr/ports"; exit 1; }
case "$(pkg -vv 2>/dev/null | grep -m1 url)" in
    *'/latest",'*) want=main ;;
    *'/quarterly",'*) want=$(git ls-remote --heads https://git.FreeBSD.org/ports.git '20*Q*' </dev/null | tail -1 | sed 's#.*refs/heads/##') ;;
    *) echo "FAIL: cannot tell pkg's branch"; exit 1 ;;
esac
[ -n "$want" ] && [ "$b" = "$want" ] || { echo "FAIL: branch $b, expected $want"; exit 1; }
echo "OK: /usr/ports on $b"; exit 0
