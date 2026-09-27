---
name: basics-users-remove
description: Remove a regular user account completely - its home folder, mail, scheduled jobs and running programs - after checking it is not a system account.
handbook: basics/#users-rmuser
handbook_commit: bdf18a0458
---

# Remove a user account

## What this does

Removes one regular user account with `rmuser`, which in one go: removes the
user's scheduled jobs (crontab and `at` jobs), stops every program running
under the user's number (UID), removes the account, its home folder, its
mail, its files in `/tmp` and `/var/tmp`, and its membership of every group
(and its own group, if nothing else is in it).

`rmuser` works by the UID and walks the whole home folder: it deletes every
file the UID owns there and every symbolic link there, whoever owns it. So
the skill first makes sure the account is an ordinary one: a UID from 1000 to
60000, used by no other account, and a home folder that is exactly
`/home/USER`, a real folder owned by the user, with nothing else mounted
inside it (`rmuser` would walk into a mounted filesystem too). Anything
else, it refuses.

**This cannot be undone** (except from a snapshot or a backup made
beforehand). Every file the user owns in the home folder is deleted, every
symbolic link there too, and on ZFS 14.2 and later the whole home dataset.
If any of it is needed, copy it somewhere else first.

## Before you start

- You need: a root shell.
- This changes: deletes the account and everything listed above.
- Time: seconds.
- Risk: high for the user's data: nothing is kept.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `USER` | the login name of the account to remove | `jru` |

Everywhere below, replace `USER` with this value, exactly as given. `USER`:
1 to 16 characters; starts with a lower-case letter; only lower-case letters
`a`-`z`, digits and `_` after that. If it does not, stop and report: do not
run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Your release group |
|---|---|
| `14.1-RELEASE`, possibly followed by `-p` and a number (end of life as of 2026-09-24) | 14.1 |
| `14.0-RELEASE`, `14.2-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life), or `16.0-CURRENT` | other |
| anything else | stop, and report the line: this skill was not tested there |

Why: on a ZFS system, `adduser` on 14.1 and later gives each user's home a
ZFS dataset of its own. On 14.2 and later `rmuser` destroys that dataset;
on 14.1 it leaves it behind, empty, and step 6 finishes the job.

## Step 2: Look at the account

Run:

    pw usershow USER | awk -F: '{print "uid=" $3 " home=" $9}'; ls -ld /home/USER; echo "exit=$?"; echo "real=$(realpath /home/USER)"; echo "usermount=$(sysctl -n vfs.usermount)"; m=$(mount -p) && echo "mountlist ok"; printf '%s\n' "$m" | awk '$2 == "/home/USER" || $2 ~ "^/home/USER/"'

Expected, for an ordinary account (the number differs):

    uid=1001 home=/home/USER
    drwxr-xr-x  2 USER  USER  512 Sep 26 20:03 /home/USER
    exit=0
    real=/home/USER
    usermount=0
    mountlist ok

(with `USER` filled in). The number after `uid=` is called `UID` below.
`real=` is where `/home/USER` really is: if `/home` is a link to another
folder (common on systems upgraded from older releases), it shows that
other path, and the mount check below would look in the wrong place.
`usermount=0` means ordinary users cannot mount filesystems. The last
command lists any filesystem mounted at the home folder or inside it; on a
ZFS system the user's own home dataset may be listed, as one line such as:

    zroot/home/USER		/home/USER		zfs	rw,nfsv4acls 	0 0

| If you see | Do this |
|---|---|
| `uid=` a number from 1000 to 60000, ` home=/home/USER` exactly, then a line starting with `d` whose third word is `USER` and which ends in `/home/USER`, then `exit=0`, then `real=/home/USER` exactly, then `usermount=0`, then `mountlist ok`, then either nothing or exactly one line whose first word ends in `/USER`, second word is `/home/USER` and third word is `zfs` | if that mount line was shown, do the ZFS check in the next row first; then go to step 3 |
| (ZFS only) the mount line was shown | before going on, run `zfs list -H -t all -r -o name 'NAME'` (NAME: the first word of the mount line). It must print exactly one line, NAME itself. More lines are snapshots or datasets inside it: stop, and report them, because `rmuser` would empty the home but could not remove the dataset |
| `real=` anything other than `/home/USER` | `/home` (or the home) is a link to somewhere else. Stop, and report it: this skill only handles a real `/home/USER` |
| `mountlist ok` missing | the list of mounted filesystems could not be read. Stop, and report it |
| `usermount=` anything other than `0` | ordinary users may mount filesystems, so one could be mounted into the home before the removal. Stop, and report it |
| any other mount line (another filesystem type, another source, a mount inside the home, or more than one line) | stop, and report it: `rmuser` would delete inside that filesystem too |
| a `uid=` of 0, under 1000, or over 60000 | a system account. Stop, and report it: this skill does not remove system accounts |
| a `home=` other than `/home/USER` | the home folder is somewhere else, possibly shared. Stop, and report it: removing it could delete other people's files |
| a line starting with `l` (a link) or owned by someone else, or `No such file or directory` | the home folder is not the user's own. Stop, and report it |
| `pw: no such user` | there is no such account. Stop, and report it |
| anything else | stop, and report the full output |

## Step 3: Check no other account shares the number or the home

Two accounts can share one UID (an alias login, or an account from a
directory service), or one home folder, or one can have its home inside the
other's. `rmuser` would then also stop the other account's programs or delete
its files. This reads the UID again, then lists the name of every account
with that UID, the
home `/home/USER`, or a home inside it; then anything in the home folder
that someone else owns (for example a link root put there), which `rmuser`
would delete too. Run:

    grep '^passwd:' /etc/nsswitch.conf; echo "nis-lines=$(grep -c '^[+-]' /etc/master.passwd)"; uid=$(pw usershow USER | cut -d: -f3) && echo "uid=$uid"; p=$(getent passwd) && echo "getent ok"; printf '%s\n' "$p" | awk -F: -v uid="$uid" '$3 == uid || $6 == "/home/USER" || $6 ~ "^/home/USER/" {print $1}'; f=$(find -x /home/USER ! -user USER); echo "find exit=$?"; printf '%s\n' "$f" | head -5

| If you see | Do this |
|---|---|
| `passwd: compat` or `passwd: files` (spaces may differ), `nis-lines=0`, `uid=` followed by the same number as `UID` in step 2, `getent ok`, then exactly one line: `USER`, then `find exit=0` and nothing after it (an empty line is fine) | only this account has the number and the home, and everything in the home is its own. Go to step 4 |
| `find exit=` anything other than `0` | the home could not be searched completely. Stop, and report the full output |
| paths after `find exit=0` | the home holds things owned by someone else. Stop, and report them: this skill does not delete them |
| `getent ok`, then any other name, or more than one line | the number or the home is shared with those accounts. Stop, and report them: this skill does not remove a shared account |
| `getent ok` missing | the list of accounts could not be read. Stop, and report it |
| a `passwd:` line naming anything else (such as `ldap`, `sss`, `cache`), or `nis-lines=` other than `0` | accounts also come from a directory service, which may not list them all. Stop, and report it: this skill only handles local accounts |
| anything else | stop, and report the full output |

## Step 4: See what will be stopped

Programs the user is running will be stopped. Run:

    ps -U USER -o pid,command

Expected: a header line `PID COMMAND`, then one line per running program (or
none). Write them down for the report. (If a line shows `ps: No ruser named`,
report it and stop.)

## Step 5: Remove the account

`-y` answers the questions `rmuser` would otherwise ask (the Handbook's
example answers `y` twice). Run:

    rmuser -y USER; echo "exit=$?"

Expected: one line starting `Removing user (USER):` and ending in `passwd.`,
then `exit=0`, such as:

    Removing user (jru): crontab processes(1) mailspool home passwd.
    exit=0

(the list in between depends on what the user had). `rmuser` shows `exit=0`,
and prints this line, even when part of the removal failed: the line only
shows that it ran, and a line starting `pw:` or `cannot` means something
failed. Step 6 decides. If the line is missing, stop, report the output, and
end with FAILED; otherwise go to step 6.

## Step 6: Verify

Run:

    pw usershow USER; echo "exit=$?"; ls -d /home/USER /var/mail/USER /var/cron/tabs/USER; echo "exit=$?"; pgrep -U UID; echo "exit=$?"

Expected:

    pw: no such user `USER'
    exit=67
    ls: /home/USER: No such file or directory
    ls: /var/cron/tabs/USER: No such file or directory
    ls: /var/mail/USER: No such file or directory
    exit=1
    exit=1

(with `USER` and `UID` filled in; the error lines may come in a different
order from the `exit=` lines). `ls` gives `exit=1` even if only one path is
gone, so count the `No such file or directory` lines.

| If you see | Do this |
|---|---|
| exactly the expected output: `exit=67`, three `No such file or directory` lines, `exit=1`, `exit=1` | finished |
| the same, except that `/home/USER` is shown on a line by itself instead of its `No such file or directory` line | the files may be gone but the home folder left behind. Go to the check below |
| anything else (the account shown, another path shown, a program number shown, or any other `exit=`) | report it, and end with FAILED |

The check for a left-behind home folder:

    ls -A /home/USER; echo "exit=$?"; zfs list -H -o name,mountpoint /home/USER; zfs list -H -t snapshot -o name -r /home/USER

Read the name and mount point line first: if its mount point is not exactly
`/home/USER`, the folder is not a dataset of its own, so use the last row
and ignore any snapshot lines.

| If you see | Do this |
|---|---|
| only `exit=0`, then one line: a dataset name ending in `/USER` and the mount point `/home/USER`, and no snapshot lines | the files are gone, but the empty ZFS dataset of the home is left. **14.1**: remove it with `zfs destroy 'NAME'; echo "exit=$?"` (NAME: the dataset name shown, inside the single quotes; no `-r`). If it shows `exit=0`, run this step 6 again; any other `exit=`: report the output, and end with FAILED. **other**: report it, and end with FAILED |
| snapshot lines (names with `@`) | the files are gone, but the dataset has snapshots, so it was not destroyed. Report the snapshots, and end with FAILED: removing them is the person's decision |
| file names before `exit=0` | the home still has files. Stop, report them, and end with FAILED |
| anything else | stop, report the full output, and end with FAILED |

## Undo

None: the account and its files are gone. `basics/users-add` can create a new
account with the same name, but not bring back its files.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-26, snapshot 20260921 (a6deeaa2fb3b) | UFS and ZFS. |
| 15.1-RELEASE | verified | 2026-09-26 | UFS and ZFS. Also tried by hand. |
| 15.0-RELEASE | verified | 2026-09-26 | UFS and ZFS. |
| 14.5-RELEASE | verified | 2026-09-26 | UFS and ZFS. |
| 14.4-RELEASE | verified | 2026-09-26 | UFS and ZFS. |
| 14.3-RELEASE (EoL) | verified | 2026-09-26 | UFS and ZFS. |
| 14.2-RELEASE (EoL) | verified | 2026-09-26 | UFS and ZFS. |
| 14.1-RELEASE (EoL) | verified | 2026-09-26 | UFS and ZFS. On ZFS `rmuser` leaves the empty home dataset behind; step 6 destroys it (the model took that branch). |
| 14.0-RELEASE (EoL) | verified | 2026-09-26 | UFS and ZFS. `adduser` makes no home dataset here. |

## Weak-model check

2026-09-26 (UTC): claude-haiku-4-5, given only this skill, the input
`USER=hbtest2` (not the skill's example), and a tool that runs one command on
the test machine, followed it on a freshly reset system of every release
above, once on a UFS machine and once on a ZFS machine (18 runs). Beforehand
the account was made with `adduser` (on ZFS 14.1 and later that gives the home
a dataset of its own), with a mail file, a crontab, a running program, and
membership of the group `operator`. A run counts only when the model said DONE
AND the independent check (`verify.sh`: the account and its own group are
gone, it is no longer in `operator`, the home dataset (on ZFS), home folder,
mail and crontab are gone, no program runs under its old UID, and `root`,
`nobody` and `operator` are still there) passed: all 18 did, with the final
text and scripts. The command logs show the skill's commands on every run,
with the 14.1 dataset step only on ZFS 14.1.

## Not verified

- Accounts with a shared UID, a home other than `/home/USER`, or something
  mounted inside the home are refused, so removing them is not covered.
- The checks in steps 2 and 3 and the removal in step 5 are separate
  commands; with `vfs.usermount=0` (step 2) only root could change the
  account or mount something into its home in between.
- A directory service (LDAP and similar) that does not list all its
  accounts can hide an account sharing the UID from step 3.
- A mount at the home folder other than the user's own ZFS dataset is
  refused (step 2). Only a folder mounted below the home was tried (15.1),
  not one mounted at the home itself, and not a system where `/home` is a
  link (which step 2 refuses).
- Files the user owns outside the home folder, `/tmp` and `/var/tmp` stay;
  finding them (`find / -user UID`) is not part of the skill.

## Differences from the Handbook

- `rmuser -y` deletes every symbolic link in the home folder, whoever owns
  it, and every file of the UID there; it walks into any filesystem mounted
  in the home. With a home in a shared folder (tried: `/srv/shared`) it
  deleted a symbolic link owned by root. Hence the checks in steps 2 and 3.
- It stops programs and removes `/tmp` files by UID: removing an alias
  account that shares a UID stopped the other account's program and removed
  its file in `/tmp` (tried on 15.1). Hence the shared-UID check.
- With ZFS, `adduser` gives the home a dataset of its own on 14.1 and later
  (not on 14.0). `rmuser -y` destroys it on 14.2 and later, but not on 14.1
  (tried three times: the empty dataset stays, with no message and exit 0),
  and not when the dataset has snapshots (`filesystem has children`, still
  exit 0). Hence the snapshot check in step 2 and the 14.1 branch in step 6.

## Source

FreeBSD Handbook, "Removing a user",
https://docs.freebsd.org/en/books/handbook/basics/#users-rmuser
