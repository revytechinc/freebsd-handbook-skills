#!/bin/sh
# True answer for test-inputs.txt (PORT=sysutils/lsof), read on the target
# without the model: the IGNORE value the ports framework sets for the port
# (BROKEN and FORBIDDEN end up there too). Its line must be an exact line of
# the model's final message.
p=/usr/ports/sysutils/lsof
[ -f $p/Makefile ] || exit 1
t=$(make -C $p -V IGNORE) || exit 1
echo "RESULT: IGNORE=[$t]"
