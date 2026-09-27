---
name: basics-file-protect
description: Protect one file in a user's home folder from being deleted or renamed, even by its owner, with the system undeletable flag (sunlink), and remove the protection again.
handbook: basics/#permissions
handbook_commit: bdf18a0458
---

# Protect a file from deletion

## What this does

Sets the *system undeletable* flag (`sunlnk`) on one file in a user's home
folder. After that, nobody can delete or rename the file, not even its owner;
only root can take the flag off again. The file's content can still be
changed, so this is no replacement for a backup.

The flag can only be taken off while the system's *securelevel* is `0` or
lower. Above that, it stays until the system is restarted with a lower
securelevel, so the skill checks the securelevel first.

## Before you start

- You need: a root shell.
- This changes: the flags of that one file. Nothing else.
- Time: seconds.
- Risk: low. Undo takes the flag off again.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `FILE` | the full path of the file | `/home/jru/thesis.pdf` |

Everywhere below, replace `FILE` with this value, exactly as given. Check it
first: it is `/home/`, then the owner's login name (which starts with a
lower-case letter and has only lower-case letters `a`-`z`, digits and `_`
after that), then `/`, then the file's name (1 to 64 characters: letters,
digits and the characters `.` `_` `-`, not starting with `.` or `-`). So the
file is directly in the home folder, not in a folder inside it. If it does
not, stop and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24) | go to step 2. The steps are the same on every release |
| anything else | stop, and report the line: this skill was not tested there |

## Step 2: Check the securelevel

Run:

    sysctl -n kern.securelevel

| If you see | Do this |
|---|---|
| `-1` or `0` | go to step 3 |
| `1`, `2` or `3` | the flag could be set but not taken off again without a restart. Stop, and report it |
| anything else | stop, and report the full output |

## Step 3: Look at the file

Run:

    stat -f "type=%HT owner=%Su uid=%u flags=%Sf" FILE; echo "exit=$?"; realpath FILE

Expected, such as:

    type=Regular File owner=jru uid=1001 flags=-
    exit=0
    /home/jru/thesis.pdf

| If you see | Do this |
|---|---|
| `type=Regular File`, `owner=` the login name in `FILE`, `uid=` a number from 1000 to 60000, `flags=` without `sunlnk` in it (such as `-`, or `uarch` on ZFS), then `exit=0`, then `FILE` again exactly | go to step 4 |
| `flags=` with `sunlnk` in it | the file is already protected. Stop, and report it: nothing needs doing |
| the last line is `FILE` with `/usr/home/` in place of `/home/` at the start, and the rest as in the first row | on this system `/home` is a link to `/usr/home`. Use that last line as `FILE` from now on, and run this step again |
| `type=Symbolic Link` or another type, or the last line is any other path | `FILE` is not a plain file in that home folder. Stop, and report the output |
| `owner=` any other name, or `uid=` any other number | the file does not belong to the owner of that home folder, or belongs to a system account. Stop, and report it |
| `No such file or directory` | there is no such file. Stop, and report it |
| anything else | stop, and report the full output |

## Step 4: Set the flag

`-h` makes `chflags` flag a link itself rather than what it points to, in case
the file was swapped for a link in the meantime. Run:

    chflags -h sunlink FILE; echo "exit=$?"

Expected: only `exit=0`. Anything else: stop, report the output, and end with
FAILED.

## Step 5: Verify

Run:

    stat -f "type=%HT owner=%Su uid=%u flags=%Sf" FILE; ls -lo FILE

Expected: the same `type=`, `owner=` and `uid=` as in step 3, and `flags=`
now with `sunlnk` in it (such as `flags=sunlnk`, or `flags=sunlnk,uarch` on
ZFS); the `ls` line shows the same flags before the size, such as:

    -rw-r--r--  1 jru jru sunlnk 48213 Sep 27 09:10 /home/jru/thesis.pdf

Otherwise stop, report the output, and end with FAILED: say that Undo takes
the flag off.

Report that the file is protected, and that it must be unprotected (Undo)
before it can be deleted or renamed.

## Undo

Only if step 4 showed `exit=0`, and while `sysctl -n kern.securelevel` still
shows `-1` or `0`:

    chflags -h nosunlink FILE; echo "exit=$?"

Expected: `exit=0`, and `stat -f "flags=%Sf" FILE` no longer shows `sunlnk`.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-27, snapshot 20260921 (a6deeaa2fb3b) | Also tried by hand on ZFS (`flags=sunlnk,uarch`), with Undo, and at securelevel 1 (see below). |
| 15.1-RELEASE | verified | 2026-09-27 |  |
| 15.0-RELEASE | verified | 2026-09-27 |  |
| 14.5-RELEASE | verified | 2026-09-27 |  |
| 14.4-RELEASE | verified | 2026-09-27 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-27 |  |
| 14.2-RELEASE (EoL) | verified | 2026-09-27 |  |
| 14.1-RELEASE (EoL) | verified | 2026-09-27 |  |
| 14.0-RELEASE (EoL) | verified | 2026-09-27 | Also tried by hand on ZFS, with Undo. |

## Weak-model check

2026-09-27 (UTC): claude-haiku-4-5, given only this skill, the input
`FILE=/home/hbtest6/contract.txt` (not the skill's example), and a tool that
runs one command on the test machine, followed it on a freshly reset system of
every release above (UFS). A run counts only when the model said DONE AND the
independent check (`verify.sh`: the file has `sunlnk` added to the flags it
had, the same mode, owner and content, no other file in the home folder has
`sunlnk`, the securelevel is still `-1`, and renaming the file fails) passed:
all 9 did, with this version of the skill and scripts. The command logs show
exactly the skill's commands on every release.

## Not verified

- Tried by hand on 16.0 at securelevel 1: `chflags sunlink` still works, but
  `chflags nosunlink` gives `Operation not permitted`, and the securelevel
  cannot be lowered without a restart. That is why step 2 stops above `0`.
  The model was not tested on that stop or on step 3's stops.
- Tried by hand on 16.0 (UFS and ZFS) and 14.0 (ZFS): with the flag set, `rm`
  and `mv` give `Operation not permitted`, while adding to the file and
  `chmod` still work.
- Other flags the Handbook mentions only by reference (such as `schg`, which
  also stops changes to the content) are not part of this skill.

## Differences from the Handbook

- The Handbook shows `chflags sunlink file1` and `chflags nosunlink file1`
  without conditions. The skill adds `-h`, keeps to plain files directly in
  a home folder, and checks the securelevel first, because at securelevel 1
  or higher the flag cannot be taken off.

## Source

FreeBSD Handbook, "FreeBSD File Flags" (in "Permissions"),
https://docs.freebsd.org/en/books/handbook/basics/#permissions
