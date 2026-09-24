#!/bin/sh
# Independent check for ports/pkg-set-origin (test inputs OLD=devel/pcre2-old,
# NEW=devel/pcre2): pcre2 records devel/pcre2 again, was reinstalled after
# setup, and nginx still runs. Exit 0 / 1.
o=$(pkg query '%o' pcre2) || { echo "FAIL: pcre2 not installed"; exit 1; }
[ "$o" = devel/pcre2 ] || { echo "FAIL: pcre2 origin is $o"; exit 1; }
s=$(cat /var/db/hbskills-origin.stamp 2>/dev/null)
[ -n "$s" ] || { echo "FAIL: no stamp from setup.sh"; exit 1; }
t=$(pkg query '%t' pcre2)
[ "$t" -ge "$s" ] || { echo "FAIL: pcre2 was not reinstalled during the run"; exit 1; }
/usr/local/sbin/nginx -v >/dev/null 2>&1 || { echo "FAIL: the nginx program no longer starts"; exit 1; }
echo "OK: origin devel/pcre2, reinstalled, nginx program starts"; exit 0
