---
name: ports-pkg-clean-all
description: Delete every file from pkg's download cache to free disk space; installed software keeps working.
handbook: ports/#pkgng-clean
handbook_commit: bdf18a0458
---

# Empty the package cache

## What this does

pkg keeps a copy of every package file it downloads, in `/var/cache/pkg`. This
skill deletes all of them to free disk space. Installed software keeps
working: the cache is only a store of downloaded files. (To delete only
outdated files and keep the current ones, see `ports/pkg-clean`.)

## Before you start

- You need: a root shell, and pkg itself installed (skill `ports/pkg-bootstrap`).
- This changes: deletes every file in `/var/cache/pkg`.
- Time: seconds.
- Risk: none for installed software. A later install or reinstall downloads
  what it needs again, which needs network access.

## Inputs

None.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.
The commands below are the same on every release.

## Step 2: See what would be deleted

Run. `-a` means "all files", `-n` only shows the plan:

    pkg clean -a -n; echo "exit=$?"

| If you see | Do this |
|---|---|
| `Nothing to do.` and `exit=0` | the cache is already empty. The task is finished |
| `The following package files will be deleted:`, a list of files under `/var/cache/pkg/`, and `exit=0` | go to step 3 |
| anything else | stop, and report the full output |

Each cached package usually appears twice, for example
`/var/cache/pkg/curl-8.22.0~9f2b5874f4.pkg` (the file) and
`/var/cache/pkg/curl-8.22.0.pkg` (a link to it). That is normal.

## Step 3: Delete them

Run. `-y` answers "yes" to the question automatically:

    pkg clean -a -y; echo "exit=$?"

Expected: the same list, then `exit=0`. Anything else: stop and report the
output.

## Step 4: Verify

Run:

    pkg clean -a -n; echo "exit=$?"

Expected: `Nothing to do.` and `exit=0`. If a list is still shown, stop and
report it.

## Undo

None needed. Files are downloaded again when a package is installed.

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

2026-09-24 (UTC): claude-haiku-4-5, given only this skill and a tool that runs
one command on the test machine, followed it on a freshly reset system of
every release above, with curl installed (so the cache held its package files
and those of its dependencies). A run counts only when the model said DONE AND
the independent check (`verify.sh`: no package file left in the cache, curl
still installed and working) passed: all 9 did. A manual review of the command
logs showed exactly the skill's four commands on every release.

## Not verified

- Nothing beyond the steps above. A reinstall after emptying the cache
  (`pkg install -y -f curl`) was run by hand on 14.0, 14.5, 15.1 and
  16.0-CURRENT: it downloaded the file again and worked.

## Differences from the Handbook

- The Handbook shows `pkg clean` and mentions removing everything; without a
  terminal the question cannot be answered, so this skill previews with `-n`
  and then uses `-y`.

## Source

FreeBSD Handbook, "Removing Stale Packages",
https://docs.freebsd.org/en/books/handbook/ports/#pkgng-clean
