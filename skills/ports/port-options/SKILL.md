---
name: ports-port-options
description: Turn one build option of a port on or off in /etc/make.conf, without the option menu, before building the port.
handbook: ports/#ports-using
handbook_commit: bdf18a0458
---

# Set a port's build option without the menu

## What this does

Many ports have build options: features that can be built in or left out,
such as `NLS` (messages in other languages) or `DOCS` (documentation). The
Handbook sets them with `make config`, a menu that waits for keyboard input.
This skill sets one option instead with one line in `/etc/make.conf`, the file
the ports build reads for settings, and checks that the ports framework sees
it. The next build of the port (skill `ports/port-install`) uses it. Nothing is
built or installed here.

## Before you start

- You need: a root shell, and the Ports Collection in `/usr/ports` (skill
  `ports/ports-tree-git`).
- This changes: adds one line to `/etc/make.conf` (the file is created if it
  does not exist).
- Time: seconds.
- Risk: low. Undo removes the line (a line break added in step 4 to the end
  of the previous last line stays; make does not mind it).

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `PORT` | the port's directory under `/usr/ports`: category, `/`, name | `editors/nano` |
| `OPTION` | the option's name, in capital letters | `NLS` |
| `STATE` | `on` to build the feature in, `off` to leave it out | `off` |

Everywhere below, replace `PORT`, `OPTION` and `STATE` with these values,
exactly as given. Check them first:

- `PORT` must be one word, a `/`, and another word; each word must start with a
  letter or a digit, and may contain only letters, digits, and the characters
  `.` `_` `+` `-`.
- `OPTION` must start with a capital letter, and may contain only capital
  letters `A`-`Z`, digits and `_`.
- `STATE` must be exactly `on` or exactly `off`.

If any of them does not, stop and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.

| The line starts with | Do this |
|---|---|
| `14.`, `15.` or `16.` (including 14.0 to 14.3, end of life as of 2026-09-24) | go to step 2. The steps are the same on every release |
| anything else | stop, and report the line: this skill was not tested there |

## Step 2: Read the port's option names

Run:

    ls /usr/ports/PORT/Makefile; make -C /usr/ports/PORT -V OPTIONS_NAME -V OPTIONS_FILE -V COMPLETE_OPTIONS_LIST; echo "exit=$?"

Expected: four lines, then `exit=0`. For `editors/nano`:

    /usr/ports/editors/nano/Makefile
    editors_nano
    /var/db/ports/editors_nano/options
    DOCS EXAMPLES NLS
    exit=0

The second line is the port's option name; below it is called `NAME`. The
third line is where the menu saves its choices; below it is called `FILE`.
The fourth line lists every option the port has.

| If you see | Do this |
|---|---|
| four lines, the last one containing `OPTION` as a whole word, then `exit=0` | write down `NAME` and `FILE`, check them (below), and go to step 3 |
| four lines, but `OPTION` is not one of the words on the fourth line | the port has no such option. Stop, and report the fourth line |
| `ls: /usr/ports/PORT/Makefile: No such file or directory` | there is no such port, or no ports tree. Stop, and report it |
| anything else | stop, and report the full output |

`NAME` and `FILE` are pasted into root commands below, so check them first.
`NAME` must contain only letters, digits, and the characters `_` and `-` (a
port whose `NAME` has any other character, such as `.`, is not handled by
this skill: Undo matches `NAME` as a pattern, where `.` would match other
lines).
`FILE` must be exactly `/var/db/ports/`, then `NAME`, then `/options`. If
either is not, stop and report both: do not run any command with them.

## Step 3: Check nothing else already sets this port's options

Choices saved from the menu (in `FILE`, or in `FILE.local` next to it) win
over `/etc/make.conf`, and so do lines containing `_FORCE`, so a line added there would be ignored. Run (with `FILE` and
`NAME` from step 2):

    ls FILE FILE.local; echo "exit=$?"; grep -n -e 'NAME_' -e '_FORCE' /etc/make.conf; echo "exit=$?"

| If you see | Do this |
|---|---|
| `ls: FILE: No such file or directory`, `ls: FILE.local: No such file or directory`, `exit=1`, then a line ending in `No such file or directory` and `exit=2` | there is no `/etc/make.conf` yet and no saved choices. Go to step 4 |
| `ls: FILE: No such file or directory`, `ls: FILE.local: No such file or directory`, `exit=1`, then only `exit=1` | no saved choices, and `/etc/make.conf` sets nothing for this port. Go to step 4 |
| `FILE` or `FILE.local` shown on a line by itself | someone chose options for this port with the menu. Stop, and report it: this skill does not remove those choices |
| one or more lines starting with a number and `:` | `/etc/make.conf` already sets options for this port, or forces options for every port. Stop, and report those lines: this skill does not edit them |
| anything else | stop, and report the full output |

Write down whether `/etc/make.conf` existed (the first two rows): Undo needs it.

## Step 4: Add the line

Run the command for `STATE` (with `NAME` from step 2). The part before the
first `;` adds a line break at the end of `/etc/make.conf` if its last line
has none, so the new line does not join onto it:

- **on**: `[ -s /etc/make.conf ] && [ -n "$(tail -c1 /etc/make.conf)" ] && echo >> /etc/make.conf; printf '%s\n' 'NAME_SET+=OPTION' >> /etc/make.conf; echo "exit=$?"`
- **off**: `[ -s /etc/make.conf ] && [ -n "$(tail -c1 /etc/make.conf)" ] && echo >> /etc/make.conf; printf '%s\n' 'NAME_UNSET+=OPTION' >> /etc/make.conf; echo "exit=$?"`

Expected: `exit=0`. For `editors/nano`, `NLS` and `off`, the line added is
`editors_nano_UNSET+=NLS`. Anything else: stop and report.

## Step 5: Check the options still make sense together

Some options come in groups where exactly one must be on, such as a choice
between two libraries. Turning one on can break such a group. Run:

    make -C /usr/ports/PORT check-config; echo "exit=$?"

| If you see | Do this |
|---|---|
| only `exit=0` | go to step 6 |
| lines such as `You must select one and only one option from the ... single`, then `exit=1` | the port's options break a group with the new line present. Run the Undo below, then stop: report the lines shown, and end with FAILED |
| anything else | run the Undo below, then stop: report the full output, and end with FAILED |

## Step 6: Verify

Run (with `NAME` from step 2):

    make -C /usr/ports/PORT -V 'SET=${NAME_SET} UNSET=${NAME_UNSET}'; make -C /usr/ports/PORT showconfig | grep ' OPTION='; echo "exit=$?"

Expected: a line showing which list make read the option into, then the
option's line from the port's configuration, then `exit=0`. For
`editors/nano`, `NLS` and `off`:

    SET= UNSET=NLS
         NLS=off: Native Language Support
    exit=0

| If you see | Do this |
|---|---|
| `STATE` is `on`: first line `SET=OPTION UNSET=`, second line containing `OPTION=on:`, then `exit=0` | finished |
| `STATE` is `off`: first line `SET= UNSET=OPTION`, second line containing `OPTION=off:`, then `exit=0` | finished |
| anything else | make did not read the line from step 4, or something overrides it. Run the Undo, then stop: report the output, and end with FAILED |

## Undo

Remove the line added in step 4 (use the same `NAME_SET` or `NAME_UNSET`
text):

    sed -i '' '/^NAME_SET+=OPTION$/d' /etc/make.conf; echo "exit=$?"

or, for `off`:

    sed -i '' '/^NAME_UNSET+=OPTION$/d' /etc/make.conf; echo "exit=$?"

Expected: `exit=0`. Then check the line is gone:

    grep -c -e '^NAME_SET+=OPTION$' -e '^NAME_UNSET+=OPTION$' /etc/make.conf; echo "exit=$?"

Expected: `0`, then `exit=1`. Anything else: stop and report. If step 3 found
no `/etc/make.conf`, it is now an empty file; make treats an empty
`/etc/make.conf` the same as none, so leave it.

A port already built with the option keeps it until it is built again.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | Ports tree `main`. |
| 15.1-RELEASE | verified | 2026-09-24 | Ports tree `2026Q3`. |
| 15.0-RELEASE | verified | 2026-09-24 | As 15.1. |
| 14.5-RELEASE | verified | 2026-09-24 | As 15.1. |
| 14.4-RELEASE | verified | 2026-09-24 | As 15.1. |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | As 15.1. Unlike building, reading and checking options works on an end-of-life release without `ALLOW_UNSUPPORTED_SYSTEM`. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill, the inputs
`PORT=shells/bash`, `OPTION=SYSLOG`, `STATE=on` (deliberately not the port,
option or direction in the skill's examples), and a tool that runs one command
on the test machine, followed it on a freshly reset system of every release
above, with the ports tree cloned beforehand and an `/etc/make.conf` holding
one comment line with no line break at its end. A run counts only when the
model said DONE AND the independent check (`verify.sh`: `/etc/make.conf` is
exactly that comment, then `shells_bash_SET+=SYSLOG` on its own line, no
options were saved by the menu, make read `SYSLOG` into `shells_bash_SET`, the
ports framework reports `SYSLOG` on and the other options at their defaults,
and nothing was built) passed: all 9 did, with the final text and scripts. A manual
review of the command logs showed exactly the skill's six commands on every
release, in order.

## Not verified

- The Haiku runs used `STATE=on` only. The `off` command, a group broken in
  step 5, and the Undo were tried by hand on 14.1 only, not by the model:
  `editors_nano_UNSET+=NLS` gave `NLS=off`;
  `editors_vim_SET+=CTAGS_UNIVERSAL` made `make check-config` stop with
  `You must select one and only one option from the CTAGS single`; and the
  Undo removed `shells_bash_SET+=SYSLOG`, printed `0` and `exit=1`, and left
  `SYSLOG=off` with the rest of the file unchanged.
- Building a port with an option changed this way is the skill
  `ports/port-install`; here only the ports framework's view of the option is
  checked.
- Settings that reach `/etc/make.conf` through `.include` from another file,
  and the older forms `OPTIONS_FILE_SET`, `OPTIONS_FILE_UNSET`, `WITH=` and
  `WITHOUT=`, are not checked in step 3; step 6 catches them only if they change the
  result.
- Options that other options depend on (for example, a feature that needs
  `DOCS`) are not checked beyond `make check-config`.

## Differences from the Handbook

- The Handbook uses `make config`, a menu that waits for keyboard input; a
  model or a script cannot drive it. `/etc/make.conf` with
  `NAME_SET+=` or `NAME_UNSET+=` sets the same thing, and is the form the
  Handbook's `make.conf` examples and the ports framework (`bsd.options.mk`)
  document.
- Tested: choices saved by the menu (`FILE`) override `/etc/make.conf`. With
  `editors_nano_UNSET+=NLS` in `/etc/make.conf` and a saved file turning `NLS`
  on, `make -V PORT_OPTIONS` reported `NLS` on. `make rmconfig` removes the saved file;
  this skill does not run it, because that discards someone's choices.

## Source

FreeBSD Handbook, "Using the Ports Collection",
https://docs.freebsd.org/en/books/handbook/ports/#ports-using
