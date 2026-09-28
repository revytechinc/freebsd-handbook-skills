---
name: basics-user-editor
description: Change which text editor a user's programs open by default (the EDITOR environment variable), in the user's own startup files for sh and csh.
handbook: basics/#shell-env-vars
handbook_commit: bdf18a0458
---

# Set a user's default editor

## What this does

Many programs (such as `crontab -e`, `chpass` and `git`) open the editor named
in the *environment variable* `EDITOR` when they need text typed in. A new
account's startup files set it to `vi`: `.profile` for the shell `sh`, and
`.cshrc` for `csh` and `tcsh`. This skill changes that one line in both
files to another installed editor, such as `ee` (the easier editor that comes
with FreeBSD), so it applies whichever of those shells the user logs in with.

## Before you start

- You need: a root shell, and the editor installed as a program file (`ee`
  and `vi` always are; others come from packages, skill `ports/pkg-install`;
  an editor installed as a symbolic link is refused: give the path of the
  file it points to).
- This changes: the `EDITOR` line in the user's `.profile` and `.cshrc`.
  Nothing else in them.
- Time: seconds.
- Risk: low. Undo puts the old editor back.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `USER` | the login name of the account | `jru` |
| `EDITORPATH` | the full path of the editor | `/usr/local/bin/nano` |

Everywhere below, replace `USER` and `EDITORPATH` with these values, exactly
as given. Check them first:

- `USER`: 1 to 16 characters; starts with a lower-case letter; only
  lower-case letters `a`-`z`, digits and `_` after that.
- `EDITORPATH`: `/usr/bin/`, `/usr/local/bin/` or `/bin/`, followed by 1 to
  32 letters, digits or the characters `.` `_` `-` (and nothing else; not
  just `.` or `..`).

If either does not, stop and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24) | go to step 2. The steps are the same on every release |
| anything else | stop, and report the line: this skill was not tested there |

## Step 2: Check the account and the editor

Run:

    u=$(pw usershow USER) && echo "user ok"; printf '%s\n' "$u" | awk -F: '{print "uid=" $3; print "home=" $9; print "shell=" $10}'; env -i PATH=/bin:/usr/bin su -m USER -c 'test ! -L EDITORPATH || exit 5; test -f EDITORPATH || exit 3; test -x EDITORPATH || exit 4'; echo "exec=$?"

| If you see | Do this |
|---|---|
| `user ok`, `uid=` a number from 1000 to 60000, `home=/home/USER`, `shell=/bin/sh`, `shell=/bin/csh` or `shell=/bin/tcsh`, then `exec=0` | go to step 3 |
| any other `shell=` (such as `/usr/sbin/nologin` or `/usr/local/bin/bash`) | the account does not log in with a shell whose startup files this skill changes. Stop, and report it |
| `uid=` any other number | a system account. Stop, and report it |
| another `home=` | the account's home is not `/home/USER`. Stop, and report it |
| `pw: no such user` and no `user ok` | there is no such account. Stop, and report it |
| `exec=3` | there is no such file: the editor is not installed there. Stop, and report it |
| `exec=4` | the user may not run it. Stop, and report it |
| `exec=5` | it is a symbolic link. Stop, and report it with the path of the file it points to (`realpath EDITORPATH`): the skill can be run again with that path if it is in one of the three folders |
| another `exec=` number | `su` could not switch to the user (for example a locked or expired account). Stop, and report the output |
| anything else | stop, and report the full output |

## Step 3: Look at the EDITOR lines

This looks for `EDITOR` in all four of the account's usual startup files (as
the user, so a link cannot show root any file the user could not read), and
shows who owns the two that will be changed. Run:

    env -i PATH=/bin:/usr/bin su -m USER -c 'grep -n EDITOR /home/USER/.profile /home/USER/.shrc /home/USER/.cshrc /home/USER/.login'; echo "grep=$?"; stat -f "owner=%Su type=%HT %N" /home/USER/.profile /home/USER/.cshrc

Expected, such as:

    /home/jru/.profile:16:EDITOR=vi;   	export EDITOR
    /home/jru/.cshrc:20:setenv	EDITOR	vi
    grep=0
    owner=jru type=Regular File /home/jru/.profile
    owner=jru type=Regular File /home/jru/.cshrc

| If you see | Do this |
|---|---|
| exactly two `EDITOR` lines: one `/home/USER/.profile:NUMBER:EDITOR=OLD;` followed by `export EDITOR` (spaces or tabs between), and one `/home/USER/.cshrc:NUMBER:setenv EDITOR OLD` (spaces or tabs between), with the same OLD in both; then `grep=0`; then `owner=USER type=Regular File` for both files; and OLD is 1 to 64 characters of only letters, digits and `/` `.` `_` `-` | write down OLD (such as `vi`): Undo needs it. Go to step 4 |
| OLD has any other character (such as `$`, `"`, `;` or a space) | Undo could not safely put it back. Stop, and report it: change the files by hand |
| any other `EDITOR` line, in any of the four files (such as an indented one, a second one, or one in `.shrc` or `.login`), or two different OLD values | the user's startup files are not the usual ones: changing one line might not change the editor the user gets. Stop, and report the lines: they have to be changed by hand |
| `owner=` another name, or a `type=` other than `Regular File` (such as `Symbolic Link`), for either file | the file does not belong to the user, or is a link to another file. Stop, and report it |
| `No such file or directory`, or `grep=1` | the startup files are not the usual ones. Stop, and report the output |
| anything else | stop, and report the full output |

## Step 4: Change the lines

The change is made with the user's rights (with `su`), so their files stay
theirs, and only these lines change. (The command line itself is read by
root's login shell; it works with `sh` and `tcsh`, the two root shells
FreeBSD uses.) Run:

    env -i PATH=/bin:/usr/bin su -m USER -c "sed -i '' 's|^EDITOR=[^;]*;|EDITOR=EDITORPATH;|' /home/USER/.profile && sed -i '' -E 's|^setenv([[:space:]]+)EDITOR([[:space:]]+).*|setenv\1EDITOR\2EDITORPATH|' /home/USER/.cshrc"; echo "exit=$?"

Expected: only `exit=0` (this does not yet show that the lines changed: step
5 checks that). Anything else: stop, report the output, and end with
FAILED (the first file may already be changed: say that Undo puts the old
editor back in both).

## Step 5: Verify

The last command starts a login shell of the user, as a login would, and in
it runs `printenv`, a separate program, which prints the `EDITOR` that
programs started from that shell receive. Run:

    env -i PATH=/bin:/usr/bin su -m USER -c "grep '^EDITOR=' /home/USER/.profile; grep -E '^setenv[[:space:]]+EDITOR[[:space:]]' /home/USER/.cshrc"; stat -f "owner=%Su %N" /home/USER/.profile /home/USER/.cshrc; su -l USER -c '/usr/bin/printenv EDITOR' </dev/null | tail -n 1

Expected: `EDITOR=EDITORPATH;` followed by `export EDITOR`, then `setenv`,
`EDITOR` and `EDITORPATH`, then `owner=USER` for both files, then
`EDITORPATH` on its own line. Otherwise stop, report the output, and end with FAILED (say
that Undo puts the old editor back).

Report that the user gets the new editor from their next login.

## Undo

Only if step 4 was run (whatever it showed): run step 4's command again with
OLD (the editor written down in step 3, such as `vi`, which step 3 checked is
safe to use) in place of `EDITORPATH`.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-28, snapshot 20260921 (a6deeaa2fb3b) |  |
| 15.1-RELEASE | verified | 2026-09-28 |  |
| 15.0-RELEASE | verified | 2026-09-28 |  |
| 14.5-RELEASE | verified | 2026-09-28 |  |
| 14.4-RELEASE | verified | 2026-09-28 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.2-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.1-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.0-RELEASE (EoL) | verified | 2026-09-28 |  |

## Weak-model check

2026-09-28 (UTC): claude-haiku-4-5, given only this skill, the inputs
`USER=hbtest9`, `EDITORPATH=/usr/bin/ee` (not the skill's example), and a
tool that runs one command on the test machine, followed it on a freshly
reset system of every release above (UFS), for a new account with the
default startup files. A run counts only when the model said DONE AND the
independent check (`verify.sh`: a login shell of the user sees
`EDITOR=/usr/bin/ee`, and so does `csh` reading `.cshrc`; the rest of both
files, and their owner, group and mode, are unchanged) passed: all 9 did,
with this version of the skill and scripts. The command logs show exactly
the skill's commands on every release.

## Not verified

- Tried by hand on 16.0 and 14.0: a new account's `.profile` has
  `EDITOR=vi;` followed by `export EDITOR` (line 16), and `.cshrc` has
  `setenv EDITOR vi` (line 20).
- Tried by hand on 16.0: in step 2, a missing editor gives `exec=3`, an
  editor only root can run (mode `700`) gives `exec=4` (the test runs as the
  user), a symbolic link gives `exec=5`, and a locked account gives
  `su: Sorry` and `exec=1`.
- Tried by hand on 16.0 for accounts whose login shell is `csh` and `tcsh`:
  steps 4 and 5 worked, and their login shells' `printenv` showed the new
  editor. The model was tested with an `sh` account only.
- Tried by hand on 16.0: step 4's command, Undo (back to `vi`), and step 4
  again with root's login shell set to `tcsh` (the default before 14.0) all
  worked. The model did not run Undo.
- Other shells (such as `bash` or `zsh`, which read other startup files) are
  not covered.

## Differences from the Handbook

- The Handbook shows setting `EDITOR` for the current session only
  (`setenv EDITOR ...` in csh, `export EDITOR=...` in sh). The skill changes
  the line the account's startup files already have, so it lasts, and does
  it as the user.

## Source

FreeBSD Handbook, "Common Environment Variables" (in "Shells"),
https://docs.freebsd.org/en/books/handbook/basics/#shell-env-vars
