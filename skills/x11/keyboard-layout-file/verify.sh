#!/bin/sh
# Independent check for x11/keyboard-layout-file (test inputs LAYOUTS=de,us,
# VARIANTS=nodeadkeys, (German without dead keys, then US), MODEL=pc105,
# OPTIONS=grp:alt_shift_toggle): 00-keyboard.conf holds exactly the
# InputClass section, no other file X.org reads sets an Xkb option, and the
# X server, started once, reads the folder and parses every file without an
# error (it then stops: the test machines have no console it can use).
# Exit 0 when verified, 1 otherwise.
d=/usr/local/etc/X11/xorg.conf.d
want=$(printf 'Section "InputClass"\n\tIdentifier      "Keyboard1"\n\tMatchIsKeyboard "on"\n\tOption "XkbLayout"  "de,us"\n\tOption "XkbVariant" "nodeadkeys,"\n\tOption "XkbModel"   "pc105"\n\tOption "XkbOptions" "grp:alt_shift_toggle"\nEndSection')
printf '%s\n' "$want" | cmp -s - "$d/00-keyboard.conf" || { echo "FAIL: $d/00-keyboard.conf missing or different"; exit 1; }
# Option names are compared ignoring case, "_" and spaces (as X.org does).
others=$(for x in /etc/X11/xorg.conf* /usr/local/etc/X11/xorg.conf* /etc/xorg.conf* /usr/local/lib/X11/xorg.conf* "$d"/*.conf /etc/X11/xorg.conf.d/*.conf /usr/local/share/X11/xorg.conf.d/*.conf; do [ -f "$x" ] && echo "$x"; done | xargs awk 'tolower($1)=="option" {n=$0; sub(/^[^"]*"/,"",n); sub(/".*/,"",n); n=tolower(n); gsub(/[_ \t]/,"",n); if (n ~ /^xkb(layout|variant|model|options|keymap)$/) print FILENAME}' | sort -u | grep -vx "$d/00-keyboard.conf")
[ -z "$others" ] || { echo "FAIL: other files also set a keyboard layout: $others"; exit 1; }
log=/tmp/hbv-xkb.$$.log
timeout 60 /usr/local/bin/Xorg :7 -logfile "$log" -nolisten tcp >/dev/null 2>&1
grep -q 'Using config directory: "/usr/local/etc/X11/xorg.conf.d"' "$log" || { echo "FAIL: Xorg did not read $d"; rm -f "$log"; exit 1; }
if grep -qE 'Problem parsing|Parse error|Error parsing' "$log"; then grep -E 'Parse error' "$log"; rm -f "$log"; echo "FAIL: Xorg could not parse its configuration"; exit 1; fi
rm -f "$log"
echo "OK: 00-keyboard.conf in place (de,us / nodeadkeys, / pc105 / grp:alt_shift_toggle); Xorg parses it"
