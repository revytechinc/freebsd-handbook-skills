---
name: x11-xorg-install
description: Install the X.org server (the xorg package and everything it needs) and let one user run it by adding them to the video group.
handbook: x11/#x-install
handbook_commit: bdf18a0458
---

# Install the X.org server

## What this does

Installs the X Window System from the FreeBSD package repository: the
package `xorg` pulls in the X server (`Xorg`), its drivers, fonts and the
basic programs around it, such as the window manager `twm`. Then it adds one
user to the group `video`, which a user must belong to in order to run a
graphical environment.

## Before you start

- You need: a root shell, network access to `pkg.FreeBSD.org`, pkg itself
  installed (skill `ports/pkg-bootstrap`), and the user account that will use
  X (skill `basics/users-add`).
- This changes: installs about 190 packages under `/usr/local` and adds the
  user to the group `video`. If newer versions exist, pkg first upgrades
  itself and may upgrade packages already installed; Undo does not reverse
  those upgrades.
- Space and time: about 420 MB to download and 3 GB of free space; about two
  minutes with a fast connection.
- Risk: low. See Undo (it removes what this skill added, not upgrades).

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `USERNAME` | the login name of the user who will use X | `jru` |

Everywhere below, replace `USERNAME` with this value, exactly as given.
`USERNAME` must start with a lower-case letter and contain only lower-case
letters, digits, `_` and `-`, at most 16 characters. If it does not, stop,
report it, run no command with it, and end with FAILED.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24) | go to step 2. The steps are the same on every release |
| anything else | stop, report the line, and end with FAILED: this skill was not tested there |

## Step 2: Check the user

Run:

    id USERNAME; echo "exit=$?"

| If you see | Do this |
|---|---|
| a line starting `uid=` with `(USERNAME)`, then `exit=0` | go to step 3 |
| `id: USERNAME: no such user` and `exit=1` | there is no such user. Stop, report it, and end with FAILED (create the account first with `basics/users-add`) |
| anything else | stop, report the output, and end with FAILED |

## Step 3: Check whether xorg is already installed

Run:

    pkg -N >/dev/null 2>&1; echo "pkg=$?"; pkg -N >/dev/null 2>&1 && { pkg info -e xorg; echo "exit=$?"; }

`pkg=0` means pkg itself is installed and working; only then does the
`exit=` line say anything about xorg.

| If you see exactly | Do this |
|---|---|
| `pkg=0`, then `exit=1` (nothing else) | not installed: go to step 4 |
| `pkg=0`, then `exit=0` (nothing else) | already installed: skip step 4, go to step 5 |
| `pkg=` followed by anything other than `0` (and no `exit=` line) | pkg is not installed or not working. Stop, report it, and end with FAILED (install it first with `ports/pkg-bootstrap`) |
| anything else | stop, report the output, and end with FAILED |

## Step 4: Install xorg

Run exactly this (`-y` answers "yes" to pkg's question; without it, pkg
installs nothing):

    pkg install -y xorg > /root/xorg-install.log 2>&1; echo "exit=$?"; tail -5 /root/xorg-install.log

The full output is kept in `/root/xorg-install.log` (Undo needs it).

The log holds a long list: first pkg updates its list of packages, then it
shows `New packages to be INSTALLED:` with about 190 packages and
`Number of packages to be installed:`, then downloads and installs each one
(`[1/189] Installing ...`). Near the end, some packages print messages (for
example about `kern.evdev.rcpt_mask`); they are information only. The last
`exit=` line comes first on the screen, then the last lines of the log.

| If you see | Do this |
|---|---|
| `exit=0` | go to step 5 |
| `exit=` followed by anything other than `0` | run `grep -m3 -E 'No address record|Network is unreachable|timed out|Could not connect|No packages available' /root/xorg-install.log` to find the reason (such as no network), report it with the output, and end with FAILED |

## Step 5: Check the X server

Run:

    pkg query '%n %v' xorg; echo "query=$?"; v=$(/usr/local/bin/Xorg -version 2>&1); echo "xorg=$?"; echo "$v" | grep -m1 '^X.Org X Server'

Expected, such as:

    xorg 7.7_3
    query=0
    xorg=0
    X.Org X Server 1.21.1.24

| If you see | Do this |
|---|---|
| a line `xorg` and a version, `query=0`, `xorg=0`, then a line starting `X.Org X Server` | go to step 6 |
| anything else | stop, report the output, and end with FAILED |

## Step 6: Add the user to the video group

First look at the group as it is (Undo needs to know):

    [ -f /root/xorg-install-video-before.txt ] || pw groupshow video > /root/xorg-install-video-before.txt; echo "exit=$?"; cat /root/xorg-install-video-before.txt

It keeps a copy of the group as it was (only the first time, so running the
skill again does not overwrite it; Undo needs it), then shows it: one line
such as `video:*:44:` followed by the members, separated by commas (nothing
after the last `:` when there are none).

| If you see | Do this |
|---|---|
| `exit=0`, then one line starting `video:` | go on |
| anything else | stop, report the output, and end with FAILED |

`-m` adds USERNAME to the members the group already has (it removes none).
Run:

    pw groupmod video -m USERNAME; echo "exit=$?"; pw groupshow video | cut -d: -f4 | tr ',' '\n' | grep -qx USERNAME; echo "member=$?"

| If you see | Do this |
|---|---|
| `exit=0`, then `member=0` | done |
| anything else | stop, report the output, and end with FAILED |

Report that X.org is installed (the `X.Org X Server` version) and that
USERNAME is in the group `video`. The change takes effect the next time
USERNAME logs in.

## Undo

Check whether USERNAME was in the group before step 6:

    if [ -f /root/xorg-install-video-before.txt ]; then cut -d: -f4 /root/xorg-install-video-before.txt | tr ',' '\n' | grep -qx USERNAME; echo "exit=$?"; else echo "no record"; fi

| If you see | Do this |
|---|---|
| `exit=1` | USERNAME was not a member before: take them out again with `pw groupmod video -d USERNAME; echo "exit=$?"` |
| `exit=0` | USERNAME was already a member: leave the group as it is |
| `no record` (step 6 was not reached), or anything else | leave the group as it is |

Only if step 4 installed xorg (not if step 3 found it already installed),
remove it and the packages it brought:

    pkg delete -y xorg; echo "exit=$?"
    pkg autoremove -n; echo "exit=$?"

`pkg autoremove -n` only lists what it would remove. If every package it
lists is also in the `New packages to be INSTALLED:` list in
`/root/xorg-install.log` (from step 4), run
`pkg autoremove -y; echo "exit=$?"`. If any is not, do not: that package was not
installed by this skill, so removing it is not part of this Undo; stop and
report the list.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-28, snapshot 20260921 (a6deeaa2fb3b) |  |
| 15.1-RELEASE | verified | 2026-09-28 |  |
| 15.0-RELEASE | verified | 2026-09-28 | Also tried by hand. |
| 14.5-RELEASE | verified | 2026-09-28 |  |
| 14.4-RELEASE | verified | 2026-09-28 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.2-RELEASE (EoL) | verified | 2026-09-28 | Packages built for 14.4; they install and run. |
| 14.1-RELEASE (EoL) | verified | 2026-09-28 | As 14.2. |
| 14.0-RELEASE (EoL) | verified | 2026-09-28 | As 14.2. |

## Weak-model check

2026-09-28 (UTC): claude-haiku-4-5, given only this skill, the input
`USERNAME=hbx` (not the skill's example), and a tool that runs one command
on the test machine, followed it on a freshly reset system of every release
above (pkg installed and the account `hbx` created beforehand). A run counts
only when the model said DONE AND the independent check (`verify.sh`: pkg
lists `xorg` as installed, `/usr/local/bin/Xorg -version` exits 0 and prints
an `X.Org X Server` line, and `hbx` is a member of `video`) passed: all 9
did. (The check on Xorg's exit status was added after these runs; run
afterwards on each of the 9 systems the model had set up, the final
`verify.sh` passed on all of them.)

## Not verified

- Tried by hand on 15.0 (2026-09-28): 189 packages, 414 MB downloaded, about
  70 seconds; `pw groupmod video -m` added a second user without removing
  the first, `-d` removed only the one named, and a user that does not exist
  gives `pw: user ... does not exist` with exit status 67.
- Starting X (`startx` from `xinit`, or a display manager) was not tried: the
  test machines have no graphics device or screen. The check stops at the X
  server program answering `-version`.
- `Xorg -version` can start its output with an empty line, so step 5 picks
  out the `X.Org X Server` line rather than the first line.
- Undo was not tried.
- The smaller `xorg-minimal` package, and building X.org from the ports tree,
  are not part of this skill.

## Differences from the Handbook

- The Handbook runs `pkg install xorg` and answers pkg's question by hand;
  without a terminal that is not possible, so this skill uses `-y`.
- The skill checks the user exists and that the X server program is present
  and reports its version, which the Handbook leaves out.

## Source

FreeBSD Handbook, "Installing The X.org Server",
https://docs.freebsd.org/en/books/handbook/x11/#x-install
