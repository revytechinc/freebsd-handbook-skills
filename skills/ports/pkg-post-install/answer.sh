#!/bin/sh
# True answer for test-inputs.txt (PACKAGE=rsync), read on the target without
# the model: the startup scripts rsync installed in /usr/local/etc/rc.d, in
# alphabetical order. Its line must be an exact line of the model's final
# message.
l=$(pkg info -l rsync) || exit 1
s=$(printf '%s\n' "$l" | sed -n 's#^[[:space:]]*/usr/local/etc/rc.d/##p' | LC_ALL=C sort | xargs)
echo "RESULT: services ${s:-none}"
