#!/bin/sh
# The true answer for test-inputs.txt (PACKAGE=curl, deliberately not the package used in the skill's examples), read from the
# catalogue on the target without the model. Printed line must appear in the
# model's final message.
v=$(env IGNORE_OSVERSION=yes pkg rquery -U '%v' curl 2>/dev/null) || exit 1
[ -n "$v" ] || exit 1
echo "RESULT: curl $v"
