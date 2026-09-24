#!/bin/sh
# The true RESULT line, from the downloaded list, without the model. pkg audit
# exits 1 with a list when something is affected; anything else means it could
# not check or did not see the planted package, and then no answer is given
# (exit 2), so "could not check" never reads as "nothing found".
[ -f /var/db/pkg/vuln.xml ] || exit 2
out=$(pkg audit -q 2>/dev/null); rc=$?
# setup.sh planted libssh2-1.8.0, so a correct check must name it; anything
# else means the test premise failed, which must not pass as an answer.
if [ $rc -eq 1 ] && printf '%s\n' "$out" | grep -qx 'libssh2-1.8.0'; then
    echo "RESULT: VULNERABLE $(printf '%s\n' "$out" | tr '\n' ' ' | sed 's/ $//')"; exit 0
fi
exit 2
