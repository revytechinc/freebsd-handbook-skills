#!/bin/sh
# Independent check for basics/shells-add (test input
# SHELL=/usr/local/bin/hbsh): /etc/shells is exactly its old content plus one
# last line /usr/local/bin/hbsh, with the same mode and owner.
# Exit 0 / 1.
read -r c0 m0 < /var/db/hb-shellsadd && [ -n "$m0" ] || { echo "FAIL: no values recorded by setup"; exit 1; }
[ "$(stat -f '%Mp%Lp:%Su:%Sg' /etc/shells)" = "$m0" ] || { echo "FAIL: /etc/shells mode or owner changed"; exit 1; }
[ "$(tail -n 1 /etc/shells)" = /usr/local/bin/hbsh ] || { echo "FAIL: last line is '$(tail -n 1 /etc/shells)'"; exit 1; }
[ "$(grep -c hbsh /etc/shells)" = 1 ] || { echo "FAIL: hbsh listed more than once"; exit 1; }
n=$(wc -l < /etc/shells) || { echo "FAIL: cannot read /etc/shells"; exit 1; }
old=$(head -n $((n - 1)) /etc/shells | sha256) || { echo "FAIL: cannot read /etc/shells"; exit 1; }
[ "$old" = "$c0" ] || { echo "FAIL: the rest of /etc/shells changed"; exit 1; }
[ "$(tail -c 1 /etc/shells | od -An -c | tr -d ' ')" = '\n' ] || { echo "FAIL: /etc/shells does not end with a newline"; exit 1; }
echo "OK: /usr/local/bin/hbsh added to /etc/shells"; exit 0
