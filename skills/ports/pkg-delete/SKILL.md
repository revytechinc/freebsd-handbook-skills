---
name: ports-pkg-delete
description: Remove one installed package, after checking that no other installed package would be removed along with it.
handbook: ports/#pkg-delete
handbook_commit: bdf18a0458
---

# Remove a package

## What this does

Removes one installed package and its files. Before removing anything it
shows what would be removed, because pkg also removes every package that
depends on the one you remove. If anything else would go too, the skill stops
and reports it instead.

## Before you start

- You need: a root shell, and pkg itself installed (skill `ports/pkg-bootstrap`).
- This changes: removes the package's programs and files from `/usr/local`.
  The packages it depended on stay installed (see `ports/pkg-autoremove`).
- Time: seconds.
- Risk: medium. Files the package installed are deleted. Undo reinstalls it,
  but any changes made to its configuration files are lost.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `PACKAGE` | the exact package name, without a version | `curl` |

Everywhere below, replace `PACKAGE` with this value, exactly as given, with no
version number. `PACKAGE` must start with a lower-case letter or a digit, and
may contain only lower-case letters, digits, and the characters `.` `_` `+`
`-`. If it contains anything else (a space, `;`, `$`, `*`, a quote, `/`), stop
and report: do not run any command with it. If `PACKAGE` is `pkg`, stop: to
remove pkg itself, see the Undo of `ports/pkg-bootstrap`.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.
The commands below are the same on every release.

## Step 2: Is PACKAGE installed?

Run:

    pkg info -E PACKAGE; echo "exit=$?"

| If you see | Do this |
|---|---|
| one line `PACKAGE-<version>`, then `exit=0` | go to step 3 |
| only `exit=1` | it is not installed, so there is nothing to remove. The task is finished |
| anything else | stop, and report the full output |

## Step 3: See what would be removed

Run. `-n` only shows the plan; nothing is removed:

    pkg delete -n PACKAGE; echo "exit=$?"

Expected, for `PACKAGE` = `curl`:

    Checking integrity... done (0 conflicting)
    Deinstallation has been requested for the following 1 packages (of 0 packages in the universe):

    Installed packages to be REMOVED:
            curl: 8.22.0

    Number of packages to be removed: 1

    The operation will free 6 MiB.
    exit=0

Look at the lines under `Installed packages to be REMOVED:`.

| If you see | Do this |
|---|---|
| exactly one package, `PACKAGE`, and `exit=0` | go to step 4 |
| more than one package | the others depend on `PACKAGE` and would be removed too. Do NOT go on. Stop, report the list, and end with FAILED: the package was not removed |
| anything else | stop, and report the full output |

## Step 4: Remove it

Run. `-y` answers "yes" to the question automatically:

    pkg delete -y PACKAGE; echo "exit=$?"

Expected: the same list as in step 3, then

    [1/1] Deinstalling curl-8.22.0...
    [1/1] Deleting files for curl-8.22.0: .......... done
    exit=0

If the last line is not `exit=0`, stop and report the output.

## Step 5: Verify

Run:

    pkg info -e PACKAGE; echo "exit=$?"

Expected: only `exit=1` (the package is no longer installed). If you see
`exit=0`, the task did not succeed: stop and report.

## Undo

Reinstall the package with the skill `ports/pkg-install`. Changes that had
been made to its configuration files are not restored.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | |
| 15.1-RELEASE | verified | 2026-09-24 | |
| 15.0-RELEASE | verified | 2026-09-24 | |
| 14.5-RELEASE | verified | 2026-09-24 | |
| 14.4-RELEASE | verified | 2026-09-24 | |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | No special setting needed: removing works on the local list. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill, the input
`PACKAGE=nginx-lite` (deliberately not the package in the skill's examples),
and a tool that runs one command on the test machine, followed it on a freshly
reset system of every release above, with nginx-lite (and its dependency
pcre2) installed beforehand. A run counts only when the model said DONE AND
the independent check (`verify.sh`: nginx-lite and its program are gone, and
pcre2 is still installed, so nothing more was removed than asked) passed: all
9 did. A manual review of the command logs showed exactly the skill's five
commands on every release.

## Not verified

- The "more than one package" row of step 3 was run by hand, not by the weak
  model: with nginx-lite installed, `pkg delete -n pcre2` listed both
  `nginx-lite` and `pcre2` (on 14.0, 14.5, 15.1 and 16.0-CURRENT).
- Step 2's `exit=1` row, and removing a name that is not installed
  (`pkg delete -y` prints `No packages matched for pattern` and exits with
  status 1), were run by hand only.

## Differences from the Handbook

- The Handbook runs `pkg delete curl` and answers its question by hand.
  Without a terminal that is not possible, so this skill uses `-y`, after
  previewing with `-n`.
- The Handbook does not say that removing a package also removes the packages
  that depend on it. Step 3 exists to catch that.

## Source

FreeBSD Handbook, "Removing Packages",
https://docs.freebsd.org/en/books/handbook/ports/#pkg-delete
