---
name: ports-pkg-unlock
description: Unlock a package that was locked with pkg lock, so that pkg can upgrade, reinstall or remove it again.
handbook: ports/#pkg-locking-unlocking
handbook_commit: bdf18a0458
---

# Unlock a package

## What this does

Removes the lock from one package (see `ports/pkg-lock`), so that pkg can
upgrade, reinstall or remove it again.

## Before you start

- You need: a root shell, and pkg itself installed (skill `ports/pkg-bootstrap`).
- This changes: one flag in pkg's database.
- Time: seconds.
- Risk: low. The next `pkg upgrade` may then upgrade the package.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `PACKAGE` | the exact package name, without a version | `curl` |

Everywhere below, replace `PACKAGE` with this value, exactly as given, with no
version number. `PACKAGE` must start with a lower-case letter or a digit, and
may contain only lower-case letters, digits, and the characters `.` `_` `+`
`-`. If it contains anything else (a space, `;`, `$`, `*`, a quote, `/`), stop
and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.
The commands below are the same on every release.

## Step 2: Check the package

Run:

    pkg query '%n locked=%k' PACKAGE; echo "exit=$?"

| If you see | Meaning | Do this |
|---|---|---|
| `PACKAGE locked=1` and `exit=0` | locked | go to step 3 |
| `PACKAGE locked=0` and `exit=0` | not locked | nothing to do. The task is finished |
| only `exit=1` | not installed | stop, and report it |
| anything else | unexpected | stop, and report the full output |

## Step 3: Unlock it

Run exactly this. The `-y` is required:

    pkg unlock -y PACKAGE; echo "exit=$?"

Expected (for `PACKAGE` = `curl`): `Unlocking curl-8.22.0` and `exit=0`.
Anything else: stop and report the output.

Do NOT leave out `-y`. Without a terminal, `pkg unlock PACKAGE` prints the
question `PACKAGE-<version>: unlock this package? [y/N]:`, takes no answer as
"no", unlocks nothing, and still exits with status 0.

## Step 4: Verify

Run the command from step 2 again:

    pkg query '%n locked=%k' PACKAGE; echo "exit=$?"

Expected: `PACKAGE locked=0` and `exit=0`. If it still says `locked=1`, the
task did not succeed: stop and report.

## Undo

Lock it again with the skill `ports/pkg-lock`.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | |
| 15.1-RELEASE | verified | 2026-09-24 |  |
| 15.0-RELEASE | verified | 2026-09-24 |  |
| 14.5-RELEASE | verified | 2026-09-24 |  |
| 14.4-RELEASE | verified | 2026-09-24 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | No special setting needed. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill, the input
`PACKAGE=nginx-lite` (deliberately not the package in the skill's examples),
and a tool that runs one command on the test machine, followed it on a freshly
reset system of every release above (ZFS-root test machines), with nginx-lite installed and locked. A run
counts only when the model said DONE AND the independent check (`verify.sh`:
nginx-lite unlocked, and no other package's lock changed, compared with the list saved before the run) passed: all 9 did. A
manual review of the command logs showed exactly the skill's four commands on
every release, always with `-y`.

The committed test scripts were run once more on 16.0-CURRENT: passed.

## Not verified

- `pkg lock -l` when nothing is locked prints `No locked packages were found`
  and exits with status 1 (seen by hand on 14.0, 14.5, 15.1, 16.0-CURRENT).

## Differences from the Handbook

- The Handbook runs `pkg unlock` and answers its question by hand. Without a
  terminal, leaving out `-y` silently does nothing and still reports success.

## Source

FreeBSD Handbook, "Locking and Unlocking Packages",
https://docs.freebsd.org/en/books/handbook/ports/#pkg-locking-unlocking
