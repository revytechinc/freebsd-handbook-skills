#!/bin/sh
# Independent check for basics/user-editor (test input USER=hbtest9,
# EDITORPATH=/usr/bin/ee): a login shell (sh) of hbtest9 sees EDITOR=/usr/bin/ee;
# .cshrc sets EDITOR to /usr/bin/ee; the rest of both files, and their owner,
# group and mode, are unchanged.
# Exit 0 / 1.
read -r p0 c0 o1 o2 < /var/db/hb-usered && [ -n "$o2" ] || { echo "FAIL: no values recorded by setup"; exit 1; }
H=/home/hbtest9
[ "$(grep -c '^EDITOR=' $H/.profile)" = 1 ] && grep -Eq '^EDITOR=/usr/bin/ee;[[:space:]]*export[[:space:]]+EDITOR$' $H/.profile || { echo "FAIL: .profile EDITOR line: $(grep '^EDITOR' $H/.profile)"; exit 1; }
[ "$(grep -Ec '^setenv[[:space:]]+EDITOR[[:space:]]' $H/.cshrc)" = 1 ] && grep -Eq '^setenv[[:space:]]+EDITOR[[:space:]]+/usr/bin/ee$' $H/.cshrc || { echo "FAIL: .cshrc EDITOR line: $(grep EDITOR $H/.cshrc)"; exit 1; }
[ "$(grep -v '^EDITOR=' $H/.profile | sha256)" = "$p0" ] || { echo "FAIL: other lines of .profile changed"; exit 1; }
[ "$(grep -Ev '^setenv[[:space:]]+EDITOR[[:space:]]' $H/.cshrc | sha256)" = "$c0" ] || { echo "FAIL: other lines of .cshrc changed"; exit 1; }
[ "$(stat -f '%Su:%Sg:%Mp%Lp' $H/.profile $H/.cshrc | tr '\n' ' ')" = "$o1 $o2 " ] || { echo "FAIL: owner or mode changed"; exit 1; }
e=$(su -l hbtest9 -c '/usr/bin/printenv EDITOR' </dev/null 2>/dev/null | tail -n 1) || true
[ "$e" = "/usr/bin/ee" ] || { echo "FAIL: a login shell sees '$e'"; exit 1; }
e=$(env -i PATH=/bin:/usr/bin su -m hbtest9 -c "env -i HOME=$H /bin/csh -f -c 'source $H/.cshrc; echo E=\$EDITOR'" </dev/null 2>/dev/null | grep '^E=') || true
[ "$e" = "E=/usr/bin/ee" ] || { echo "FAIL: csh sees '$e'"; exit 1; }
echo "OK: hbtest9's EDITOR is /usr/bin/ee"; exit 0
