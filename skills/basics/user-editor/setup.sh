#!/bin/sh
# Preconditions for basics/user-editor (test input USER=hbtest9,
# EDITORPATH=/usr/bin/ee): an ordinary account hbtest9 with the default
# startup files, which set EDITOR to vi.
rm -f /var/db/hb-usered || exit 1
pw usershow hbtest9 >/dev/null 2>&1 && { echo "setup: hbtest9 exists"; exit 1; }
pw useradd -n hbtest9 -d /home/hbtest9 -m -s /bin/sh -w no || exit 1
grep -q '^EDITOR=vi;' /home/hbtest9/.profile && grep -Eq '^setenv[[:space:]]+EDITOR[[:space:]]+vi$' /home/hbtest9/.cshrc || { echo "setup: default EDITOR lines missing"; exit 1; }
# Recorded for verify.sh: each startup file with its EDITOR line removed
# (checksums), and owner:group:mode of both files.
p=$(grep -v '^EDITOR=' /home/hbtest9/.profile | sha256) && c=$(grep -Ev '^setenv[[:space:]]+EDITOR[[:space:]]' /home/hbtest9/.cshrc | sha256) || exit 1
o=$(stat -f '%Su:%Sg:%Mp%Lp' /home/hbtest9/.profile /home/hbtest9/.cshrc | tr '\n' ' ') || exit 1
(set -C; echo "$p $c $o" > /var/db/hb-usered) || exit 1
