---
name: ports-ports-tree-git
description: Download the FreeBSD Ports Collection to /usr/ports with git, on the branch matching the machine's packages (the newest quarterly branch, or main for Latest).
handbook: ports/#ports-using-git-method
handbook_commit: bdf18a0458
---

# Get the Ports Collection with git

## What this does

The Ports Collection is the set of recipes FreeBSD uses to build software from
source. This skill downloads it to `/usr/ports` with git. It picks the same
branch the machine's binary packages come from, because the Handbook warns that
mixing ports and packages from different branches causes conflicts.

## Before you start

- You need: a root shell, network access to `pkg.FreeBSD.org` and
  `git.FreeBSD.org`, pkg itself installed (skill `ports/pkg-bootstrap`), and
  about 1.5 GB of free disk space.
- This changes: installs the `git` package (if missing) and creates
  `/usr/ports`.
- Time: a few minutes.
- Risk: low. Undo removes `/usr/ports`.

## Inputs

None.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.
The commands below are the same on every release.

## Step 2: Check that /usr/ports does not exist yet

Run:

    ls -d /usr/ports; echo "exit=$?"

| If you see | Do this |
|---|---|
| `ls: /usr/ports: No such file or directory` and `exit=1` | go to step 3 |
| `/usr/ports` and `exit=0` | a ports tree (or something else) is already there. Stop, and report it: this skill does not replace it |
| anything else | stop, and report the full output |

## Step 3: Install git

Run:

    pkg install -y git; echo "exit=$?"

Expected: the list of packages being installed (git needs several), or the
line `The most recent versions of packages are already installed`, then
`exit=0`. Anything else: stop and report the output.

## Step 4: Find which branch the packages come from

Run:

    pkg -vv | grep -m1 url; echo "exit=$?"

Look at the end of the `url` line:

| The url ends with | Your branch | Do this |
|---|---|---|
| `/quarterly",` | the newest quarterly branch | go to step 5 |
| `/latest",` | `main` | skip step 5; go to step 6 and use the **main** command |
| anything else | unknown | stop, and report the output |

## Step 5: Find the name of the newest quarterly branch

Run:

    git ls-remote --heads https://git.FreeBSD.org/ports.git '20*Q*' | tail -1; echo "exit=$?"

Expected: one line ending in `refs/heads/` and a name like `2026Q3` (the year
and the quarter), then `exit=0`. Write that name down: it is `BRANCH` below.
If there is no such line, stop and report the output.

## Step 6: Download the tree

Run the command for your branch, replacing `BRANCH` with the name from step 5.
`--quiet` keeps git from printing a progress line for every file:

- **quarterly**: `git clone --quiet --depth 1 -b BRANCH https://git.FreeBSD.org/ports.git /usr/ports; echo "exit=$?"`
- **main**: `git clone --quiet --depth 1 https://git.FreeBSD.org/ports.git /usr/ports; echo "exit=$?"`

Expected: after about a minute, only `exit=0`. Anything else: stop and report
the output.

## Step 7: Verify

Run:

    git -C /usr/ports branch --show-current; ls /usr/ports/sysutils/lsof/Makefile; echo "exit=$?"

Expected: the branch name (`BRANCH` from step 5, or `main`), then
`/usr/ports/sysutils/lsof/Makefile`, then `exit=0`. Otherwise stop and report.

## Undo

Only if step 2 showed that `/usr/ports` did not exist before:

    rm -r /usr/ports; echo "exit=$?"

Expected: `exit=0` (it takes a while: the tree has about 176,000 files).

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | Packages come from Latest, so the tree is `main`; step 5 skipped. |
| 15.1-RELEASE | verified | 2026-09-24 | Quarterly: `2026Q3`. |
| 15.0-RELEASE | verified | 2026-09-24 | As 15.1. |
| 14.5-RELEASE | verified | 2026-09-24 | As 15.1. |
| 14.4-RELEASE | verified | 2026-09-24 | As 15.1. |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | As 15.1; installing git needs no special setting. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill and a tool that runs
one command on the test machine, followed it on a freshly reset system of
every release above. A run counts only when the model said DONE AND the
independent check (`verify.sh`: `/usr/ports` is a git checkout on the branch
matching pkg's, and holds the tree) passed: all 9 did. A manual review of the
command logs showed exactly the skill's seven commands on the quarterly
releases, and six on 16.0-CURRENT, where step 5 is skipped.

## Not verified

- Updating the tree later (`git -C /usr/ports pull`) was run by hand right
  after cloning (`Already up to date.`), not after the branch had moved on.
- Switching to another quarterly branch was not tested.
- Right after a new quarterly branch is created (early January, April, July
  and October), pkg.FreeBSD.org may still serve packages built from the
  previous one for some days; in that window this skill takes the new branch,
  one quarter ahead of the packages. The tests (2026-09-24) were not in that
  window, and `verify.sh` uses the same rule, so it would not notice.

## Differences from the Handbook

- The Handbook's example branch is `2023Q1`; the skill finds the newest one
  (`2026Q3` on 2026-09-24) instead of using a fixed name.
- The Handbook's commands print one progress line per few hundred files
  (176,000 files in all). The skill adds `--quiet`.

## Source

FreeBSD Handbook, "Installing the Ports Collection: Git Method",
https://docs.freebsd.org/en/books/handbook/ports/#ports-using-git-method
