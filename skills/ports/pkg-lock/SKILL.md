---
name: ports-pkg-lock
description: Lock an installed package so that pkg will not upgrade, reinstall or remove it until it is unlocked.
handbook: ports/#pkg-locking-unlocking
handbook_commit: bdf18a0458
---

# Lock a package

## What this does

Locks one installed package. While it is locked, pkg refuses to remove it,
reinstall it or change it, and refuses to remove packages it depends on. Use
it to keep a package exactly as it is, for example while testing. Unlock it
with `ports/pkg-unlock`.

## Before you start

- You need: a root shell, and pkg itself installed (skill `ports/pkg-bootstrap`).
- This changes: one flag in pkg's database.
- Time: seconds.
- Risk: low. Later `pkg upgrade`, `pkg delete` and similar commands will
  refuse to touch the package until it is unlocked.

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
| `PACKAGE locked=0` and `exit=0` | installed, not locked | go to step 3 |
| `PACKAGE locked=1` and `exit=0` | already locked | nothing to do. The task is finished |
| only `exit=1` | not installed | stop, and report it: only installed packages can be locked |
| anything else | unexpected | stop, and report the full output |

## Step 3: Lock it

Run exactly this. The `-y` is required:

    pkg lock -y PACKAGE; echo "exit=$?"

Expected (for `PACKAGE` = `curl`): `Locking curl-8.22.0` and `exit=0`.
Anything else: stop and report the output.

Do NOT leave out `-y`. Without a terminal, `pkg lock PACKAGE` prints the
question `PACKAGE-<version>: lock this package? [y/N]:`, takes no answer as
"no", locks nothing, and still exits with status 0.

## Step 4: Verify

Run:

    pkg lock -l; echo "exit=$?"

Expected: `Currently locked packages:`, a line `PACKAGE-<version>`, and
`exit=0`. If `PACKAGE` is not listed, the task did not succeed: stop and
report.

## Undo

Unlock it with the skill `ports/pkg-unlock`.

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
reset system of every release above (UFS-root test machines), with nginx-lite installed. A run
counts only when the model said DONE AND the independent check (`verify.sh`:
nginx-lite locked, and no other package's lock changed, compared with the list saved before the run) passed: all 9 did. A
manual review of the command logs showed exactly the skill's four commands on
every release, always with `-y`.

The committed test scripts were run once more on 14.0-RELEASE: passed.

## Not verified

- What a lock blocks was run by hand on 14.0, 14.5, 15.1 and 16.0-CURRENT, not
  by the weak model: with nginx-lite locked, `pkg delete -y nginx-lite` printed
  `The following package(s) are locked or vital and may not be removed:` and
  exited with status 7; `pkg install -y -f nginx-lite` printed
  `nginx-lite-<version> is locked and may not be modified` and exited with
  status 1; removing its dependency (`pkg delete -n pcre2`) was refused too.
- Whether a lock holds back `pkg upgrade` when a newer version is waiting was
  not tested (no newer version was waiting in that trial).

## Differences from the Handbook

- The Handbook runs `pkg lock` and answers its question by hand. Without a
  terminal, leaving out `-y` silently does nothing and still reports success.

## Source

FreeBSD Handbook, "Locking and Unlocking Packages",
https://docs.freebsd.org/en/books/handbook/ports/#pkg-locking-unlocking
