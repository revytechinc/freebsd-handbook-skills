---
name: basics-permissions-set
description: Set who may read or run one file or folder in a user's home folder, as three permission digits (change rights only for the owner), showing the old setting so it can be undone.
handbook: basics/#permissions
handbook_commit: bdf18a0458
---

# Set a file's permissions

## What this does

Sets the permissions of one file or folder inside a home folder: whether its
owner, its group, and everyone else may read it, change it, or run it (for a
folder: list it, add or remove files in it, and enter it). The permissions are
given as three digits, one each for the owner, the group and everyone else:

| Digit | Means | Shown by `ls -l` as |
|---|---|---|
| `0` | nothing | `---` |
| `4` | read | `r--` |
| `5` | read and run (for a folder: read and enter) | `r-x` |
| `6` | read and change | `rw-` |
| `7` | read, change and run (for a folder: everything) | `rwx` |

(`1`, `2` and `3` are the rarely used run-only, change-only, and change-and-run.)
So `600` lets only the owner read and change a file; `644` lets everyone read
it; `700` keeps a folder to its owner alone. This skill only gives change
rights to the owner. The old permissions are shown
first, so the change can be undone.

## Before you start

- You need: a root shell.
- This changes: the permissions of that one file or folder. Not its content,
  not its owner, and nothing inside a folder.
- Time: seconds.
- Risk: low. Undo puts the old permissions back.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `FILE` | the full path of the file or folder | `/home/jru/notes.txt` |
| `MODE` | the new permissions, as three digits | `640` |

Everywhere below, replace `FILE` and `MODE` with these values, exactly as
given. Check them first:

- `FILE`: starts with `/home/` or `/usr/home/`, then the owner's login name
  (the home folder: it starts with a lower-case letter and has only
  lower-case letters `a`-`z`, digits and `_` after that), then `/` and the rest of the path; only letters, digits
  and the characters `/` `.` `_` `-`; does not contain `..`, `//` or `/./`,
  and does not end with `/` or `/.`. (So the home folder itself is not a
  target, only what is inside it.) These rules keep the path inside that home
  folder.
- `MODE`: exactly three digits; the first is from `0` to `7`, and the second
  and third are each `0`, `1`, `4` or `5`. (This skill does not let the group
  or everyone change a file: `2`, `3`, `6` or `7` there would.)

If either does not, stop and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24) | go to step 2. The steps are the same on every release |
| anything else | stop, and report the line: this skill was not tested there |

## Step 2: Look at the file

Run:

    stat -f "mode=%Mp%03Lp type=%HT owner=%Su uid=%u group=%Sg" FILE; echo "exit=$?"; realpath FILE

Expected, such as:

    mode=0644 type=Regular File owner=jru uid=1001 group=jru
    exit=0
    /home/jru/notes.txt

| If you see | Do this |
|---|---|
| `mode=0` followed by three digits, `type=Regular File` or `type=Directory`, `owner=` the login name in `FILE` (the part after `/home/` or `/usr/home/`, up to the next `/`), `uid=` a number from 1000 to 60000, `group=` the same login name, then `exit=0`, then `FILE` again exactly | write down the three digits after `mode=0`: they are the old permissions, needed for Undo. Go to step 3 |
| `mode=` followed by four digits whose first is not `0` (such as `mode=4755`) | the file has special permissions (setuid, setgid or sticky) that this skill would remove. Stop, and report it |
| the last line is `FILE` with `/usr/home/` in place of `/home/` at the start, and the rest as in the first row | on this system `/home` is a link to `/usr/home`. Use that last line as `FILE` from now on, and run this step again |
| `type=Symbolic Link`, or the last line is any other path | `FILE` is, or passes through, a link to somewhere else. Stop, and report both paths |
| `owner=` any other name | the file does not belong to the owner of that home folder. Stop, and report it |
| `uid=` any other number (such as `0` for root) | a system account's file. Stop, and report it: this skill does not change them |
| `group=` any other name (such as `wheel`) | the file belongs to a group other than the owner's own, whose members the middle digit would let read it. Stop, and report it |
| `No such file or directory` | there is no such file. Stop, and report it |
| anything else (such as another `type=`) | stop, and report the full output |

## Step 3: Set the permissions

The change is made as the file's owner (OWNER below: the login name from
`FILE`, the same as `owner=` in step 2), not as root. The owner may change
their own files' permissions anyway, and the system then refuses to change
any file the owner does not own, even if a file or folder on the path is
swapped for a link while the skill runs. `-h` makes `chmod` change a link itself rather than
what it points to. `env -i` starts it with an empty environment, so none of
root's settings are handed to the owner's process. Run:

    env -i PATH=/sbin:/bin:/usr/sbin:/usr/bin su -m OWNER -c 'chmod -h MODE FILE'; echo "exit=$?"

Expected: only `exit=0`. Anything else (such as `Operation not permitted`
and `exit=1`): stop, report the output, and end with FAILED.

## Step 4: Verify

Run:

    stat -f "mode=%Mp%03Lp type=%HT owner=%Su uid=%u group=%Sg" FILE; ls -ld FILE; realpath FILE

Expected: `mode=0MODE` (with `MODE` filled in, such as `mode=0640`), the
same `type=`, `owner=`, `uid=` and `group=` as in step 2, then the `ls` line
whose first characters show the new permissions (such as `-rw-r-----` for
`640`), then `FILE` again exactly.
Otherwise stop, report the output, and end with FAILED: step 3 may have
changed something, so say that Undo puts the old permissions back.

## Undo

Only if step 3 showed `exit=0`: put back the three digits written down in step
2 (OLDMODE below):

    env -i PATH=/sbin:/bin:/usr/sbin:/usr/bin su -m OWNER -c 'chmod -h OLDMODE FILE'; echo "exit=$?"

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-27, snapshot 20260921 (a6deeaa2fb3b) |  |
| 15.1-RELEASE | verified | 2026-09-27 |  |
| 15.0-RELEASE | verified | 2026-09-27 |  |
| 14.5-RELEASE | verified | 2026-09-27 |  |
| 14.4-RELEASE | verified | 2026-09-27 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-27 |  |
| 14.2-RELEASE (EoL) | verified | 2026-09-27 |  |
| 14.1-RELEASE (EoL) | verified | 2026-09-27 |  |
| 14.0-RELEASE (EoL) | verified | 2026-09-27 |  |

## Weak-model check

2026-09-27 (UTC): claude-haiku-4-5, given only this skill, the inputs
`FILE=/home/hbtest5/notes.txt`, `MODE=600` (not the skill's example), and a
tool that runs one command on the test machine, followed it on a freshly reset
system of every release above, where the file was readable by everyone
(`644`). A run counts only when the model said DONE AND the independent check
(`verify.sh`: the file is `0600`, with the same owner, group and content, and
nothing else in the home folder changed permissions, owner or group) passed:
all 9 did, with this version of the skill and scripts. The command logs show
exactly the skill's commands on every release.

## Not verified

- Folders were not tried by the model (only a file). Changing a folder's
  permissions with this skill does not change the files inside it.
- The stops in step 2 were tried by hand on 16.0 (a setuid file, a link, a
  path through a linked folder, a file owned by root, which shows `uid=0`, and
  a missing file); the
  model was not tested on them. Tried by hand on 16.0 and 14.0: step 3's command works
  when the owner's shell is `/usr/sbin/nologin`, and the owner's process sees
  only `PATH` and `PWD` in its environment; when a folder on the path is
  swapped for a link to `/etc`, it gives `Operation not permitted` and
  `exit=1`. On 16.0: when the owner swaps `FILE` itself for a link to
  `/etc/master.passwd`, it gives `exit=0` but changes only the link, and step
  4 then shows `type=Symbolic Link` and stops. `/etc/master.passwd` was
  unchanged every time.
- A system where `/home` is a link to `/usr/home` was not tried.
- A home folder itself (such as `/home/jru`) is not a target of this skill.
- Files outside home folders, and the Handbook's letter forms (such as
  `chmod go-w,a+x FILE`), are not part of this skill.

## Differences from the Handbook

- `stat -f %Lp` does not print leading zeros (`040` for `0040`); the skill
  uses `%03Lp`, which does (tried on 16.0 and 14.0).
- The Handbook explains the permission digits and letters, and shows `chmod`
  with both. The skill uses only the digits (with `-h`, run as the file's
  owner), for one file or folder in a home folder, owned by that folder's
  user, and refuses changes that would let the group or everyone change a file or that
  would silently remove special permissions.

## Source

FreeBSD Handbook, "Permissions",
https://docs.freebsd.org/en/books/handbook/basics/#permissions
