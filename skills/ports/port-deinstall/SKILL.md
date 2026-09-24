---
name: ports-port-deinstall
description: Uninstall a program that was installed from the Ports Collection, using make deinstall in its port directory, after checking that nothing else depends on it.
handbook: ports/#ports-removing
handbook_commit: bdf18a0458
---

# Uninstall a port

## What this does

Removes a program that was built and installed from the Ports Collection,
from its port directory. `make deinstall` does **not** check whether other
installed software needs the program, and removes it anyway, which can break
that software. This skill checks first and stops if anything depends on it.
(`ports/pkg-delete` does the same job by package name.)

## Before you start

- You need: a root shell, pkg installed, and the Ports Collection in
  `/usr/ports` (skill `ports/ports-tree-git`).
- This changes: removes the program's files from `/usr/local`.
- Time: seconds.
- Risk: medium. Undo builds it again (`ports/port-install`); changes made to
  its configuration files are lost.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `PORT` | the port's directory under `/usr/ports`: category, `/`, name | `misc/figlet` |

Everywhere below, replace `PORT` with this value, exactly as given. It must be
one word, a `/`, and another word; each word must start with a letter or a
digit, and may contain only letters, digits, and the characters `.` `_` `+`
`-`. If it does not, stop and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.
The commands below are the same on every release (removing works even where
building is refused because the release has reached end of life).

## Step 2: Check the port exists

Run:

    ls -d /usr/ports; ls /usr/ports/PORT/Makefile; echo "exit=$?"

| If you see | Do this |
|---|---|
| `/usr/ports`, then `/usr/ports/PORT/Makefile`, then `exit=0` | go to step 3 |
| `ls: /usr/ports: No such file or directory` | there is no ports tree. Stop, and report it |
| `/usr/ports`, then `ls: /usr/ports/PORT/Makefile: No such file or directory` | there is no such port. Stop, and report it |

## Step 3: Find its package name

Run:

    make -C /usr/ports/PORT -V PKGBASE; echo "exit=$?"

| If you see | Do this |
|---|---|
| one word (for example `figlet`), then `exit=0` | that word is `NAME`. Go to step 4 |
| anything else (an empty line, an error, or a status other than 0) | stop, and report the full output |

## Step 4: Check it is installed and that nothing depends on it

Run, replacing `NAME` with the word from step 3:

    pkg info -e NAME && pkg query '%rn' NAME; echo "exit=$?"

| If you see | Do this |
|---|---|
| only `exit=0` | installed, and nothing depends on it. Go to step 5 |
| one or more package names, then `exit=0` | those packages need it and would break. Do NOT go on. Stop, report the names, and end with FAILED |
| only `exit=1` | `NAME` is not installed. There is nothing to remove. The task is finished |
| anything else | stop, and report the full output |

## Step 5: Uninstall it

Run:

    make -C /usr/ports/PORT deinstall; echo "exit=$?"

Expected: `Installed packages to be REMOVED:` with the package, lines such as
`[1/1] Deinstalling figlet-2.2.5_1...`, then `exit=0`. Anything else: stop and
report the output.

## Step 6: Verify

Run:

    pkg info -e NAME; echo "exit=$?"

Expected: only `exit=1` (no longer installed). If you see `exit=0`, the task
did not succeed: stop and report.

## Undo

Build and install it again with `ports/port-install`.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | |
| 15.1-RELEASE | verified | 2026-09-24 |  |
| 15.0-RELEASE | verified | 2026-09-24 |  |
| 14.5-RELEASE | verified | 2026-09-24 |  |
| 14.4-RELEASE | verified | 2026-09-24 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | Removing works without any special setting (building needs one). |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill, the input
`PORT=sysutils/tree` (deliberately not the port in the skill's examples), and
a tool that runs one command on the test machine, followed it on a freshly
reset system of every release above, with tree built
and installed from the ports tree beforehand. A run counts only when the model
said DONE AND the independent check (`verify.sh`: tree gone, and no other
package removed, compared with the list saved before the run) passed: all 9
did with this final text (on the UFS-root test machines; an earlier version
also passed on the ZFS-root ones). A manual review of
the command logs showed exactly the skill's six commands on every release,
including the check for dependents.

## Not verified

- Not run by the weak model: the "not installed" row of step 4 (the exact
  step 4 command with a name that is not installed printed only `exit=1` on
  14.0) and its stop row (the query part alone, `pkg query '%rn'`, listed
  `git` and `nginx-lite` for pcre2 on 14.5, and `git` for curl on 14.0).

## Differences from the Handbook

- The Handbook says that if other software depends on the port, "this
  information will be displayed but the uninstallation will proceed". In the
  tests nothing was displayed: `make deinstall` of `devel/pcre2` on 14.5
  removed it silently while nginx-lite needed it, and nginx then failed with
  `Shared object "libpcre2-8.so.0" not found`; on 14.0, `make deinstall` of
  `ftp/curl` removed it although git needs it. Step 4 exists for this.
- The Handbook's example, `sysutils/lsof`, cannot be built on a standard
  install (it needs `/usr/src`), so it would not be there to remove.

## Source

FreeBSD Handbook, "Removing Installed Ports",
https://docs.freebsd.org/en/books/handbook/ports/#ports-removing
