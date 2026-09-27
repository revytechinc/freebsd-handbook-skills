#!/bin/sh
# Preconditions for basics/users-remove (test input USER=hbtest2): a regular
# account hbtest2 made by adduser (on ZFS 14.1 and later, with its own home
# dataset), with a
# home folder, a mail file, a crontab, a running
# process, and membership of the group operator.
pw usershow hbtest2 >/dev/null 2>&1 && exit 1
# adduser, as the Handbook does: on a ZFS machine it makes the home a
# dataset of its own, which rmuser then has to destroy.
f=$(mktemp) && printf '%s\n' 'hbtest2::::::Removal Test::sh:' > "$f" && adduser -f "$f" -w no >/dev/null || exit 1
rm -f "$f"; pw groupmod operator -m hbtest2 || exit 1
rm -f /var/mail/hbtest2 && t=$(mktemp) && echo 'test mail' > "$t" && chown hbtest2 "$t" && mv "$t" /var/mail/hbtest2 && [ -f /var/mail/hbtest2 ] && [ ! -L /var/mail/hbtest2 ] || exit 1
echo '0 3 * * * true' | crontab -u hbtest2 - || exit 1
daemon -u hbtest2 sleep 3600 </dev/null >/dev/null 2>&1 || exit 1   # no open output, so ssh can end
sleep 1
pgrep -U hbtest2 sleep >/dev/null || exit 1
rm -f /var/db/hb-rmuser-uid && u=$(id -u hbtest2) && (set -C; echo "$u" > /var/db/hb-rmuser-uid) || exit 1
