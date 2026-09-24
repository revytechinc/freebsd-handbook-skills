#!/bin/sh
# The true RESULT line, computed on the machine without the model.
[ -f /usr/ports/Mk/bsd.port.mk ] || exit 1
out=$(pkg version -l '<' 2>/dev/null) || exit 1
names=$(printf '%s\n' "$out" | awk 'NF {print $1}' | tr '\n' ' ' | sed 's/ $//')
if [ -n "$names" ]; then echo "RESULT: OUTDATED $names"; else echo "RESULT: nothing to update"; fi
