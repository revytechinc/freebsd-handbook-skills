---
name: ports-pkg-clean
description: Delete outdated package files from pkg's download cache, keeping the files of the current versions.
handbook: ports/#pkgng-clean
handbook_commit: bdf18a0458
---

# Remove outdated files from the package cache

## What this does

pkg keeps a copy of every package file it downloads, in `/var/cache/pkg`. Over
time the cache fills with old versions. This skill deletes the cached files
that are **stale**: versions the repository no longer offers, and files that
are not packages at all. Files of the current versions are kept (to remove
everything, see `ports/pkg-clean-all`). Installed software is not touched.

## Before you start

- You need: a root shell, and pkg itself installed (skill `ports/pkg-bootstrap`).
- This changes: deletes files in `/var/cache/pkg`.
- Time: seconds.
- Risk: none for installed software. Deleted files would be downloaded again
  if they were ever needed.

## Inputs

None.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.
The commands below are the same on every release.

## Step 2: See what would be deleted

Run. `-n` only shows the plan; nothing is deleted:

    pkg clean -n; echo "exit=$?"

| If you see | Do this |
|---|---|
| `Nothing to do.` and `exit=0` | nothing is stale. The task is finished |
| `The following package files will be deleted:`, a list of files under `/var/cache/pkg/`, and `exit=0` | go to step 3 |
| anything else | stop, and report the full output |

Example:

    The following package files will be deleted:
            /var/cache/pkg/curl-0.0.1~0000000000.pkg
    The cleanup will free 2 MiB
    exit=0

## Step 3: Delete them

Run. `-y` answers "yes" to the question automatically:

    pkg clean -y; echo "exit=$?"

Expected: the same list, then `exit=0`. Anything else: stop and report the
output.

## Step 4: Verify

Run:

    pkg clean -n; echo "exit=$?"

Expected: `Nothing to do.` and `exit=0`. If a list is still shown, stop and
report it.

## Undo

None needed: the deleted files were outdated copies. A package that is needed
again is downloaded again by `pkg install`.

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
every release above, with curl installed and one stale file placed in the
cache. A run counts only when the model said DONE AND the independent check
(`verify.sh`: the stale file gone, the current curl package file still cached,
curl still working) passed: all 9 did. A manual review of the command logs
showed exactly the skill's four commands on every release.

## Not verified

- The stale file in the tests was made by copying a cached package under a
  version the repository does not have (`curl-0.0.1~0000000000.pkg`), which is
  how an old version looks to pkg. A cache aged by real releases was not used.

## Differences from the Handbook

- The Handbook says `pkg clean` keeps "only copies of the latest installed
  packages". In the tests it did not look at what is installed: after `curl`
  was removed, its cached file was still kept, because the repository still
  offers that version. What it deletes is files the repository no longer
  offers, and files that are not packages (a stray `notapackage.txt` was
  deleted too).
- The Handbook answers the question by hand; without a terminal this skill
  previews with `-n` and then uses `-y`.

## Source

FreeBSD Handbook, "Removing Stale Packages",
https://docs.freebsd.org/en/books/handbook/ports/#pkgng-clean
