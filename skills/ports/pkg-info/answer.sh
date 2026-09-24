#!/bin/sh
# True answer for test-inputs.txt (PACKAGE=nginx-lite), read on the target
# without the model. Its line must be an exact line of the model's final message.
v=$(pkg query '%v' nginx-lite 2>/dev/null) || exit 1
[ -n "$v" ] || exit 1
echo "RESULT: nginx-lite $v installed"
