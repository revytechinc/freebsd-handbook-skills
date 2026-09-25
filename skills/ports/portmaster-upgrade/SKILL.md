---
name: ports-portmaster-upgrade
description: Upgrade every installed port that the Ports Collection in /usr/ports has a newer version of, by rebuilding it from source with portmaster, without any questions or menus.
handbook: ports/#portmaster
handbook_commit: bdf18a0458
---

# Upgrade outdated ports with portmaster

## What this does

portmaster is a small tool that upgrades installed programs by building them
again from the Ports Collection in `/usr/ports`. This skill lists what is
outdated, then has portmaster rebuild and reinstall all of it in one run,
with no questions and no option menus.

Use it when you build programs from ports. If all your programs come from
packages, use `ports/pkg-upgrade` instead: it is much faster and needs no
ports tree.

## Before you start

- You need: a root shell, network access to FreeBSD's servers, the Ports
  Collection in `/usr/ports` (skill `ports/ports-tree-git`), and portmaster
  installed (skill `ports/pkg-install` with `PACKAGE=portmaster`).
- Read `/usr/ports/UPDATING` first (skill `ports/ports-outdated` shows the
  newest entries): some upgrades need a manual step that portmaster does not
  do.
- This changes: rebuilds and reinstalls every outdated program under
  `/usr/local`, and installs any tools needed to build them (such as
  `gmake`), which stay installed.
- Time: from a minute to many hours, depending on how much is outdated.
- Risk: medium. The old versions are not kept, so there is no simple undo.

## Inputs

None.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.

| The line starts with | Your release group | Use in step 4 |
|---|---|---|
| `14.0-`, `14.1-`, `14.2-` or `14.3-` (end of life as of 2026-09-24) | EoL | the command marked **EoL** |
| `14.4-`, `14.5-`, `15.` or `16.` | current | the command marked **current** |
| anything else | stop, and report the line: this skill was not tested there | |

Why: the Ports Collection refuses to build anything on a release that has
reached end of life. The **EoL** command sets `ALLOW_UNSUPPORTED_SYSTEM=yes`,
which lets the build go ahead; the ports team gives no support for builds
made that way.

## Step 2: Check portmaster and the ports tree

Run:

    pkg info -E portmaster && ls /usr/ports/Mk/bsd.port.mk; echo "exit=$?"

| If you see | Do this |
|---|---|
| a line such as `portmaster-3.35`, then `/usr/ports/Mk/bsd.port.mk`, then `exit=0` | go to step 3 |
| `pkg: No package(s) matching portmaster`, then `exit=1` | portmaster is not installed. Stop, and report it (see `ports/pkg-install`) |
| a `portmaster-` line, then `ls: /usr/ports/Mk/bsd.port.mk: No such file or directory` and `exit=1` | there is no ports tree. Stop, and report it (see `ports/ports-tree-git`) |
| anything else | stop, and report the full output |

## Step 3: List what is outdated

Run:

    portmaster -L > /root/portmaster-list.txt 2>&1; echo "exit=$?"; grep -e 'New version available' -e 'new version' /root/portmaster-list.txt

Expected: `exit=0`, then either one line saying nothing is outdated:

    exit=0
    	===>>> There are no new versions available

or one line per outdated program, then a count, such as:

    exit=0
    	===>>> New version available: figlet-2.2.5_2
    	===>>> 1 has a new version available

| If you see | Do this |
|---|---|
| `exit=0`, then `There are no new versions available` | nothing to upgrade. Stop here: the task is finished, with nothing changed |
| `exit=0`, then one or more `New version available:` lines and a count | write the names down, and go to step 4 |
| anything else | stop, and report the full output |

## Step 4: Upgrade

Run the command for your release group. `-a` means all outdated ports, `-G`
means no option menus, `--no-confirm` and `-y` answer every question with
yes, and `BATCH=yes` makes the builds use default options. The output is
long, so it goes into a file in root's home directory. The command then shows
portmaster's summary of what it did (empty if it did not finish), and after
`--- end of log:` the last lines of the log:

- **current**: `env BATCH=yes portmaster -a -G --no-confirm -y > /root/portmaster.log 2>&1; echo "exit=$?"; sed -n '/The following actions were performed/,$p' /root/portmaster.log; echo "--- end of log:"; tail -3 /root/portmaster.log`
- **EoL**: `env BATCH=yes ALLOW_UNSUPPORTED_SYSTEM=yes portmaster -a -G --no-confirm -y > /root/portmaster.log 2>&1; echo "exit=$?"; sed -n '/The following actions were performed/,$p' /root/portmaster.log; echo "--- end of log:"; tail -3 /root/portmaster.log`

Expected, after anything from a minute to hours, `exit=0` and a summary such
as:

    exit=0
    ===>>> The following actions were performed:
    	Installation of devel/gmake (gmake-4.4.1)
    	Upgrade of figlet-2.2.5_1 to figlet-2.2.5_2

    --- end of log:
    	Installation of devel/gmake (gmake-4.4.1)
    	Upgrade of figlet-2.2.5_1 to figlet-2.2.5_2


Lines may begin with odd characters such as `]0;`: that is portmaster
setting the terminal's title, and is harmless.

| If you see | Do this |
|---|---|
| `exit=0` and `The following actions were performed:` with an `Upgrade of` line for each name from step 3 | go to step 5 |
| `exit=1` and `You can restart from the point of failure with this command line:`, and you used the **current** command on a release that step 1 says is EoL | you used the wrong command. Run the **EoL** command. (portmaster also saved the failed command in `/root/portmasterfail.txt`; that file is only a note and can stay) |
| anything else | stop: report the last lines shown, run no other command, and end with FAILED. The ports already upgraded stay upgraded |

## Step 5: Verify

Run:

    portmaster -L 2>&1 | grep -e 'New version available' -e 'new version'

| If you see | Do this |
|---|---|
| exactly one line, ending in `===>>> There are no new versions available` | finished |
| one or more `New version available:` lines | stop, and report them |
| anything else, including no output at all | portmaster could not check. Stop, and report the output |

## Undo

There is no simple undo: with the options above, portmaster does not keep
the old versions. The
build log `/root/portmaster.log` and the list `/root/portmaster-list.txt` can
be removed with `rm /root/portmaster.log /root/portmaster-list.txt`. Build
tools that were installed stay installed; `ports/pkg-autoremove` removes the
ones nothing needs.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | Ports tree `main`. |
| 15.1-RELEASE | verified | 2026-09-24 | Ports tree `2026Q3`. |
| 15.0-RELEASE | verified | 2026-09-24 | As 15.1. |
| 14.5-RELEASE | verified | 2026-09-24 | As 15.1. |
| 14.4-RELEASE | verified | 2026-09-24 | As 15.1. |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | Needs the **EoL** command. Without `ALLOW_UNSUPPORTED_SYSTEM=yes` (seen on 14.1), portmaster stops with `exit=1` and writes `~/portmasterfail.txt`. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill and a tool that
runs one command on the test machine, followed it on a freshly reset system of
every release above. Beforehand the machine got the ports tree, portmaster and
`tree` from packages, and the local ports tree was made to offer a newer
`tree` (its revision raised to `_99`); the skill's examples use `figlet`. A
run counts only when the model said DONE AND the independent check
(`verify.sh`: `tree` is now the `_99` version built from ports, portmaster
lists nothing to upgrade, `tree` runs, and no other package changed apart
from build tools added) passed: all 9 did, with the final text and scripts. A manual review of the command
logs showed the skill's five commands on every release, with the **EoL**
command on 14.0 to 14.3 only.

## Not verified

- The Handbook's `-b`, which makes portmaster keep a backup package of each
  old version, was not tested.
- Steps 3 and 5 show only portmaster's lines about new versions; other
  messages in the list (for example about a port that was moved or removed
  from the tree) are not shown.
- The test network allows only FreeBSD's own servers, so sources came from
  FreeBSD's copy (`distcache.FreeBSD.org`).
- Only one outdated port was tested at a time, made outdated on purpose by
  raising its revision in the local ports tree. Large upgrades, and upgrades
  that need a step from `/usr/ports/UPDATING`, were not tried.

## Differences from the Handbook

- The Handbook runs `portmaster -a` interactively; it asks questions and can
  open option menus. The skill adds `-G --no-confirm -y` and `BATCH=yes` so
  nothing waits for the keyboard.
- On 14.0 to 14.3 (end of life) the Ports Collection refuses to build unless
  `ALLOW_UNSUPPORTED_SYSTEM` is set; the Handbook does not mention this.

## Source

FreeBSD Handbook, "Upgrading Ports Using Portmaster",
https://docs.freebsd.org/en/books/handbook/ports/#portmaster
