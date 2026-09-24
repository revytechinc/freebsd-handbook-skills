#!/bin/sh
# Independent check for ports/pkg-audit: the vulnerability list was downloaded
# during the run (newer than setup's stamp). The reported answer is checked by
# answer.sh. Exit 0 / 1.
[ -f /var/db/pkg/vuln.xml ] || { echo "FAIL: no vulnerability list downloaded"; exit 1; }
s=$(cat /var/db/hbskills-audit.stamp 2>/dev/null); m=$(stat -f %c /var/db/pkg/vuln.xml)
[ -n "$s" ] && [ "$m" -ge "$s" ] || { echo "FAIL: the list was not downloaded during the run"; exit 1; }
echo "OK: vulnerability list downloaded"; exit 0
