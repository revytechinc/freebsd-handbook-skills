---
name: basics-users-change
description: Change an ordinary user account's full name and login shell, without an editor, keeping the old values so the change can be undone.
handbook: basics/#users-chpass
handbook_commit: bdf18a0458
---

# Change a user's full name and shell

## What this does

Changes two details of one ordinary user account: the full name, and the
*login shell* (the command-line program the user gets when they log in). As a
safety check, the new shell must be one listed in `/etc/shells` (the list of
approved shells that `chpass` and some services, such as `ftpd`, honour). The old values are shown first, so
the change can be undone. System accounts (such as root) are refused: a
wrong shell there can lock the administrator out.

## Before you start

- You need: a root shell.
- This changes: the account's full name and shell in `/etc/master.passwd` and
  `/etc/passwd`. Nothing else about the account changes (its UID, group, home
folder, password, class and expiry dates stay as they were).
- Time: seconds.
- Risk: low. Undo puts the old values back.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `USER` | the login name of the account | `jru` |
| `FULLNAME` | the new full name | `J. Random User` |
| `SHELL` | the new login shell, as a full path | `/bin/csh` |

Everywhere below, replace `USER`, `FULLNAME` and `SHELL` with these values,
exactly as given. Check them first:

- `USER`: 1 to 16 characters; starts with a lower-case letter; only
  lower-case letters `a`-`z`, digits and `_` after that.
- `FULLNAME`: 1 to 40 characters; only letters, digits, spaces and the
  characters `.` and `-`.
- `SHELL`: starts with `/`; only letters, digits and the characters `/` `.`
  `_` `-`.

If any of them does not, stop and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24) | go to step 2. The steps are the same on every release |
| anything else | stop, and report the line: this skill was not tested there |

## Step 2: Look at the account and note the old values

Run:

    u=$(pw usershow USER) && echo "pw ok"; printf '%s\n' "$u" | awk -F: '{print "uid=" $3; print "name=" $8; print "shell=" $10}'

Expected, such as:

    pw ok
    uid=1001
    name=J. Random User
    shell=/bin/sh

Write down the `name=` and `shell=` values: they are the old values, needed
for Undo. The full-name field can also hold office and phone details after
commas; this skill would erase them, so it stops if there are any. It also
stops if the old values could not be put back safely by Undo.

| If you see | Do this |
|---|---|
| `pw ok`, then `uid=` a number from 1000 to 60000, then a `name=` line whose value is empty or has only letters, digits, spaces and the characters `.` `-` `&` `'`, then a `shell=` line whose value follows the rules for `SHELL` | go to step 3 (`User &` is the full name `pw` gives an account when none was set) |
| a `name=` value containing `,` | the account has office or phone details that this skill would erase. Stop, and report it |
| a `name=` or `shell=` value with any other character (such as `$`, `"` or `\`) | Undo could not safely put it back. Stop, and report it: change it by hand instead |
| `uid=` any other number (such as `0` for root) | a system account. Stop, and report it: this skill does not change system accounts |
| `pw: no such user` and no `pw ok` | there is no such account. Stop, and report it |
| anything else | stop, and report the full output |

## Step 3: Check the new shell is allowed

This skill only accepts shells listed in `/etc/shells`, and only if they
exist. Run:

    grep -Fx 'SHELL' /etc/shells; echo "listed=$?"; ls -l SHELL; echo "installed=$?"

| If you see | Do this |
|---|---|
| `SHELL` on a line by itself, `listed=0`, then a line starting `-r-xr-xr-x` (or with `x` in the same places) ending in `SHELL`, `installed=0` | the shell is listed and exists. Go to step 4 |
| `listed=1` | the shell is not listed in `/etc/shells`, so this skill refuses it. Stop, and report it (the shells listed there are shown by `grep -v '^#' /etc/shells`) |
| `listed=0` and `installed=1` | the shell is not installed. Stop, and report it |
| anything else | stop, and report the full output |

## Step 4: Change the full name and shell

The command checks again that the account is an ordinary one (UID 1000 to
60000) and that the shell is listed, installed and not a link, and changes
nothing if any check fails. Run:

    pw usershow USER | awk -F: '$3>=1000 && $3<=60000 {ok=1} END {exit !ok}' && grep -Fqx 'SHELL' /etc/shells && [ -x SHELL ] && [ ! -L SHELL ] && pw usermod -n USER -c "FULLNAME" -s SHELL; echo "exit=$?"

Expected: only `exit=0`. Anything else: stop, report the output, and end with
FAILED (with `exit=1` and no other output, one of the checks failed and
nothing was changed).

## Step 5: Verify

Run:

    pw usershow USER | awk -F: '{print "uid=" $3; print "name=" $8; print "shell=" $10}'

Expected: the same `uid=` as in step 2, then `name=FULLNAME` and
`shell=SHELL` (with the new values filled in). Otherwise stop, report the
output, and end with FAILED: the account was changed, so say that Undo puts
the old values back.

## Undo

Only if step 4 showed `exit=0`: put back the old values written down in step
2 (OLDNAME and OLDSHELL below; step 2 already checked they are safe to put
back, and OLDNAME may be empty). Run:

    pw usermod -n USER -c "OLDNAME" -s OLDSHELL; echo "exit=$?"

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-27, snapshot 20260921 (a6deeaa2fb3b) | Undo also tried by hand, with the old names `User &`, `O'Brien` and empty. |
| 15.1-RELEASE | verified | 2026-09-27 | Also tried by hand; `chpass -s` also works without an editor. |
| 15.0-RELEASE | verified | 2026-09-27 |  |
| 14.5-RELEASE | verified | 2026-09-27 |  |
| 14.4-RELEASE | verified | 2026-09-27 | Undo also tried by hand. |
| 14.3-RELEASE (EoL) | verified | 2026-09-27 |  |
| 14.2-RELEASE (EoL) | verified | 2026-09-27 |  |
| 14.1-RELEASE (EoL) | verified | 2026-09-27 |  |
| 14.0-RELEASE (EoL) | verified | 2026-09-27 | Undo also tried by hand. |

## Weak-model check

2026-09-27 (UTC): claude-haiku-4-5, given only this skill, the inputs
`USER=hbtest3`, `FULLNAME=Changed Name`, `SHELL=/bin/tcsh` (not the skill's
example), and a tool that runs one command on the test machine, followed it
on a freshly reset system of every release above, with the account made
beforehand with no full name given (so `pw` set `User &`) and `/bin/sh`. A run counts only when the model
said DONE AND the independent check (`verify.sh`: the account has the new
full name and shell, its home, primary group and password field are
unchanged, its class and expiry dates are unchanged, and `/etc/shells` and
every other account are unchanged) passed: all 9 did, with this version of the skill and scripts. The
command logs show exactly the skill's commands on every release.

## Not verified

- The stops in steps 2 and 3 were tried by hand on 16.0 only (the model was
  not tested on them), as were step 4's checks (root, an unlisted shell and a
  linked shell each gave `exit=1` without a change): step 2 with `root` shows `uid=0`, with a missing account shows
  `pw: no such user` and no `pw ok`, and with an account made with office and
  phone details shows a `name=` value with commas; step 3 with an unlisted
  shell shows `listed=1`, and with a listed shell removed shows `installed=1`.
- Undo was tried by hand on 16.0, 14.4 and 14.0 only (the account came back
  exactly, and root's entry was unchanged); the model was not asked to run it.

- Shells from packages (such as `/usr/local/bin/zsh`, which the package adds
  to `/etc/shells`) were not tried. A shell installed as a symbolic link
  (`ls -l` shows a line starting `l`) is stopped at step 3.
- The other fields `chpass` shows (office, phones, expiry, class) are not
  part of this skill.
- A user changing their own details (as the Handbook's second example
  shows) is not covered: this skill runs as root.

## Differences from the Handbook

- The Handbook's `chpass` opens an editor with all the account's fields,
  which a model cannot use reliably. The skill uses `pw usermod -c ... -s ...`,
  which changes just the two fields. (`chpass -s SHELL USER` also changes the
  shell without an editor: tried on 15.1.)
- The skill checks the new shell is in `/etc/shells`; the Handbook does not
  mention it. It keeps the account consistent with the list that `chpass`
  enforces when users change their own shell.

## Source

FreeBSD Handbook, "Change user information",
https://docs.freebsd.org/en/books/handbook/basics/#users-chpass
