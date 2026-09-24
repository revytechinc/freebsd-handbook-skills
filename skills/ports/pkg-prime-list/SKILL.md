---
name: ports-pkg-prime-list
description: List the packages that were installed on purpose (not as dependencies) and save their origins to a file, for example to rebuild or reinstall the same set later.
handbook: ports/#pkgng-autoremove
handbook_commit: bdf18a0458
---

# List the packages installed on purpose

## What this does

pkg remembers which packages you installed on purpose and which it installed
only as dependencies ("automatic" packages). This skill shows the packages
installed on purpose, and saves their **origins** (their place in the ports
collection, such as `ftp/curl`) to a file. That file is the list needed to
rebuild or reinstall the same software on another machine.

## Before you start

- You need: a root shell, and pkg itself installed (skill `ports/pkg-bootstrap`).
- This changes: creates the new file `FILE`. Nothing else. `FILE` must not
  exist yet (step 3 checks), so no existing file is ever overwritten.
- Time: seconds.
- Risk: none.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `FILE` | the file to save the list in; a full path under `/root/` | `/root/prime-origins.txt` |

Everywhere below, replace `FILE` with this value, exactly as given. `FILE`
must start with `/root/`, must not contain `..`, must not have any part that
starts with `.` (so not `/root/.ssh/...`), and may contain only letters,
digits, and the characters `/` `.` `_` `-`. If it does not, stop and
report: do not run any command with it. (Other places, such as `/etc`, hold
files the system reads, and `/tmp` can be written by other users.)

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.
The commands below are the same on every release.

## Step 2: Show the packages installed on purpose

Run:

    pkg prime-list; echo "exit=$?"

Expected: one package name per line, then `exit=0`. For example, with curl
installed:

    curl
    pkg
    exit=0

On 15.x and 16.0-CURRENT the list also contains a few `FreeBSD-...` names:
parts of the base system that were installed on purpose. Count the names (not
the `exit=` line) and write the number down. If the last line is not
`exit=0`, stop and report the output.

## Step 3: Check that FILE does not exist yet

Run:

    ls -l FILE; echo "exit=$?"

| If you see | Do this |
|---|---|
| `ls: FILE: No such file or directory` and `exit=1` | good: go to step 4 |
| a line describing the file, and `exit=0` | the file already exists. Do NOT overwrite it. Stop, report it, and end with FAILED: ask for a new file name |
| anything else | stop, and report the full output |

## Step 4: Save their origins to FILE

Run exactly this. It first collects the list, and only then creates `FILE`;
if collecting fails, no file is created at all. Step 3 made sure nothing is at
`FILE`, and `set -C` also makes the shell refuse to replace an existing file,
in case one appeared since:

    out=$(pkg prime-origins) && (set -C; printf '%s\n' "$out" > FILE); echo "exit=$?"

| If you see | Do this |
|---|---|
| only `exit=0` (the list goes into the file, not to the screen) | go to step 5 |
| a line ending in `File exists` | the file exists after all. Stop, report it, and end with FAILED. Do not remove anything |
| anything else | stop, report the output, and end with FAILED. Do not remove anything |

## Step 5: Verify

Run:

    wc -l < FILE && cat FILE; echo "exit=$?"

Expected: first a number, the same as the count you wrote down in step 2;
then that many lines such as `ftp/curl` and `ports-mgmt/pkg` (on 15.x and
16.0-CURRENT also lines starting `base/`); then `exit=0`. If the number is
different, or there is an error, stop and report the output.

## Undo

Only if step 3 showed that `FILE` did not exist before. Remove the file:

    rm FILE; echo "exit=$?"

Expected: `exit=0`.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | The list includes base-system packages. |
| 15.1-RELEASE | verified | 2026-09-24 | The list includes 7 base-system packages. |
| 15.0-RELEASE | verified | 2026-09-24 | The list includes base-system packages. |
| 14.5-RELEASE | verified | 2026-09-24 |  |
| 14.4-RELEASE | verified | 2026-09-24 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | No special setting needed. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill, the input
`FILE=/root/installed-origins.txt` (deliberately not the path in the skill's
examples), and a tool that runs one command on the test machine, followed it
on a freshly reset system of every release above, with curl and nginx-lite
installed on purpose. A run counts only when the model said DONE AND the
independent check (`verify.sh`: the file holds exactly the origins in the
list saved before the run, and pkg's database still agrees) passed: all 9
did. A manual review of the command logs showed exactly the skill's five
commands on every release, including the check that `FILE` did not exist.

## Not verified

- Reinstalling or rebuilding from the saved list (with poudriere, synth or
  `pkg install`) is not part of this skill and was not tested here.

## Differences from the Handbook

- As the Handbook says, `prime-list` and `prime-origins` are aliases defined
  in `/usr/local/etc/pkg.conf`, installed with pkg; both gave exactly the same
  result as the `pkg query` they stand for on 14.0, 14.5, 15.1 and
  16.0-CURRENT.
- On 15.x and 16.0-CURRENT the list includes some base-system packages
  (7 on 15.1), which the Handbook's example does not show.

## Source

FreeBSD Handbook, "Automatically Removing Unused Packages",
https://docs.freebsd.org/en/books/handbook/ports/#pkgng-autoremove
