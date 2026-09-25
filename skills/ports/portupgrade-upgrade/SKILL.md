---
name: ports-portupgrade-upgrade
description: Upgrade every installed port that the Ports Collection in /usr/ports has a newer version of, with portupgrade (deprecated), without any questions or menus.
handbook: ports/#portupgrade
handbook_commit: bdf18a0458
---

# Upgrade outdated ports with portupgrade

## What this does

portupgrade is an older tool, written in Ruby, that upgrades installed
programs by building them again from the Ports Collection in `/usr/ports`.
The Handbook marks it **deprecated**: it will be removed. This skill checks
the package database, lists what is outdated, has portupgrade rebuild all of
it with no questions, and then removes the index file portupgrade downloads,
which does not match the ports tree.

If you are choosing a tool, prefer `ports/portmaster-upgrade`. If all your
programs come from packages, use `ports/pkg-upgrade` instead.

## Before you start

- You need: a root shell, network access to FreeBSD's servers, the Ports
  Collection in `/usr/ports` (skill `ports/ports-tree-git`), and portupgrade
  installed (skill `ports/pkg-install` with `PACKAGE=portupgrade`).
- Read `/usr/ports/UPDATING` first (skill `ports/ports-outdated` shows the
  newest entries): some upgrades need a manual step that portupgrade does not
  do.
- This changes: rebuilds and reinstalls every outdated program under
  `/usr/local`, and installs any tools needed to build them (such as
  `gmake`), which stay installed.
- Time: from a minute to many hours, depending on how much is outdated.
- Risk: medium. There is no simple undo.

## Inputs

None.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.

| The line starts with | Your release group | `N` (used in step 7) |
|---|---|---|
| `14.0-`, `14.1-`, `14.2-` or `14.3-` (end of life as of 2026-09-24) | EoL | `14` |
| `14.4-` or `14.5-` | current | `14` |
| `15.` | current | `15` |
| `16.` | current | `16` |
| anything else | stop, and report the line: this skill was not tested there | |

Why: the Ports Collection refuses to build anything on a release that has
reached end of life. The **EoL** command in step 5 sets
`ALLOW_UNSUPPORTED_SYSTEM=yes`, which lets the build go ahead; the ports team
gives no support for builds made that way.

## Step 2: Check portupgrade, the ports tree, and any index file

Run:

    pkg info -E portupgrade && ls /usr/ports/Mk/bsd.port.mk; echo "exit=$?"; ls /usr/ports | grep '^INDEX'; echo "exit=$?"

| If you see | Do this |
|---|---|
| a line such as `portupgrade-2.4.16_4,2`, then `/usr/ports/Mk/bsd.port.mk`, `exit=0`, then `exit=1` | go to step 3. Write down: there was no index file |
| the same first three lines, then one or more names starting with `INDEX` and `exit=0` | go to step 3. Write down: an index file was already there, so step 7 is skipped |
| first `pkg: No package(s) matching portupgrade` and `exit=1` (the lines after it do not matter) | portupgrade is not installed. Stop, and report it (see `ports/pkg-install`) |
| a `portupgrade-` line, then `ls: /usr/ports/Mk/bsd.port.mk: No such file or directory` and `exit=1` | there is no ports tree. Stop, and report it (see `ports/ports-tree-git`) |
| anything else | stop, and report the full output |

## Step 3: Check the package database

Check that every installed package has the packages it needs (a broken
database makes portupgrade stop part-way). Run:

    pkg check -d -n; echo "exit=$?"

| If you see | Do this |
|---|---|
| `Checking all packages: .......... done` (the number of dots varies), then `exit=0` | go to step 4 |
| anything else, such as lines naming a missing dependency | stop, and report the full output. Repairing the package database is not part of this skill |

## Step 4: List what is outdated

Run:

    pkg version -vPl '<'; echo "exit=$?"

`-P` compares the installed programs with the ports tree itself. (Without it,
pkg uses an index file if one is there, and the one portupgrade downloads
describes a different branch, so the list would be wrong.)

Expected: one line per outdated program, then `exit=0`, such as:

    figlet-2.2.5_1                     <   needs updating (port has 2.2.5_2)
    exit=0

| If you see | Do this |
|---|---|
| only `exit=0` | nothing is outdated. Stop here: the task is finished, with nothing changed |
| one or more `needs updating (port has ...)` lines, then `exit=0` | write the names down, and go to step 5 |
| anything else | stop, and report the full output |

## Step 5: Upgrade

Run the command for your release group. `-a` means all outdated ports,
`--batch` and `--yes` mean no menus and no questions, and `BATCH=yes` makes
the builds use default options. The output is long, so it goes into a file in
root's home directory, and only portupgrade's list of results is shown:

- **current**: `env BATCH=yes portupgrade -a --batch --yes > /root/portupgrade.log 2>&1; echo "exit=$?"; sed -n '/Listing the results/,$p' /root/portupgrade.log | grep -v -e '- base/.*(port directory error)'`
- **EoL**: `env BATCH=yes ALLOW_UNSUPPORTED_SYSTEM=yes portupgrade -a --batch --yes > /root/portupgrade.log 2>&1; echo "exit=$?"; sed -n '/Listing the results/,$p' /root/portupgrade.log | grep -v -e '- base/.*(port directory error)'`

Expected, after anything from a minute to hours, something like:

    exit=0
    --->  Listing the results (+:done / -:ignored / *:skipped / !:failed)
    	+ misc/figlet (figlet-2.2.5_1 -> figlet-2.2.5_2)
    --->  Packages processed: 1 done, 499 ignored, 0 skipped and 0 failed
    --->  Session ended at: Fri, 25 Sep 2026 00:55:12 +0000 (consumed 00:00:22)

The `ignored` count is normal. On 15 and 16, the base system's own packages
(`base/FreeBSD-...`) have no port, so portupgrade ignores them; the `grep -v`
hides the one `- base/...` line it prints for each, and nothing else. A line mentioning `bdb.so: warning:
redefining 'object_id'` is harmless.

| If you see | Do this |
|---|---|
| `exit=0`, a `+` line for each name from step 4, and `0 skipped and 0 failed` | go to step 6 |
| `exit=1`, a `!` line ending in `(unknown build error)`, and you used the **current** command on a release that step 1 says is EoL | you used the wrong command. Run the **EoL** command |
| anything else | stop: report the lines shown, run no other command, and end with FAILED. The ports already upgraded stay upgraded |

## Step 6: Verify

Run:

    pkg version -vPl '<'; echo "exit=$?"

| If you see | Do this |
|---|---|
| only `exit=0` | go to step 7 |
| one or more `needs updating` lines | stop, and report them |
| anything else | stop, and report the full output |

## Step 7: Remove the downloaded index

portupgrade downloaded `/usr/ports/INDEX-N` and made `/usr/ports/INDEX-N.db`
from it. That index describes FreeBSD's newest ports branch, not your ports
tree, so other tools that read it would show wrong versions. If step 2 found
an index file already there, skip this step: it was not made by this skill.
Otherwise run (with `N` from step 1):

    rm -f /usr/ports/INDEX-N /usr/ports/INDEX-N.db; ls /usr/ports | grep '^INDEX'; echo "exit=$?"

Expected: only `exit=1` (nothing starting with `INDEX` is left). Anything
else: stop and report.

## Undo

There is no simple undo: portupgrade does not keep the old versions. The log
`/root/portupgrade.log` can be removed with `rm /root/portupgrade.log`. Build
tools that were installed stay installed; `ports/pkg-autoremove` removes the
ones nothing needs.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-25, snapshot 20260921 (a6deeaa2fb3b) | Ports tree `main`. |
| 15.1-RELEASE | verified | 2026-09-25 | Ports tree `2026Q3`. |
| 15.0-RELEASE | verified | 2026-09-25 | As 15.1. |
| 14.5-RELEASE | verified | 2026-09-25 | As 15.1. |
| 14.4-RELEASE | verified | 2026-09-25 | As 15.1. |
| 14.3-RELEASE (EoL) | verified | 2026-09-25 | Needs the **EoL** command. Without `ALLOW_UNSUPPORTED_SYSTEM=yes` portupgrade reports `! sysutils/tree (tree-2.3.2)	(unknown build error)` and `exit=1`; the log shows `Ports Collection support for your FreeBSD version has ended`. |
| 14.2-RELEASE (EoL) | verified | 2026-09-25 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-25 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-25 | As 14.3. |

## Weak-model check

2026-09-25 (UTC): claude-haiku-4-5, given only this skill and a tool that
runs one command on the test machine, followed it on a freshly reset system of
every release above. Beforehand the machine got the ports tree, portupgrade
and `tree` from packages, and the local ports tree was made to offer a newer
`tree` (its revision raised to `_99`); the skill's examples use `figlet`. A
run counts only when the model said DONE AND the independent check
(`verify.sh`: `tree` is now the `_99` version built locally, `pkg version -P`
lists nothing outdated, no `INDEX` file is left in `/usr/ports`, `tree` runs,
and no other package changed apart from build tools added) passed: all 9 did,
with the final text and scripts.
A manual review of the command logs showed the skill's commands on every
release, in order, with the **EoL** command on 14.0 to 14.3 only.

## Not verified

- The test network allows only FreeBSD's own servers, so sources came from
  FreeBSD's copy (`distcache.FreeBSD.org`).
- Only one outdated port was tested at a time, made outdated on purpose by
  raising its revision in the local ports tree. Large upgrades were not
  tried.
- The failure without `ALLOW_UNSUPPORTED_SYSTEM=yes` was seen on 14.1; on
  14.0, 14.2 and 14.3 only the **EoL** command was run.
- The case where an `INDEX` file was already in `/usr/ports` before step 2
  (step 7 skipped) was not tried; portupgrade may overwrite such a file with
  the newest branch's index.
- `pkg version -P` prints nothing for a port it cannot compare (for example
  one missing from the tree); steps 4 and 6 do not show those.
- The Handbook's other forms (`portupgrade -R NAME`, `-P`, `-PP`, `-F`) were
  not tested.

## Differences from the Handbook

- The Handbook says to run `pkgdb -F` first. It no longer works with pkg: on
  14.1 and 15.1 it prints `pkgdb -F not supported with PKGNG yet. Use 'pkg check' directly.`
  The skill runs `pkg check -d -n` instead.
- The Handbook runs `portupgrade -a` interactively. The skill adds `--batch
  --yes` and `BATCH=yes` so nothing waits for the keyboard.
- Found in testing, not in the Handbook: portupgrade downloads the index for
  FreeBSD's newest ports branch (`INDEX-N`) into `/usr/ports`. On a quarterly
  ports tree it does not match, and plain `pkg version` then reports programs
  as outdated that are not (on 15.1: `pcre2`, `pkg`, `readline` and others).
  The skill compares with `pkg version -P` and removes the file afterwards.
  portupgrade's own `portversion` uses that index too, which is why the
  skill does not use it.
- On 14.0 to 14.3 (end of life) the Ports Collection refuses to build unless
  `ALLOW_UNSUPPORTED_SYSTEM` is set; the Handbook does not mention this.

## Source

FreeBSD Handbook, "Upgrading Ports Using Portupgrade",
https://docs.freebsd.org/en/books/handbook/ports/#portupgrade
