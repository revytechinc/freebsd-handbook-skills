---
name: ports-pkg-set-automatic
description: Mark an installed package as "automatic" (installed only as a dependency), so that pkg autoremove removes it once nothing needs it.
handbook: ports/#pkgng-autoremove
handbook_commit: bdf18a0458
---

# Mark a package as installed automatically

## What this does

pkg remembers whether each package was installed on purpose or only as a
dependency ("automatic"). `pkg autoremove` removes automatic packages that
nothing needs any more. This skill marks one package as automatic. Use it for
a package you installed yourself but no longer want to keep for its own sake.

## Before you start

- You need: a root shell, and pkg itself installed (skill `ports/pkg-bootstrap`).
- This changes: one flag in pkg's database. Nothing is removed now.
- Time: seconds.
- Risk: low now, but the next `pkg autoremove` will remove the package (and
  its own unneeded dependencies) if no other package needs it. Undo reverses
  the mark.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `PACKAGE` | the exact package name, without a version | `curl` |

Everywhere below, replace `PACKAGE` with this value, exactly as given, with no
version number. `PACKAGE` must start with a lower-case letter or a digit, and
may contain only lower-case letters, digits, and the characters `.` `_` `+`
`-`. If it contains anything else (a space, `;`, `$`, `*`, a quote, `/`), stop
and report: do not run any command with it. If `PACKAGE` is `pkg` or starts
with `pkg-` (such as `pkg-devel`), stop and report: the package manager must
never be marked automatic. If `PACKAGE` starts with `freebsd-` (in any mix of
upper and lower case), stop and report: that is part of the base system.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.
The commands below are the same on every release.

## Step 2: Check the package and its current mark

Run:

    pkg query '%n %a' PACKAGE; echo "exit=$?"

| If you see | Meaning | Do this |
|---|---|---|
| `PACKAGE 0` and `exit=0`, where the name printed is exactly `PACKAGE` | installed on purpose | go to step 3 |
| a different name than `PACKAGE` (for example other upper and lower case) | not the package you were given | stop, and report it |
| `PACKAGE 1` and `exit=0` | already automatic | nothing to do. The task is finished |
| only `exit=1` | not installed | stop, and report it |
| anything else | unexpected | stop, and report the full output |

## Step 3: Mark it automatic

Run exactly this. The `-y` is required:

    pkg set -y -A 1 PACKAGE; echo "exit=$?"

Expected: only `exit=0`. Anything else: stop and report the output.

Do NOT leave out `-y`. Without a terminal, `pkg set -A 1 PACKAGE` prints the
question `Mark PACKAGE-<version> as automatically installed? [y/N]:`, takes
no answer as "no", changes nothing, and still exits with status 0.

## Step 4: Verify

Run the command from step 2 again:

    pkg query '%n %a' PACKAGE; echo "exit=$?"

Expected: `PACKAGE 1` and `exit=0`. If it still says `PACKAGE 0`, the task
did not succeed: stop and report.

## Undo

Mark it as installed on purpose again:

    pkg set -y -A 0 PACKAGE; echo "exit=$?"; pkg query '%n %a' PACKAGE

Expected: `exit=0`, then `PACKAGE 0`.

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
reset system of every release above, with nginx-lite installed on purpose. A
run counts only when the model said DONE AND the independent check
(`verify.sh`: nginx-lite still installed and now marked automatic, and no
other package's mark changed compared with the list saved before the run)
passed: all 9 did. A manual review of the command logs showed exactly the skill's four
commands on every release, always with `-y`.

## Not verified

- Undo was run by hand (`pkg set -y -A 0`, then the mark read back as `0`) on
  14.0, 14.5, 15.1 and 16.0-CURRENT, not by the weak model.
- The effect on `pkg autoremove` was seen by hand: after marking curl
  automatic, `pkg autoremove -n` listed curl and its 9 dependencies.

## Differences from the Handbook

- The Handbook's example is `pkg set -A 1 devel/cmake`. cmake is not installed
  on a fresh system, so that exact command prints
  `pkg: No package(s) matching devel/cmake` and exits with status 1. The
  origin form (`ftp/curl`) works for installed packages; this skill uses the
  name.
- Without `-y` (and without a terminal) the command silently does nothing and
  still exits 0. The Handbook does not use `-y`.

## Source

FreeBSD Handbook, "Automatically Removing Unused Packages",
https://docs.freebsd.org/en/books/handbook/ports/#pkgng-autoremove
