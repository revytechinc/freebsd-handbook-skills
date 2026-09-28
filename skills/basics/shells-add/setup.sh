#!/bin/sh
# Preconditions for basics/shells-add (test input SHELL=/usr/local/bin/hbsh):
# an installed shell /usr/local/bin/hbsh (a copy of /bin/sh, root-owned, mode
# 555) that is not listed in /etc/shells. (A copy stands in for a shell from
# a package, so the test needs no network.)
rm -f /var/db/hb-shellsadd || exit 1
[ -e /usr/local/bin/hbsh ] || [ -L /usr/local/bin/hbsh ] && { echo "setup: hbsh exists"; exit 1; }
grep -q hbsh /etc/shells && { echo "setup: hbsh listed"; exit 1; }
mkdir -p /usr/local/bin && cp /bin/sh /usr/local/bin/hbsh && chown root:wheel /usr/local/bin/hbsh && chmod 555 /usr/local/bin/hbsh || exit 1
# Recorded for verify.sh: /etc/shells' checksum, mode and owner.
c=$(sha256 -q /etc/shells) && m=$(stat -f '%Mp%Lp:%Su:%Sg' /etc/shells) || exit 1
(set -C; echo "$c $m" > /var/db/hb-shellsadd) || exit 1
