---
name: x11-keyboard-layout-file
description: Set the keyboard layout X.org uses (layouts, variants, model and options) with a file in /usr/local/etc/X11/xorg.conf.d, after checking every name against the list the keyboard data itself provides.
handbook: x11/#x-config-input-keyboard-layout
handbook_commit: bdf18a0458
---

# Set the X.org keyboard layout in a file

## What this does

Writes `/usr/local/etc/X11/xorg.conf.d/00-keyboard.conf`, an `InputClass`
section that applies to every keyboard, with the keyboard layout (one or
more, such as German and US), a variant for each, the keyboard model, and
options (such as the key combination that switches between layouts). X.org
reads it the next time it starts.

Before writing, every name is checked against
`/usr/local/share/X11/xkb/rules/base.lst`, the list of models, layouts,
variants and options that the keyboard data on the machine provides. A
name that is not there would make X.org fail to load the layout.

## Before you start

- You need: a root shell and the X server installed (skill
  `x11/xorg-install`).
- This changes: creates one file in `/usr/local/etc/X11/xorg.conf.d/`.
- Time: under a minute.
- Risk: low: Undo removes the file.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `LAYOUTS` | one or more layouts, separated by commas | `es,fr` |
| `VARIANTS` | a variant for each layout, separated by commas; empty for the standard one | `,azerty` |
| `MODEL` | the keyboard model | `pc105` |
| `OPTIONS` | options, separated by commas; may be empty | `grp:win_space_toggle` |

`LAYOUTS` has 1 to 4 names; each name is letters, digits and `_`.
`VARIANTS` has at most as many entries as `LAYOUTS` (an empty entry means
the standard variant; `VARIANTS` may be empty altogether); each entry is
letters, digits, `_` and `-`. `MODEL` is letters, digits, `_` and `-`.
`OPTIONS` is empty, or names of letters, digits, `_` and `:`, separated by
commas. None contains a space, a quote or any other character. If any input does
not fit, stop, report it, run no command, and end with FAILED. Everywhere
below, replace `LAYOUTS`, `VARIANTS`, `MODEL` and `OPTIONS` with the
values, exactly as given (an empty value becomes nothing, so `'VARIANTS'`
becomes `''`).

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24) | go to step 2 |
| anything else | stop, report the line, and end with FAILED: this skill was not tested there |

## Step 2: Check the X server and its keyboard data

Run:

    pkg info -e xorg-server; echo "xserver=$?"; ls /usr/local/share/X11/xkb/rules/base.lst

| If you see | Do this |
|---|---|
| `xserver=0`, then `/usr/local/share/X11/xkb/rules/base.lst` | go to step 3 |
| `xserver=1` | the X server is not installed. Stop, report it, and end with FAILED (install it first with `x11/xorg-install`) |
| anything else | stop, report the output, and end with FAILED |

## Step 3: Check every name

This looks up the model, each layout, each variant (for the layout in the
same position) and each option in the list, prints a line `UNKNOWN ...` for
each name that is not there, and then `VALID` or `INVALID`. Run:

    awk -v L='LAYOUTS' -v V='VARIANTS' -v M='MODEL' -v O='OPTIONS' 'BEGIN{nl=split(L,la,","); nv=split(V,va,","); no=split(O,oa,",")} /^! /{sec=$2; next} NF==0{next} sec=="model" && $1==M {mok=1} sec=="layout" {lay[$1]=1} sec=="variant" {sub(":","",$2); n=split($2,ls,","); for(j=1;j<=n;j++) var[$1" "ls[j]]=1} sec=="option" && $1 ~ /:/ {opt[$1]=1} END{bad=0; if(M=="" || !mok){print "UNKNOWN model " M; bad=1} if(nl==0){print "NO layouts"; bad=1} if(nl>4){print "TOO-MANY layouts"; bad=1} for(i=1;i<=nl;i++){if(la[i]=="" || !(la[i] in lay)){print "UNKNOWN layout " la[i]; bad=1}} if(nv>nl){print "TOO-MANY variants"; bad=1} for(i=1;i<=nv;i++){if(va[i]!="" && !((va[i]" "la[i]) in var)){print "UNKNOWN variant " va[i] " for layout " la[i]; bad=1}} for(i=1;i<=no;i++){if(oa[i]!="" && !(oa[i] in opt)){print "UNKNOWN option " oa[i]; bad=1}} print (bad ? "INVALID" : "VALID")}' /usr/local/share/X11/xkb/rules/base.lst

| If the last line is | Do this |
|---|---|
| `VALID` | go to step 4 |
| `INVALID` | report the `UNKNOWN` (or `NO layouts`) lines: those names do not exist (the variants of a layout are listed in that file under `! variant`, each followed by the layout, such as `nodeadkeys      de:`). Stop and end with FAILED |
| anything else | stop, report the output, and end with FAILED |

## Step 4: Check no other file sets the keyboard layout

Two things can make the new file useless:

- If `/etc/X11/xorg.conf.d/` holds any `.conf` file, X.org uses that folder
  **instead of** `/usr/local/etc/X11/xorg.conf.d/`, and the new file would
  be ignored.
- Another file X.org reads that also sets an `Xkb` option (`XkbLayout`,
  `XkbVariant`, `XkbModel`, `XkbOptions`, and also `XkbKeymap`, which
  replaces them; X.org ignores upper and lower case, `_` and spaces in
  option names, so `Xkb_Layout` counts too) would change or override these
  settings. (`XkbRules` does not count: the X server's own file
  `/usr/local/share/X11/xorg.conf.d/20-evdev-kbd.conf` sets it to `evdev`
  on every machine.)

This prints `SHADOWED` and the files if `/etc/X11/xorg.conf.d/` holds
`.conf` files, then every file X.org reads that sets an `Xkb` option, or
`NONE`. Run:

    s=$(ls /etc/X11/xorg.conf.d/*.conf 2>/dev/null); [ -n "$s" ] && echo "SHADOWED $s"; f=$(for x in /etc/X11/xorg.conf* /usr/local/etc/X11/xorg.conf* /etc/xorg.conf* /usr/local/lib/X11/xorg.conf* /usr/local/etc/X11/xorg.conf.d/*.conf /etc/X11/xorg.conf.d/*.conf /usr/local/share/X11/xorg.conf.d/*.conf; do [ -f "$x" ] && echo "$x"; done | xargs awk 'tolower($1)=="option" {n=$0; sub(/^[^"]*"/,"",n); sub(/".*/,"",n); n=tolower(n); gsub(/[_ \t]/,"",n); if (n ~ /^xkb(layout|variant|model|options|keymap)$/) print FILENAME}' | sort -u); echo "${f:-NONE}"

| If you see | Do this |
|---|---|
| a line starting `SHADOWED` | X.org reads `/etc/X11/xorg.conf.d/` instead. Do not change anything. Stop, report it, and end with FAILED |
| `NONE` (and no `SHADOWED`) | go to step 5 |
| exactly `/usr/local/etc/X11/xorg.conf.d/00-keyboard.conf` | the file may be there already: go to step 5, which checks it |
| any other file name | another file already sets the keyboard layout. Do not change it. Stop, report the file names, and end with FAILED |

## Step 5: Write the file

This writes the file only if nothing of that name exists yet (`written`;
it is written to a temporary file first and then moved into place, so a
failed write leaves nothing behind), says `already` if it exists with
exactly this content, and `different` (writing nothing) if it exists with
other content or is a link. Run:

    d=/usr/local/etc/X11/xorg.conf.d; f=$d/00-keyboard.conf; c=$(printf 'Section "InputClass"\n\tIdentifier      "Keyboard1"\n\tMatchIsKeyboard "on"\n\tOption "XkbLayout"  "%s"\n\tOption "XkbVariant" "%s"\n\tOption "XkbModel"   "%s"\n\tOption "XkbOptions" "%s"\nEndSection' 'LAYOUTS' 'VARIANTS' 'MODEL' 'OPTIONS'); if [ -L "$f" ]; then echo different; elif [ ! -e "$f" ]; then mkdir -p "$d" && printf '%s\n' "$c" > "$f.new" && mv "$f.new" "$f" && echo written || rm -f "$f.new"; elif printf '%s\n' "$c" | cmp -s - "$f"; then echo already; else echo different; fi; cat "$f"

Expected (with the values filled in; `already` instead of `written` if the
file was there):

    written
    Section "InputClass"
    	Identifier      "Keyboard1"
    	MatchIsKeyboard "on"
    	Option "XkbLayout"  "LAYOUTS"
    	Option "XkbVariant" "VARIANTS"
    	Option "XkbModel"   "MODEL"
    	Option "XkbOptions" "OPTIONS"
    EndSection

| If you see | Do this |
|---|---|
| `written` or `already`, then the lines above with the values | done: end with DONE |
| `different`, then other lines | `00-keyboard.conf` exists with other content. Do not change it. Stop, report it, and end with FAILED |
| anything else | stop, report the output, and end with FAILED |

Report the layout set and that X.org uses it the next time it starts. Note
whether step 5 said `written` (Undo needs to know).

## Undo

Only if step 5 said `written`, remove the file:

    rm /usr/local/etc/X11/xorg.conf.d/00-keyboard.conf; echo "exit=$?"

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-10-07, snapshot 20260921 (a6deeaa2fb3b) |  |
| 15.1-RELEASE | verified | 2026-10-07 | Also tried by hand. |
| 15.0-RELEASE | verified | 2026-10-07 |  |
| 14.5-RELEASE | verified | 2026-10-07 |  |
| 14.4-RELEASE | verified | 2026-10-07 |  |
| 14.3-RELEASE (EoL) | verified | 2026-10-07 |  |
| 14.2-RELEASE (EoL) | verified | 2026-10-07 |  |
| 14.1-RELEASE (EoL) | verified | 2026-10-07 |  |
| 14.0-RELEASE (EoL) | verified | 2026-10-07 |  |

## Weak-model check

2026-10-07 (UTC): claude-haiku-4-5, given only this skill, the inputs
`LAYOUTS=de,us`, `VARIANTS=nodeadkeys,`, `MODEL=pc105` and
`OPTIONS=grp:alt_shift_toggle` (not the skill's examples), and a tool that
runs one command on the test machine, followed it on a freshly reset system
of every release above (pkg and the X server installed beforehand). A run
counts only when the model said DONE AND the independent check
(`verify.sh`: `00-keyboard.conf` holds exactly the `InputClass` section, no
other file X.org reads sets a layout option in any spelling, and the X
server, started once, read the folder and parsed every file without an
error) passed: all 9 did, with the commands as they are now (the inputs
in single quotes).

## Not verified

- The test machines have only a serial console, so X.org cannot start
  there and no keyboard was used with these settings. Tried by hand on 15.1
  (2026-10-06): X.org reads and parses the files in
  `/usr/local/etc/X11/xorg.conf.d/` before it stops at
  `xf86OpenConsole: No console driver found`; a broken file is reported
  there as `Parse error` and `Problem parsing the config file` (an unclosed
  section is reported in the next file it reads). The `InputClass` section
  itself is applied only when a keyboard appears, which happens after that
  point, so its effect was not seen.
- Checking the names by compiling a keymap without a display
  (`setxkbmap -print ... | xkbcomp`) did not work: `setxkbmap` needs a
  running X server for that. Under `Xvfb`, `setxkbmap` rejected the
  Handbook's example with `Error loading new keyboard description`; it
  accepted a valid layout but did not change the layout `Xvfb` reported,
  so it was not used as a check.
- Changing the layout at runtime with `setxkbmap`, and listing input
  devices with `xinput`, need a running X session; they are not part of
  this skill.

## Differences from the Handbook

- The inputs are written into the commands as they are, so the rules in
  Inputs (only the listed characters, no spaces or quotes) are what keeps a
  value from being read as part of a command; nothing in the commands
  checks them again.
- The Handbook's example uses `XkbLayout "es, fr"` with `XkbVariant
  ",qwerty"`. The keyboard data on 15.1 has no `qwerty` variant for the
  French layout (`fr`); `base.lst` lists it for `cz`, `de`, `hu` and others,
  and `setxkbmap` rejected the example. The skill checks every name first.
  It writes the values without spaces after the commas.
- The skill always writes all four options (an empty value where an input
  is empty).

## Source

FreeBSD Handbook, "Input Configuration" and "Using X.org Configuration
Files", https://docs.freebsd.org/en/books/handbook/x11/#x-config-input-keyboard-layout
