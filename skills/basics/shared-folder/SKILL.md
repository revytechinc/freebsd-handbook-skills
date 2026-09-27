---
name: basics-shared-folder
description: Create a folder under /home that the members of one group can all add files to, where each member can delete only their own files (the sticky bit) and nobody else can look in.
handbook: basics/#permissions
handbook_commit: bdf18a0458
---

# Create a shared folder for a group

## What this does

Creates the folder `/home/NAME`, owned by root and by the group `GROUP`, with
the permissions `1770`:

- `770`: the group's members may list the folder and add files to it;
  everybody else may not even look in.
- `1` (the *sticky bit*, shown by `ls -l` as a `T` at the end): a member may
  delete or rename only the files they own, not the other members' files.
  This is what the Handbook shows for `/tmp`.

New files in the folder automatically get the group `GROUP` (on FreeBSD a
new file always takes its folder's group). Whether other members can read or
change a file then depends on that file's own permissions.

## Before you start

- You need: a root shell, and an existing group whose members are the people
  who will share the folder (skill `basics/groups-add`).
- This changes: creates one empty folder. Nothing else.
- Time: seconds.
- Risk: low. Undo removes the folder while it is still empty.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `NAME` | the new folder's name, under `/home` | `projects` |
| `GROUP` | the group that will share it | `teamtwo` |

Everywhere below, replace `NAME` and `GROUP` with these values, exactly as
given. Check them first: each is 1 to 16 characters, starts with a lower-case
letter, and has only lower-case letters `a`-`z`, digits and `_` after that.
If either does not, stop and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24) | go to step 2. The steps are the same on every release |
| anything else | stop, and report the line: this skill was not tested there |

## Step 2: Check the group

Run:

    g=$(pw groupshow GROUP) && echo "group ok"; printf '%s\n' "$g" | awk -F: '{print "gid=" $3; print "members=" $4}'

| If you see | Do this |
|---|---|
| `group ok`, then `gid=` a number from 1000 to 60000, then a `members=` line | go to step 3. The names after `members=` are the people who will share the folder |
| `gid=` any other number (such as `0` for `wheel`) | a system group. Stop, and report it: this skill does not make folders for system groups |
| `pw: unknown group` and no `group ok` | there is no such group. Stop, and report it (skill `basics/groups-add` makes one) |
| anything else | stop, and report the full output |

## Step 3: Check the name is free

The name must not be a user account's: an existing account of that name
probably has `/home/NAME` as its home, and an account added later with
`pw useradd -m` would take the folder over as its home (see skill
`basics/users-add`). Run:

    ls -ld /home /home/NAME; echo "exit=$?"; pw usershow NAME; echo "user=$?"

Expected (with `NAME` filled in, the first line's date and size differ):

    ls: /home/NAME: No such file or directory
    drwxr-xr-x  5 root wheel 512 Sep 27 09:10 /home
    exit=1
    pw: no such user `NAME'
    user=67

| If you see | Do this |
|---|---|
| those lines: a `/home` line starting with `d` and owned by `root`, `/home/NAME: No such file or directory`, `exit=1`, `pw: no such user`, `user=67` (the error lines may come in a different order) | go to step 4 |
| a line ending in `/home/NAME` | the folder already exists. Stop, and report it: this skill does not change existing folders |
| `user=0` | a user account of that name exists. Stop, and report it |
| the `/home` line starts with `l` (a link, such as `-> /usr/home`) | not tested on such a system. Stop, and report it |
| anything else | stop, and report the full output |

## Step 4: Create the folder

`mkdir` refuses a folder that already exists, and `-m 1770` gives the new
one its permissions straight away. Run:

    mkdir -m 1770 /home/NAME && chown root:GROUP /home/NAME; echo "exit=$?"

Expected: only `exit=0`. Anything else: stop, report the output, and end with
FAILED (if the folder was created, say that Undo removes it).

## Step 5: Verify

Run:

    stat -f "type=%HT mode=%Mp%03Lp owner=%Su group=%Sg" /home/NAME; ls -ld /home/NAME

Expected (for `GROUP` `teamtwo`):

    type=Directory mode=1770 owner=root group=teamtwo
    drwxrwx--T  2 root teamtwo 512 Sep 27 09:12 /home/projects

Otherwise stop, report the output, and end with FAILED: say that Undo removes
the folder.

Report the folder, and that the group's members can use it from their next
login (programs already running keep their old groups).

## Undo

Only if step 4 created the folder. `rmdir` removes it only while it is empty;
if members have put files in it, they must be moved out first:

    rmdir /home/NAME; echo "exit=$?"

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-27, snapshot 20260921 (a6deeaa2fb3b) | Also tried by hand (see below). |
| 15.1-RELEASE | verified | 2026-09-27 |  |
| 15.0-RELEASE | verified | 2026-09-27 |  |
| 14.5-RELEASE | verified | 2026-09-27 |  |
| 14.4-RELEASE | verified | 2026-09-27 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-27 |  |
| 14.2-RELEASE (EoL) | verified | 2026-09-27 |  |
| 14.1-RELEASE (EoL) | verified | 2026-09-27 |  |
| 14.0-RELEASE (EoL) | verified | 2026-09-27 | Also tried by hand on ZFS. |

## Weak-model check

2026-09-27 (UTC): claude-haiku-4-5, given only this skill, the inputs
`NAME=hbproj`, `GROUP=hbshare` (not the skill's example), and a tool that runs
one command on the test machine, followed it on a freshly reset system of
every release above (UFS), where `hbshare` had two members and a third
account was not a member. A run counts only when the model said DONE AND the
independent check (`verify.sh`: `/home/hbproj` is a folder with mode `1770`,
owner root and group `hbshare`; each member can create a file there, which
gets the group `hbshare`; one member cannot delete the other's file; the
non-member cannot list the folder) passed: all 9 did, with this version of
the skill and scripts. The command logs show exactly the skill's commands on
every release.

## Not verified

- Tried by hand on 16.0 (UFS) and 14.0 (ZFS): a member's new file gets the
  folder's group; another member gets `Operation not permitted` deleting it;
  a non-member gets `Permission denied` listing the folder; a second
  `mkdir` of the same folder gives `File exists`; `rmdir` of a folder with
  files gives `Directory not empty`.
- The stops in steps 2 and 3 were not tried by the model.
- A system where `/home` is a link to `/usr/home` was not tried; step 3 stops
  there.

## Differences from the Handbook

- The Handbook shows the sticky bit only on `/tmp` (`chmod 1777 /tmp`). The
  skill applies it to a group's folder, with `1770` so that only the group's
  members can use it.

## Source

FreeBSD Handbook, "The setuid, setgid, and sticky Permissions" (in
"Permissions"), https://docs.freebsd.org/en/books/handbook/basics/#permissions
