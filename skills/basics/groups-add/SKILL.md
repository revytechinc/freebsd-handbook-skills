---
name: basics-groups-add
description: Add an ordinary user account to a group, creating the group first if it does not exist, without removing the group's other members.
handbook: basics/#users-groups
handbook_commit: bdf18a0458
---

# Add a user to a group

## What this does

Adds one user account to one group, so the user gets the group's access to
files and folders. If the group does not exist yet, it is created first. The
group's other members stay. System groups (such as `wheel` or `operator`,
which give administrator-like rights) are refused.

## Before you start

- You need: a root shell.
- This changes: `/etc/group` (a new group line, or one more name on an
  existing line). Nothing else.
- Time: seconds.
- Risk: low. Undo takes the user out again, or removes the group if this
  skill created it.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `GROUP` | the group's name | `teamtwo` |
| `USER` | the login name of the account to add | `jru` |

Everywhere below, replace `GROUP` and `USER` with these values, exactly as
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

## Step 2: Check the account

Run:

    u=$(pw usershow USER) && echo "user ok"; printf '%s\n' "$u" | awk -F: '{print "uid=" $3}'

| If you see | Do this |
|---|---|
| `user ok`, then `uid=` a number from 1000 to 60000 | go to step 3 |
| `uid=` any other number (such as `0` for root) | a system account. Stop, and report it: this skill does not change system accounts |
| `pw: no such user` and no `user ok` | there is no such account. Stop, and report it |
| anything else | stop, and report the full output |

## Step 3: Check the group

Run:

    g=$(pw groupshow GROUP) && echo "group ok"; printf '%s\n' "$g" | awk -F: '{print "gid=" $3; print "members=" $4}'; id -Gn USER | tr ' ' '\n' | grep -Fx 'GROUP'; echo "member=$?"

| If you see | Do this |
|---|---|
| `pw: unknown group`, no `group ok`, `gid=` with nothing after it, `members=`, then `member=1` | the group does not exist. Write down: **new**. Go to step 4 |
| `group ok`, then `gid=` a number from 1000 to 60000, a `members=` line, then `member=1` | the group exists and the user is not in it. Write down: **existing**, and the `members=` line. Go to step 5 |
| `GROUP` on a line by itself, then `member=0` | the user is already in the group (it may be the user's own main group). Stop, and report it: nothing needs doing |
| `group ok`, then `gid=` any other number (such as `0` for `wheel` or `5` for `operator`) | a system group. Stop, and report it: this skill does not add members to system groups |
| anything else | stop, and report the full output |

## Step 4: Create the group (only if step 3 said new)

Skip this step if you wrote down **existing**. Run:

    pw groupadd GROUP; echo "exit=$?"

Expected: only `exit=0`. Anything else: stop, report the output, and end with
FAILED.

## Step 5: Add the user

`-m` adds the user to the members already there. (Do not use `-M`: it
replaces the whole member list.) Run:

    pw groupmod GROUP -m USER; echo "exit=$?"

Expected: only `exit=0`. Anything else: stop, report the output, and end with
FAILED (if step 4 created the group, say so: Undo removes it).

## Step 6: Verify

Run:

    pw groupshow GROUP; id -Gn USER

Expected: first a line `GROUP:*:GID:MEMBERS`, where the members are the ones
written down in step 3 (none, for a new group) with `USER` added; then the
user's groups, including `GROUP`. Such as, for a new group `teamtwo`:

    teamtwo:*:1002:jru
    jru teamtwo

Otherwise stop and report. The user gets the new group's access at their next
login; programs already running keep their old groups.

## Undo

If step 4 ran and showed `exit=0` (this skill created the group), remove the
group, whether or not step 5 worked:

    pw groupdel GROUP; echo "exit=$?"

If step 3 said **existing** and step 5 showed `exit=0`, take only this user
out:

    pw groupmod GROUP -d USER; echo "exit=$?"

In any other case, nothing was changed: there is nothing to undo.

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
`GROUP=hbteam`, `USER=hbtest4` (not the skill's example), and a tool that
runs one command on the test machine, followed it on a freshly reset system of
every release above, where the group `hbteam` already existed with one other
member. A run counts only when the model said DONE AND the independent check
(`verify.sh`: `/etc/group` has one `hbteam` line, with its old GID, no
password and exactly the old member and `hbtest4`; `id` shows `hbtest4` in it, and every other group and every account
are unchanged) passed: all 9 did, with this version of the skill and scripts.
The command logs show exactly the skill's commands on every release, without
step 4.

## Not verified

- The stops were tried by hand on 16.0 (and the first two on 14.0 too); the
  model was not tested on them: step 3 with `wheel` shows `gid=0`, and with
  the user's own main group shows the name and `member=0`; step 2 with `root`
  shows `uid=0`, and with a missing account shows `pw: no such user` and no
  `user ok`.

- The path for a new group (steps 4 and 5, and Undo with `pw groupdel`) was
  tried by hand on 16.0 and 14.0 only; the model was tested on an existing
  group.
- Tried by hand on 16.0 and 14.0: `pw groupmod -m` does not add a name twice,
  and `pw groupmod -d` exits 0 even when the user was not a member. That is
  why Undo takes a user out only after this skill added them.
- Group passwords (`pw groupmod -h`, `newgrp`) are not part of this skill.

## Differences from the Handbook

- The Handbook's `pw groupmod teamtwo -M jru` replaces the group's whole
  member list; the skill uses `-m`, which the Handbook shows next, so no
  existing member is removed.
- The skill refuses system groups, following the Handbook's warning about
  `operator`.

## Source

FreeBSD Handbook, "Managing Groups",
https://docs.freebsd.org/en/books/handbook/basics/#users-groups
