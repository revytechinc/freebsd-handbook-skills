#!/bin/sh
# Independent check for ports/port-options (test input PORT=shells/bash,
# OPTION=SYSLOG, STATE=on): /etc/make.conf is exactly the comment setup.sh
# left (which had no line break) and, on its own line, the one line that turns
# SYSLOG on for shells/bash, no saved options file was made (the menu was not
# used), make read the line into shells_bash_SET, the ports framework now has SYSLOG on and the other options at their
# defaults, and nothing was built or installed.
# Exit 0 / 1.
[ "$(printf '# local settings\nshells_bash_SET+=SYSLOG\n' | sha256)" = "$(sha256 -q /etc/make.conf 2>/dev/null)" ] || { echo "FAIL: /etc/make.conf is not the comment line plus 'shells_bash_SET+=SYSLOG'"; exit 1; }
[ ! -e /var/db/ports/shells_bash ] || { echo "FAIL: saved options exist in /var/db/ports/shells_bash"; exit 1; }
[ "$(make -C /usr/ports/shells/bash -V '${shells_bash_SET}|${shells_bash_UNSET}')" = "SYSLOG|" ] || { echo "FAIL: make did not read SYSLOG into shells_bash_SET"; exit 1; }
o=$(make -C /usr/ports/shells/bash -V PORT_OPTIONS | xargs -n1 | LC_ALL=C sort | xargs)
[ "$o" = "DOCS HELP NLS SYSBASHRC SYSLOG" ] || { echo "FAIL: bash options are '$o'"; exit 1; }
pkg -N >/dev/null 2>&1 || { echo "FAIL: pkg does not work"; exit 1; }
pkg info -e bash; [ $? -eq 1 ] || { echo "FAIL: bash was installed, or pkg could not tell"; exit 1; }
w=$(make -C /usr/ports/shells/bash -V WRKDIR) && [ -n "$w" ] || { echo "FAIL: no WRKDIR"; exit 1; }
[ ! -d "$w" ] || { echo "FAIL: bash was built (in $w)"; exit 1; }
echo "OK: SYSLOG on for shells/bash through /etc/make.conf only"; exit 0
