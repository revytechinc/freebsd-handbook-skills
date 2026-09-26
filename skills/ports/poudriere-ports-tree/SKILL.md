---
name: ports-poudriere-ports-tree
description: Give poudriere its own copy of the Ports Collection, cloned with git from the branch matching this machine's packages.
handbook: ports/#poudriere-initialization
handbook_commit: bdf18a0458
---

# Give poudriere a ports tree

## What this does

poudriere builds packages from its own copy of the Ports Collection (a
*ports tree*), kept separate from `/usr/ports`. This skill creates one with
git, from the same branch the machine's packages come from: the current
quarterly branch (such as `2026Q3`) if pkg uses `quarterly`, or `main` if pkg
uses `latest`. That way packages built with poudriere match the official
ones. Next step: `ports/poudriere-bulk`.

## Before you start

- You need: a root shell, network access to FreeBSD's servers, git and
  poudriere installed (skill `ports/pkg-install`), and poudriere configured
  (skill `ports/poudriere-jail`, steps 1 to 3). About 1.5 GB of free disk
  space.
- This changes: creates the ports tree under `/usr/local/poudriere/ports/`.
- Time: about a minute.
- Risk: low. Undo deletes the tree.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `TREE` | a name for the ports tree | `local` |

Everywhere below, replace `TREE` with this value, exactly as given. It must
be 1 to 20 characters: letters `a`-`z`, `A`-`Z` and digits only, and not
`PORTSTREE` (the word poudriere uses as a heading). If it is not, stop and
report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24) | go to step 2. The steps are the same on every release |
| anything else | stop, and report the line: this skill was not tested there |

## Step 2: Check poudriere, git, and existing trees

Run:

    pkg info -E poudriere git && poudriere ports -l; echo "exit=$?"

| If you see | Do this |
|---|---|
| a `poudriere-` line, a `git-` line, a header line starting `PORTSTREE`, no line starting with `TREE` followed by a space, then `exit=0` | go to step 3 |
| a line starting with `TREE` followed by a space | a tree with that name exists. Stop, and report it |
| `ZPOOL variable is not set` | poudriere is not configured yet. Stop, and report it (see `ports/poudriere-jail`) |
| `pkg: No package(s) matching` and a name | that program is not installed. Stop, and report it (see `ports/pkg-install`) |
| anything else | stop, and report the full output |

## Step 3: Find which branch the machine's packages come from

Run:

    pkg -vv | grep -e '/quarterly"' -e '/latest"'; echo "exit=$?"

| If you see | Do this |
|---|---|
| one line with a `url` ending in `/quarterly",`, then `exit=0` | quarterly: go to step 4 |
| one line with a `url` ending in `/latest",`, then `exit=0` | latest: the branch is `main`. Go to step 5 |
| anything else | stop, and report the full output |

## Step 4 (quarterly only): Find the current quarterly branch

Run:

    git ls-remote --heads https://git.FreeBSD.org/ports.git '20*Q*' </dev/null > /root/poudriere-branches.txt; echo "exit=$?"; tail -1 /root/poudriere-branches.txt

Expected: `exit=0`, then one line: a long hexadecimal number, spaces, and
`refs/heads/` followed by a branch name such as `2026Q3`. The
part after `refs/heads/` is called `BRANCH` below. It must be four digits,
`Q`, and one digit from 1 to 4; if it is not, or anything else is shown, stop
and report.

## Step 5: Create the ports tree

Run the command for your branch. The output goes into a file in root's home
directory, and only the end is shown:

- **quarterly**: `poudriere ports -c -p TREE -m git+https -B BRANCH > /root/poudriere-ports.log 2>&1; echo "exit=$?"; tail -2 /root/poudriere-ports.log`
- **latest**: `poudriere ports -c -p TREE -m git+https > /root/poudriere-ports.log 2>&1; echo "exit=$?"; tail -2 /root/poudriere-ports.log`

Expected, after about a minute:

    exit=0
    [00:00:00] Creating local fs at /usr/local/poudriere/ports/local... done
    [00:00:00] Cloning the ports tree... done

| If you see | Do this |
|---|---|
| `exit=0` and `Cloning the ports tree... done` | go to step 6 |
| anything else | stop: report the lines shown, and end with FAILED |

## Step 6: Verify

Run:

    poudriere ports -l && git -C /usr/local/poudriere/ports/TREE rev-parse --abbrev-ref HEAD; echo "exit=$?"

Expected: a header line starting `PORTSTREE`, a line starting with `TREE`
and `git+https`, then the branch (`BRANCH` from step 4, or `main`), then
`exit=0`. Otherwise stop and report.

## Undo

Remove the branch list (`rm -f /root/poudriere-branches.txt`), and delete the
ports tree (it does not ask for confirmation):

    poudriere ports -d -p TREE; echo "exit=$?"

Expected: `Deleting portstree "TREE"... done`, then `exit=0`.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-26, snapshot 20260921 (a6deeaa2fb3b) | UFS and ZFS. pkg uses `latest`, so the tree is on `main`. |
| 15.1-RELEASE | verified | 2026-09-26 | UFS and ZFS. Quarterly: branch `2026Q3`, a shallow clone of 1.4 GB. |
| 15.0-RELEASE | verified | 2026-09-26 | As 15.1. |
| 14.5-RELEASE | verified | 2026-09-26 | As 15.1. |
| 14.4-RELEASE | verified | 2026-09-26 | As 15.1. |
| 14.3-RELEASE (EoL) | verified | 2026-09-26 | As 15.1. |
| 14.2-RELEASE (EoL) | verified | 2026-09-26 | As 15.1. |
| 14.1-RELEASE (EoL) | verified | 2026-09-26 | As 15.1. |
| 14.0-RELEASE (EoL) | verified | 2026-09-26 | As 15.1. |

## Weak-model check

2026-09-26 (UTC): claude-haiku-4-5, given only this skill, the input
`TREE=testtree` (not the skill's example), and a tool that runs one command
on the test machine, followed it on a freshly reset system of every release
above, once on a UFS machine and once on a ZFS machine (18 runs). Beforehand
poudriere and git were installed and poudriere configured. A run counts only
when the model said DONE AND the independent check (`verify.sh`: poudriere
lists `testtree` as `git+https`; it is a real ports tree; and its branch is
the one the check works out separately from pkg's configuration, by the
same rule as the skill: the newest quarterly branch, or `main` for `latest`) passed: all 18 did, with the final
text and scripts. The command logs show the skill's commands only: the
quarterly steps with `-B` on every release but 16.0, and the `main` command
on 16.0.

## Not verified

- For the first week or two of a new quarter, the newest quarterly branch
  already exists while the official `quarterly` packages are still built
  from the previous one; a tree made then is one quarter ahead of them. The
  test's check works the branch out the same way, so it would not notice.
- Step 3 assumes the repository shown is the one in use. A disabled
  repository with such a URL would also be found; the test machines have
  the default configuration.

- Other methods than `git+https` (the Handbook's other options) were not
  tried.
- Updating the tree later (`poudriere ports -u -p TREE`) is not part of this
  skill and was not tried.

## Differences from the Handbook

- The Handbook runs `poudriere ports -c -p local -m git+https`, which clones
  `main`. The skill picks the branch matching the machine's packages with
  `-B`, as `ports/ports-tree-git` does for `/usr/ports`.
- On 15 and 16, `pkg -vv` also lists the base system and kernel-module
  repositories; step 3 looks only for the URL ending in `/quarterly` or
  `/latest`, which is the ports repository.

## Source

FreeBSD Handbook, "Building Packages with poudriere",
https://docs.freebsd.org/en/books/handbook/ports/#poudriere-initialization
