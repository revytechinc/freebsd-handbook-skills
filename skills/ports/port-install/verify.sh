#!/bin/sh
# Independent check for ports/port-install (test input PORT=sysutils/tree):
# tree is installed, recorded with origin sysutils/tree, not from a repository
# (pkg records locally built or added packages as "unknown-repository"), its
# source was downloaded by the ports build into /usr/ports/distfiles, and it
# runs.
# Exit 0 / 1.
q=$(pkg query '%o %R' tree 2>/dev/null) || { echo "FAIL: tree is not installed"; exit 1; }
[ "$q" = "sysutils/tree unknown-repository" ] || { echo "FAIL: tree recorded as '$q', not built from ports"; exit 1; }
ls /usr/ports/distfiles/tree-*.t* >/dev/null 2>&1 || { echo "FAIL: no downloaded tree source in /usr/ports/distfiles: not a ports build"; exit 1; }
/usr/local/bin/tree --version >/dev/null 2>&1 || { echo "FAIL: tree does not run"; exit 1; }
echo "OK: tree built from ports and working"; exit 0
