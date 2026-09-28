#!/bin/sh
# Preconditions for basics/man-search (test input KEYWORD=crontab): no
# manual-page search database, as on 15.0 and later before the weekly
# periodic job has run (14.x ships one; the databases of all manual-page
# folders are removed here so every release takes the same path).
m=$(env -u MANPATH manpath -q) || exit 1
bad=$(printf '%s\n' "$m" | tr ':' '\n' | while IFS= read -r d; do
    case "$d" in /*) rm -f -- "$d/mandoc.db" || echo "rm failed: $d" ;; *) echo "odd manpath entry: $d" ;; esac
done)
[ -z "$bad" ] || { echo "setup: $bad"; exit 1; }
o=$(env -u MANPATH man -k crontab 2>&1); r=$?
[ $r = 5 ] && [ "$o" = "apropos: nothing appropriate" ] || { echo "setup: man -k gave $r: $o"; exit 1; }
exit 0
