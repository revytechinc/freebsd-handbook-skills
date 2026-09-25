---
name: ports-ports-clean-distfiles
description: Free disk space by deleting downloaded port source files in /usr/ports/distfiles that no installed port needs, with portmaster, without questions.
handbook: ports/#ports-disk-space
handbook_commit: bdf18a0458
---

# Remove stale port source files

## What this does

Every port build first downloads the program's source files (called
*distfiles*) into `/usr/ports/distfiles`, and they stay there. Over time old
versions, and sources of ports that were later removed, pile up. This skill
has portmaster delete every file there that no **installed** port needs, with
no questions, and then checks that nothing stale is left.

## Before you start

- You need: a root shell, the Ports Collection in `/usr/ports` (skill
  `ports/ports-tree-git`), and portmaster installed (skill `ports/pkg-install`
  with `PACKAGE=portmaster`).
- Make sure no port is being built or downloaded right now (this skill does
  not check).
- This changes: deletes files in `/usr/ports/distfiles` (and in its folders; a folder left empty is removed too)
  that belong to no installed port. That includes sources downloaded for a
  port you have not installed yet, and the sources of the port versions you
  had before an upgrade.
- Time: seconds to a few minutes.
- Risk: low. There is no undo. portmaster keeps only the sources that the
  current ports tree lists for installed ports, so the sources of an older
  installed version (or of an installed port no longer in the tree) are
  deleted too; the next build downloads what the tree lists, if it is still
  available.

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

## Step 2: Check portmaster, the ports tree, and where sources are kept

Settings in `/etc/make.conf` (`DISTDIR`) can keep sources somewhere other than
`/usr/ports/distfiles`; this skill only handles the normal place. Run:

    pkg info -E portmaster && ls /usr/ports/Mk/bsd.port.mk && make -C /usr/ports/ports-mgmt/pkg -V DISTDIR && ls -d /usr/ports/distfiles; echo "exit=$?"

| If you see | Do this |
|---|---|
| a line such as `portmaster-3.35`, `/usr/ports/Mk/bsd.port.mk`, then `/usr/ports/distfiles` twice, then `exit=0` | go to step 3 |
| the first three lines as above, then `ls: /usr/ports/distfiles: No such file or directory` and `exit=1` | nothing has been downloaded yet. Stop here: the task is finished, with nothing changed |
| `pkg: No package(s) matching portmaster`, then `exit=1` | portmaster is not installed. Stop, and report it (see `ports/pkg-install`) |
| a `portmaster-` line, then `ls: /usr/ports/Mk/bsd.port.mk: No such file or directory` and `exit=1` | there is no ports tree. Stop, and report it (see `ports/ports-tree-git`) |
| a `portmaster-` line and `/usr/ports/Mk/bsd.port.mk`, then any path other than `/usr/ports/distfiles` | sources are kept somewhere else. Stop, and report the path: this skill does not handle that |
| anything else | stop, and report the full output |

## Step 3: Note the space used now

Run:

    du -sh /usr/ports/distfiles; echo "exit=$?"

Expected: a size and the folder, then `exit=0`, such as:

    1.6M	/usr/ports/distfiles
    exit=0

Write the size down. Anything else: stop and report.

## Step 4: Delete the stale files

`-y` answers every question with yes. The output goes into a file in root's
home directory and is then shown. Run:

    portmaster --clean-distfiles -y > /root/portmaster-distfiles.log 2>&1; echo "exit=$?"; cat /root/portmaster-distfiles.log

Expected: `exit=0`, two lines starting `===>>>`, then one `Deleting` line per
file removed (none if nothing was stale), with blank lines between, such as:

    exit=0
    ===>>> Gathering distinfo list for installed ports

    ===>>> Checking for stale distfiles

           Deleting figlet-2.2.5.tar.gz

           Deleting stale-1.0.tgz

| If you see | Do this |
|---|---|
| `exit=0`, `===>>> Gathering distinfo list for installed ports`, `===>>> Checking for stale distfiles`, and otherwise only `Deleting` lines and blank lines | go to step 5 |
| anything else, such as a line with `Aborting` or `Cannot`, or any other line | stop: report the full output, and end with FAILED |

## Step 5: Verify

Run the same command again, into a second log file. With nothing stale left,
it must delete nothing:

    portmaster --clean-distfiles -y > /root/portmaster-distfiles-2.log 2>&1; echo "exit=$?"; cat /root/portmaster-distfiles-2.log; du -sh /usr/ports/distfiles

| If you see | Do this |
|---|---|
| `exit=0`, the two `===>>>` lines, no `Deleting` line and no other line apart from blank lines, then a size and `/usr/ports/distfiles` | finished. Report the size from step 3, this size, and the files deleted in step 4 |
| any `Deleting` line, or anything else | stop, and report the full output |

## Undo

None: deleted source files are downloaded again when a port that needs them
is built. The logs can be removed with `rm /root/portmaster-distfiles.log
/root/portmaster-distfiles-2.log`.

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
every release above. Beforehand the ports tree was cloned, portmaster and
`tree` were installed from packages, and `/usr/ports/distfiles` held the
sources of `tree` (installed) and `figlet` (not installed) plus two made-up
stale files, one in a folder. A run counts only when the model said DONE AND
the independent check (`verify.sh`: the source of `tree` is still there, the
`figlet` source and both stale files are gone, no index file was downloaded,
`git status` shows the tree's tracked files unchanged, and `tree` is still
installed) passed: all 9 did, with the final text and scripts. A manual
review of the command logs showed exactly the skill's five commands on every
release.

## Not verified

- portmaster decides what is needed from the list of installed packages. A
  package database that cannot be read would make every file look stale;
  step 2's `pkg info` would then fail first, but that case was not tried.
- Sources kept elsewhere with `DISTDIR`: step 2 stops; not tried.
- Step 5 shows that nothing stale is left, not that every needed source
  remained: if portmaster wrongly deleted a needed file, step 5 would not
  show it. The test checked this separately (the installed port's source
  stayed).

## Differences from the Handbook

- The Handbook runs `portmaster --clean-distfiles` interactively (it asks
  about each file). The skill adds `-y`.
- The Handbook also gives `portsclean -D` and `portsclean -DD`, from the
  deprecated portupgrade. Tried by hand on 15.1: `portsclean -D` first
  downloads the index of FreeBSD's newest ports branch into `/usr/ports` and
  uses it to decide what is still needed, which on a quarterly ports tree
  describes different versions; it also deleted without asking. The skill
  does not use it.
- With no `/usr/ports/distfiles` folder at all, portmaster prints `Cannot cd
  to /usr/ports/distfiles/` and `Aborting update` and exits 1 (tried on
  15.1); step 2 finishes early instead.

## Source

FreeBSD Handbook, "Ports and Disk Space",
https://docs.freebsd.org/en/books/handbook/ports/#ports-disk-space
