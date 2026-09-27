#!/bin/sh
# Preconditions for basics/shared-folder (test input NAME=hbproj,
# GROUP=hbshare): ordinary accounts hbta, hbtb (members of the group hbshare)
# and hbtc (not a member); no /home/hbproj.
for u in hbta hbtb hbtc hbproj; do pw usershow $u >/dev/null 2>&1 && { echo "setup: $u exists"; exit 1; }; done
pw groupshow hbshare >/dev/null 2>&1 && { echo "setup: group hbshare exists"; exit 1; }
[ -e /home/hbproj ] && { echo "setup: /home/hbproj exists"; exit 1; }
for u in hbta hbtb hbtc; do pw useradd -n $u -d /home/$u -m -s /bin/sh -w no || exit 1; done
pw groupadd hbshare -M hbta,hbtb || exit 1
