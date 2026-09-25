---
name: ports-ports-clean-work
description: Free disk space by removing the temporary build directories (work directories) that port builds leave in /usr/ports, using only the base system.
handbook: ports/#ports-disk-space
handbook_commit: bdf18a0458
---

# Remove leftover port build directories

## What this does

Building a port unpacks and compiles its source in a temporary directory
called `work` (or `work-` followed by a name, for ports built in several
variants) inside the port's directory, such as `/usr/ports/misc/figlet/work`.
A build that finishes with `clean` removes it; a build that stopped part-way,
or was run without `clean`, leaves it behind, sometimes using gigabytes. This
skill lists those directories and removes them. The downloaded source files
in `/usr/ports/distfiles` and the ports tree itself are not touched.

## Before you start

- You need: a root shell and the Ports Collection in `/usr/ports` (skill
  `ports/ports-tree-git`).
- Make sure no port is being built right now (no `make`, portmaster or
  portupgrade running): its work directory would be removed under it.
- This changes: deletes every `work` and `work-*` directory inside a port's
  directory (`/usr/ports/CATEGORY/PORT/`), never under `distfiles` or
  `packages`, or under `Mk`, `Tools`, `Templates`, `Keywords` or a name
  starting with `.` (such as `.git`). Those are the only directories left
  out, named one by one; everything else two levels down is treated as a
  port. They are temporary; a later build creates them again.
- Time: seconds to a few minutes.
- Risk: low. There is no undo, but nothing needed is lost: the next build of
  a port unpacks its source again.

## Inputs

None.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.

| The line starts with | Do this |
|---|---|
| `14.`, `15.` or `16.` (including 14.0 to 14.3, end of life as of 2026-09-24) | go to step 2. The steps are the same on every release |
| anything else | stop, and report the line: this skill was not tested there |

## Step 2: Check the ports tree, and where builds put their work directories

Settings in `/etc/make.conf` (`WRKDIRPREFIX` or `WRKDIR`) can move work
directories out of `/usr/ports`; this skill only handles the normal place. To
find out, ask one port (`ports-mgmt/pkg`, which every ports tree has) where
its work directory would be. Run:

    ls /usr/ports/Mk/bsd.port.mk && make -C /usr/ports/ports-mgmt/pkg -V WRKDIR; echo "exit=$?"

| If you see | Do this |
|---|---|
| `/usr/ports/Mk/bsd.port.mk`, then exactly `/usr/ports/ports-mgmt/pkg/work`, then `exit=0` | go to step 3 |
| `/usr/ports/Mk/bsd.port.mk`, then any other path, then `exit=0` | work directories are kept somewhere else. Stop, and report the path: this skill does not handle that |
| `ls: /usr/ports/Mk/bsd.port.mk: No such file or directory`, then `exit=1` | there is no ports tree. Stop, and report it |
| anything else | stop, and report the full output |

## Step 3: List the work directories and their size

Run:

    find -H /usr/ports -mindepth 3 -maxdepth 3 -type d \( -name work -o -name 'work-*' \) ! -path '/usr/ports/.*' ! -path '/usr/ports/Mk/*' ! -path '/usr/ports/Tools/*' ! -path '/usr/ports/Templates/*' ! -path '/usr/ports/Keywords/*' ! -path '/usr/ports/distfiles/*' ! -path '/usr/ports/packages/*' -exec du -sh {} +; echo "exit=$?"

Expected: one line per leftover directory, with its size, then `exit=0`, such
as:

    1.2M	/usr/ports/misc/figlet/work
    exit=0

| If you see | Do this |
|---|---|
| only `exit=0` | there is nothing to remove. Stop here: the task is finished, with nothing changed |
| one or more lines, each a size, then a path under `/usr/ports/` ending in `/work` or in `/work-` and a name, then `exit=0` | go to step 4 |
| anything else | stop, and report the full output |

## Step 4: Remove them

Run:

    find -H /usr/ports -mindepth 3 -maxdepth 3 -type d \( -name work -o -name 'work-*' \) ! -path '/usr/ports/.*' ! -path '/usr/ports/Mk/*' ! -path '/usr/ports/Tools/*' ! -path '/usr/ports/Templates/*' ! -path '/usr/ports/Keywords/*' ! -path '/usr/ports/distfiles/*' ! -path '/usr/ports/packages/*' -exec rm -rf {} +; echo "exit=$?"

Expected: `exit=0`. Anything else: stop and report.

## Step 5: Verify

Run:

    find -H /usr/ports -mindepth 3 -maxdepth 3 -type d \( -name work -o -name 'work-*' \) ! -path '/usr/ports/.*' ! -path '/usr/ports/Mk/*' ! -path '/usr/ports/Tools/*' ! -path '/usr/ports/Templates/*' ! -path '/usr/ports/Keywords/*' ! -path '/usr/ports/distfiles/*' ! -path '/usr/ports/packages/*'; echo "exit=$?"

Expected: only `exit=0` (no directory is listed). Anything else (a
directory listed, any other line, or an exit other than 0): stop and report
the full output.

## Undo

None needed: the removed directories were temporary. Building a port again
(skill `ports/port-install`) recreates its work directory.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-25, snapshot 20260921 (a6deeaa2fb3b) | Ports tree `main`. |
| 15.1-RELEASE | verified | 2026-09-25 | Ports tree `2026Q3`. |
| 15.0-RELEASE | verified | 2026-09-25 | As 15.1. |
| 14.5-RELEASE | verified | 2026-09-25 | As 15.1. |
| 14.4-RELEASE | verified | 2026-09-25 | As 15.1. |
| 14.3-RELEASE (EoL) | verified | 2026-09-25 | As 15.1. |
| 14.2-RELEASE (EoL) | verified | 2026-09-25 | As 15.1. |
| 14.1-RELEASE (EoL) | verified | 2026-09-25 | As 15.1. |
| 14.0-RELEASE (EoL) | verified | 2026-09-25 | As 15.1. |

## Weak-model check

2026-09-25 (UTC): claude-haiku-4-5, given only this skill and a tool that
runs one command on the test machine, followed it on a freshly reset system of
every release above. Beforehand the ports tree was cloned and two ports were
left half-built: `misc/figlet` built but not installed, `sysutils/tree` only
unpacked, plus an empty `sysutils/tree/work-test`, and six directories that
must survive: `distfiles/keepme/work`, `Mk/Uses/work`, `Tools/scripts/work`,
`Templates/test/work`, `Keywords/test/work` and `packages/All/work`. A run counts only when the model said DONE AND the independent
check (`verify.sh`: no `work` or `work-*` directory left in a port's
directory, those six still there, the downloaded
sources still in `/usr/ports/distfiles`, `git status` shows the ports tree
unchanged in its tracked files, and nothing installed) passed: all 9 did, with the final text and
scripts. A manual review of the
command logs showed exactly the skill's five commands on every release.

## Not verified

- The directories left out are named one by one rather than with a pattern
  such as `[a-z]*`: in a locale such as `en_US.UTF-8`, `[a-z]` also matches
  capital letters (tried on 14.1: it matched `Mk/Uses/work`).
- A `work` that is a symbolic link (to space on another disk) is not a
  directory to `find -type d`, so it is neither listed nor removed.
- Nothing checks that no build is running; that is left to the reader
  ("Before you start").
- Step 2 asks one port. A setting in `/etc/make.conf` that moves work
  directories for some other ports only is not seen; those are then neither
  listed nor removed.
- If `/usr/ports` is a symbolic link, step 2 may print the real path instead
  of `/usr/ports/...` and stop; not tried.
- With work directories moved elsewhere, step 2 stops; removing them from
  such a place is not covered. Tried by hand on 14.1: with
  `WRKDIRPREFIX=/var/tmp/w` inside `.if ${.CURDIR:M/usr/ports/*}` in
  `/etc/make.conf`, asking the top of the tree showed nothing, while step 2's
  command showed `/var/tmp/w/usr/ports/ports-mgmt/pkg/work`.
- `-H` makes `find` follow `/usr/ports` itself if it is a symbolic link (for
  example to a tree on another disk); tried by hand on 14.1, not in the model
  runs.
- The `work-` pattern comes from the ports tree's own `.gitignore`, which
  lists `/*/*/work` and `/*/*/work-*`. In the test, the `work-` directory was
  an empty one made for the purpose, not left by a real build.

## Differences from the Handbook

- The Handbook removes work directories with `portsclean -C`, which needs
  portupgrade, a tool the Handbook marks deprecated (it prints a `Delete`
  line for each directory and removes it). The skill
  uses `find`, which is part of the base system.

## Source

FreeBSD Handbook, "Ports and Disk Space",
https://docs.freebsd.org/en/books/handbook/ports/#ports-disk-space
