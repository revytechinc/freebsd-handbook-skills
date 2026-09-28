---
name: basics-shells-add
description: Add an installed shell (such as bash or zsh from a package) to /etc/shells, the list of approved login shells, so users may choose it with chsh.
handbook: basics/#changing-shells
handbook_commit: bdf18a0458
---

# Add a shell to /etc/shells

## What this does

Adds one installed shell to `/etc/shells`, the list of shells users may pick
for themselves with `chsh`. A shell installed from a package is normally
added by the package itself; this skill is for one that is missing (the
Handbook's note on changing the shell). The file is checked first, and the
shell's line is added at the end.

## Before you start

- You need: a root shell, and the shell already installed (skill
  `ports/pkg-install`).
- This changes: adds one line to `/etc/shells`. Nothing else.
- Time: seconds.
- Risk: low. Undo removes the line again.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `SHELL` | the full path of the installed shell | `/usr/local/bin/bash` |

Everywhere below, replace `SHELL` with this value, exactly as given. Check it
first: it is `/bin/`, `/usr/bin/` or `/usr/local/bin/`, followed by 1 to 32
letters, digits or the characters `_` `-` (and nothing else; no `.`, which
Undo's `sed` would read as "any character"). If it is
not, stop and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24) | go to step 2. The steps are the same on every release |
| anything else | stop, and report the line: this skill was not tested there |

## Step 2: Check the shell and the list

Run:

    [ -f /etc/shells ] || echo "no /etc/shells"; awk -v s='SHELL' '{ sub(/#.*/, ""); if ($1 == s) f = 1 } END { exit !f }' /etc/shells; echo "listed=$?"; ls -ld 'SHELL' "$(dirname 'SHELL')"; stat -f "type=%HT owner=%Su mode=%Mp%03Lp" 'SHELL'; echo "exit=$?"; stat -f "folder owner=%Su mode=%Mp%03Lp" "$(dirname 'SHELL')"; realpath 'SHELL'; tail -c 1 /etc/shells | od -An -c

Expected, such as:

    listed=1
    -r-xr-xr-x  1 root wheel 942344 Sep 20 10:12 /usr/local/bin/bash
    drwxr-xr-x  2 root wheel    182 Sep 20 10:12 /usr/local/bin
    type=Regular File owner=root mode=0555
    exit=0
    folder owner=root mode=0755
    /usr/local/bin/bash
       \n

"The file checks" below means: `type=Regular File`, `owner=root`, `mode=0`
followed by three digits whose first is `5` or `7` and whose last two are
each `0`, `1`, `4` or `5`; then `exit=0`; `folder owner=root` with a `mode=`
whose last two digits are each `0`, `1`, `4` or `5`; and the path line is
`SHELL` again exactly; and in the two `ls -ld` lines, no `+` right after the
permissions (a `+` means extra permissions, an ACL, that the mode does not
show). Together they mean only root can replace the shell file.

Go through these rows in order and use the first that matches:

| If you see | Do this |
|---|---|
| `no /etc/shells` | the list itself is missing. Stop, and report it: it has to be restored first |
| `type=Symbolic Link` (even with `No such file or directory` after it), or the path line differs from `SHELL` | `SHELL` is a link. Stop, and report both paths: add the path it points to instead, if that is what is wanted |
| `No such file or directory` | the shell is not installed (or its folder is missing). Stop, and report it |
| anything where the file checks do not hold (another `owner=`, a `mode=` such as `0775` or one starting with `4`, or a `+` after the permissions, for the file or the folder) | someone other than root could change the shell, or it has special permissions. Stop, and report it: a listed shell is trusted by the system (if it is already listed, report that too: it should be fixed or removed) |
| `listed=0`, and the file checks hold | it is already listed. Stop, and report it: nothing needs doing |
| `listed=1`, the file checks hold, then `\n` | the shell is installed, only root can change it, and it is not listed yet. Go to step 3 |
| `listed=1`, the file checks hold, then something other than `\n` | `/etc/shells` does not end with a line break: the new line would be joined to the last one. Stop, and report it |
| anything else | stop, and report the full output |

## Step 3: Add it

Run:

    printf '%s\n' 'SHELL' >> /etc/shells; echo "exit=$?"

Expected: only `exit=0`. Anything else: stop, report the output, and end with
FAILED.

## Step 4: Verify

Run:

    grep -Fxc 'SHELL' /etc/shells; tail -n 1 /etc/shells

Expected: `1`, then `SHELL`. Otherwise stop, report the output, and end with
FAILED.

Report that users can now choose the shell: each user runs `chsh -s SHELL`
(it asks for their password), or root changes it for them (skill
`basics/users-change`). The new shell is used from their next login.

## Undo

Only if step 3 showed `exit=0`. First check no account uses the shell:

    u=$(pw usershow -a) && echo "pw ok"; printf '%s\n' "$u" | awk -F: -v s='SHELL' '$NF == s { n++ } END { print "users=" n + 0 }'

Go on only with `pw ok` and `users=0`; otherwise stop, and report it (those
accounts must get another shell first, skill `basics/users-change`). Then
remove the line: `sed` deletes the last line of `/etc/shells` only if it is
exactly `SHELL`, in one step:

    sed -i '' '${\|^SHELL$|d;}' /etc/shells; echo "exit=$?"; grep -Fxc 'SHELL' /etc/shells

Expected: `exit=0`, then `0` (the line is gone). A `1` means it was not the
last line any more: stop, and report it.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-28, snapshot 20260921 (a6deeaa2fb3b) | Also tried by hand (see below). |
| 15.1-RELEASE | verified | 2026-09-28 |  |
| 15.0-RELEASE | verified | 2026-09-28 |  |
| 14.5-RELEASE | verified | 2026-09-28 |  |
| 14.4-RELEASE | verified | 2026-09-28 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.2-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.1-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.0-RELEASE (EoL) | verified | 2026-09-28 |  |

## Weak-model check

2026-09-28 (UTC): claude-haiku-4-5, given only this skill, the input
`SHELL=/usr/local/bin/hbsh` (not the skill's example), and a tool that runs
one command on the test machine, followed it on a freshly reset system of
every release above (UFS), where `/usr/local/bin/hbsh` was a copy of
`/bin/sh`, root-owned with mode `555`, not listed in `/etc/shells` (it
stands in for a shell from a package, so no network was needed). A run
counts only when the model said DONE AND the independent check
(`verify.sh`: `/etc/shells` is exactly its old content plus the one last
line, still ending with a line break, with the same permissions and owner)
passed: all 9 did, with this version of the skill and scripts. The command
logs show exactly the skill's commands on every release.

## Not verified

- A shell from a real package was not used; packages such as `bash` add
  themselves to `/etc/shells` when installed, so this skill is rarely needed
  for them.
- The model was not tested on any stop in step 2. Tried by hand on 16.0:
  a link to the shell shows `type=Symbolic Link`; the shell with mode
  `0775` fails the file checks; an already listed shell shows `listed=0`.
- Undo was tried by hand on 16.0 and 14.0: the `sed` command removes the
  last line only when it is exactly the shell, and otherwise leaves the file
  unchanged; the model did not run it.
- Tried by hand on 16.0 and 14.0: step 2's `awk` also finds a listed shell
  with a comment after it (`/usr/local/bin/bash # from pkg`), as the system
  reads the file. On 16.0 (ZFS) an ACL giving `nobody` write access showed
  as `+` after `-r-xr-xr-x` while `stat` still said `mode=0555`.
- The checks cover the shell file and its folder, not the folders above,
  nor what the shell loads (libraries, or the program named on a script's
  first line).
- `chsh -s` by a user (it asks for the user's password) was not tried.

## Differences from the Handbook

- The Handbook adds the line with `echo /usr/local/bin/bash >> /etc/shells`.
  The skill first checks the shell is installed, is not a link, can only be
  changed by root, is not listed yet, and that `/etc/shells` ends with a line
  break; it adds the line with `printf`, which prints the path exactly.

## Source

FreeBSD Handbook, "Changing the Shell" (in "Shells"),
https://docs.freebsd.org/en/books/handbook/basics/#changing-shells
