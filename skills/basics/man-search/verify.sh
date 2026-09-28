#!/bin/sh
# Independent check for basics/man-search: every manual-page folder has its
# search database again; the base one is
# owned by root with mode 644, and man -k finds crontab(1) and
# crontab(5).
# Exit 0 / 1.
db=/usr/share/man/mandoc.db
[ -f $db ] && [ ! -L $db ] || { echo "FAIL: no $db"; exit 1; }
[ "$(stat -f '%Su %Lp' $db)" = "root 644" ] || { echo "FAIL: $db is $(stat -f '%Su %Lp' $db)"; exit 1; }
m=$(env -u MANPATH manpath -q) || { echo "FAIL: manpath failed"; exit 1; }
bad=$(printf '%s\n' "$m" | tr ':' '\n' | while IFS= read -r d; do
    # A folder with no pages gets no database (makewhatis skips empty ones).
    # Any find output, an error included, counts as "has pages".
    [ -d "$d" ] || continue
    [ -n "$(find -L "$d" ! -type d -path "$d/*/*" ! -name mandoc.db 2>&1 | head -n 1)" ] || continue
    { [ -f "$d/mandoc.db" ] && [ ! -L "$d/mandoc.db" ] && [ "$(stat -f %Lp "$d/mandoc.db")" = 644 ]; } || echo "$d"
done)
[ -z "$bad" ] || { echo "FAIL: no database in: $bad"; exit 1; }
out=$(env -u MANPATH man -k crontab 2>&1) || { echo "FAIL: man -k crontab failed: $out"; exit 1; }
printf '%s\n' "$out" | grep -q '^crontab(1) ' && printf '%s\n' "$out" | grep -q '^crontab(5) ' || { echo "FAIL: man -k crontab gave: $out"; exit 1; }
echo "OK: man -k works"; exit 0
