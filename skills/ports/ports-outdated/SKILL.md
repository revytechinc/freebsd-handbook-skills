---
name: ports-ports-outdated
description: List the installed software that has a newer version in the Ports Collection, and show the recent notes in /usr/ports/UPDATING to read before upgrading.
handbook: ports/#ports-upgrading
handbook_commit: bdf18a0458
---

# See which installed software can be upgraded from ports

## What this does

Compares every installed package with the version in the Ports Collection
(`/usr/ports`) and lists the ones that are older. It also shows the newest
entries of `/usr/ports/UPDATING`, where the ports team announces changes that
need manual steps; the Handbook says to read it before any upgrade. Nothing is
changed.

## Before you start

- You need: a root shell, pkg installed, and an up-to-date Ports Collection in
  `/usr/ports` (skill `ports/ports-tree-git`).
- This changes: writes the list to `/root/outdated.txt` (replacing an older
  copy of that file). Nothing else.
- Time: seconds.
- Risk: none.

## Inputs

None.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.
The commands below are the same on every release.

## Step 2: Check the ports tree is there

Run:

    ls /usr/ports/Mk/bsd.port.mk; echo "exit=$?"

Expected: `/usr/ports/Mk/bsd.port.mk` and `exit=0`. If you see `No such file
or directory`, there is no ports tree: stop and report it.

## Step 3: List what is older than the ports tree

Run:

    pkg version -vl '<' > /root/outdated.txt; echo "exit=$?"; cat /root/outdated.txt

Expected: `exit=0`, then one line per package that is older than its port,
for example:

    exit=0
    expat-2.8.2                        <   needs updating (port has 2.8.4)
    git-2.54.0                         <   needs updating (port has 2.55.0)

If only `exit=0` is shown, nothing is older than the ports tree. Anything
other than `exit=0`: stop and report the output.

## Step 4: Show the newest notes in UPDATING

Run:

    head -40 /usr/ports/UPDATING; echo "exit=$?"

Expected: the file's introduction, then entries that start with a date such
as `20260910:`, each with `AFFECTS:` naming the ports concerned. Read them: if
an entry's `AFFECTS:` names a package from step 3, say so in your final
answer, because that upgrade needs the manual steps the entry describes.

## Step 5: Report

Write this line in your final answer:

- if step 3 listed packages: `RESULT: OUTDATED ` followed by the first word of
  each line from step 3 (the name and version, such as `expat-2.8.2`), in the
  order shown, separated by single spaces
- if step 3 listed nothing: `RESULT: nothing to update`

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | Packages and tree both `main`: nothing older (see Not verified). |
| 15.1-RELEASE | verified | 2026-09-24 | Quarterly packages, `main` tree: several packages listed. |
| 15.0-RELEASE | verified | 2026-09-24 | As 15.1. |
| 14.5-RELEASE | verified | 2026-09-24 | As 15.1. |
| 14.4-RELEASE | verified | 2026-09-24 | As 15.1. |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | As 15.1; no special setting needed. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill and a tool that runs
one command on the test machine, followed it on a freshly reset system of
every release above (ZFS-root test machines). This skill changes nothing, so
the independent check is the answer: a run counts only when the model said
DONE AND its final message contained the exact `RESULT:` line computed on the
machine before the run (`answer.sh`), unchanged after it: all 9 did. A manual
review of the command logs showed exactly the skill's four commands on every
release.

## Not verified

- The test used packages from the Quarterly branch with a `main` ports tree,
  so that some versions really differ. A machine whose packages and ports tree
  are on the same branch usually lists few or none.
- On 16.0-CURRENT packages and ports tree are both on `main`, so nothing was
  older than its port. For the test, `PORTREVISION=99` was added to the local
  `www/nginx-lite/Makefile`, so that nginx-lite was older than its port.
- Doing the upgrade itself (with a port-upgrade tool or `pkg upgrade`) is
  covered by other skills.

## Differences from the Handbook

- The Handbook shows `pkg version -l "<"`; the skill adds `-v`, which also
  prints the version the port has, and saves the list to `/root/outdated.txt`.

## Source

FreeBSD Handbook, "Upgrading Ports",
https://docs.freebsd.org/en/books/handbook/ports/#ports-upgrading
