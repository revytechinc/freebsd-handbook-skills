---
name: basics-users-add
description: Create a new user account with its own group and home folder, optionally allowed to become the superuser, without typing any password into a command.
handbook: basics/#users-adduser
handbook_commit: bdf18a0458
---

# Add a user account

## What this does

Creates one user account: a login name, a full name, a group of the same name,
a home folder `/home/USER` filled with the default settings files, and the
shell `/bin/sh`. Optionally adds the user to the group `wheel`, whose members
may become the superuser (root) with `su`. The account is created with
password login switched off, so no password ever appears in a command; the
person sets their own password afterwards (see step 5).

## Before you start

- You need: a root shell.
- This changes: adds the user to `/etc/passwd` and `/etc/master.passwd`, adds
  a group to `/etc/group` (and the user to `wheel`, if asked), and creates
  `/home/USER`.
- Time: seconds.
- Risk: low. Undo removes the account and its home folder.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `USER` | the login name | `jru` |
| `FULLNAME` | the person's full name | `J. Random User` |
| `WHEEL` | `yes` to allow this user to become root, `no` otherwise | `yes` |

Everywhere below, replace `USER`, `FULLNAME` and `WHEEL` with these values,
exactly as given. Check them first:

- `USER`: 1 to 16 characters; starts with a lower-case letter; only
  lower-case letters `a`-`z`, digits and `_` after that.
- `FULLNAME`: 1 to 40 characters; only letters, digits, spaces and the
  characters `.` and `-`. (A `:` or `,` would break the account file.)
- `WHEEL`: exactly `yes` or exactly `no`.

If any of them does not, stop and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24) | go to step 2. The steps are the same on every release |
| anything else | stop, and report the line: this skill was not tested there |

## Step 2: Check the name is free

Run:

    pw usershow USER; echo "exit=$?"; pw groupshow USER; echo "exit=$?"; ls -d /home/USER /var/mail/USER /var/cron/tabs/USER; echo "exit=$?"

The last command also looks for a mail file and a scheduled-jobs file
(crontab) left over from an earlier account of the same name: Undo would
remove those too, so they must not exist. Expected, when the name is free:

    pw: no such user `USER'
    exit=67
    pw: unknown group `USER'
    exit=65
    ls: /home/USER: No such file or directory
    ls: /var/cron/tabs/USER: No such file or directory
    ls: /var/mail/USER: No such file or directory
    exit=1

(with `USER` filled in).

| If you see | Do this |
|---|---|
| those eight lines (the error lines may come in a different order from the `exit=` lines) | go to step 3 |
| a line starting with `USER:` after the first command, and `exit=0` | a user with that name exists. Stop, and report it: this skill does not change existing accounts |
| a line starting with `USER:` after the second command, and `exit=0` | a group with that name exists. Stop, and report it |
| any of `/home/USER`, `/var/mail/USER` or `/var/cron/tabs/USER` shown on a line by itself | files from an earlier account of that name are still there. Stop, and report them: this skill does not take them over |
| anything else | stop, and report the full output |

## Step 3: Create the account

`-d /home/USER -m` creates exactly the home folder step 2 checked, with the
default files; `-s /bin/sh` sets the shell, and `-w no` switches password
login off until a password is set. Run the command for `WHEEL`:

- **yes**: `pw useradd -n USER -c "FULLNAME" -d /home/USER -m -s /bin/sh -w no -G wheel; echo "exit=$?"`
- **no**: `pw useradd -n USER -c "FULLNAME" -d /home/USER -m -s /bin/sh -w no; echo "exit=$?"`

Expected: only `exit=0`. Anything else: run `pw usershow USER; echo
"exit=$?"` to see whether the account was partly made, report both outputs,
and end with FAILED.

## Step 4: Verify

Run:

    pw usershow USER; id USER; ls -ld /home/USER

Expected, for `jru` with `WHEEL=yes` (`NNNN` stands for a number, usually
`1001` for the first user added):

    jru:*:NNNN:NNNN::0:0:J. Random User:/home/jru:/bin/sh
    uid=NNNN(jru) gid=NNNN(jru) groups=NNNN(jru),0(wheel)
    drwxr-xr-x  2 jru jru 512 Sep 26 20:03 /home/jru

Check: the first line has `*` as its second field (password login is off),
`FULLNAME`, `/home/USER` and `/bin/sh`; the second line lists the group
`USER`, and `wheel` if `WHEEL` is `yes`; the third line shows the folder owned
by `USER`. Otherwise stop and report.

## Step 5: Report

Report the account created, and say that it has no password yet: to log in
with a password, the person (or root) runs `passwd USER`, which asks for the
new password twice without showing it. That command waits for typing, so this
skill does not run it.

## Undo

Only if step 3 showed `exit=0`: remove the account, its group and its home
folder (and any mail or scheduled jobs it has since received):

    pw userdel -n USER -r; echo "exit=$?"

Expected: `exit=0`, and `ls -d /home/USER` then says `No such file or
directory`.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-26, snapshot 20260921 (a6deeaa2fb3b) | Undo also tried by hand. |
| 15.1-RELEASE | verified | 2026-09-26 | As 16.0. |
| 15.0-RELEASE | verified | 2026-09-26 |  |
| 14.5-RELEASE | verified | 2026-09-26 |  |
| 14.4-RELEASE | verified | 2026-09-26 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-26 |  |
| 14.2-RELEASE (EoL) | verified | 2026-09-26 |  |
| 14.1-RELEASE (EoL) | verified | 2026-09-26 | As 16.0. |
| 14.0-RELEASE (EoL) | verified | 2026-09-26 |  |

## Weak-model check

2026-09-26 (UTC): claude-haiku-4-5, given only this skill, the inputs
`USER=hbtest1`, `FULLNAME=Test Account`, `WHEEL=yes` (not the skill's
example), and a tool that runs one command on the test machine, followed it
on a freshly reset system of every release above. A run counts only when the
model said DONE AND the independent check (`verify.sh`: the account has that
full name, `/bin/sh` and `/home/hbtest1`; its password field is `*`; its
primary group is its own and it is in `wheel`; its home folder exists, is owned by it and has
the default files) passed: all 9 did, with the final text. The command logs show exactly the
skill's four commands on every release.

## Not verified

- Tried by hand on 15.1: `pw useradd -m` does not fail when the home folder
  already exists; it takes the folder over. `pw userdel -r` also removes the
  user's mail file and crontab. That is why step 2 checks all three.
- Shells from packages (the Handbook's example uses `zsh`) were not tried;
  the skill uses the base system's `/bin/sh`.
- Setting the password (`passwd USER`) waits for typing and is not part of
  the skill.

## Differences from the Handbook

- The Handbook uses `adduser`, which asks each question in turn, including
  the password twice. A model cannot answer such prompts reliably, and a
  password typed into a command would be stored in logs. The skill uses
  `pw useradd`, the tool `adduser` itself uses, with every answer on the
  command line and password login switched off.
- The skill's default shell is `/bin/sh`, as `adduser` offers by default.

## Source

FreeBSD Handbook, "Adding a user",
https://docs.freebsd.org/en/books/handbook/basics/#users-adduser
