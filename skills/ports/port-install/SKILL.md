---
name: ports-port-install
description: Build one program from the Ports Collection in /usr/ports and install it, without any interactive option menus.
handbook: ports/#ports-using
handbook_commit: bdf18a0458
---

# Build and install a port

## What this does

Builds one program from source using its port in `/usr/ports`, installs it,
and cleans up the build files. pkg records the result like any other package,
so pkg can later show, lock or remove it.

## Before you start

- You need: a root shell, network access to FreeBSD's servers, pkg installed
  (skill `ports/pkg-bootstrap`), and the Ports Collection in `/usr/ports`
  (skill `ports/ports-tree-git`, which picks the branch matching the machine's
  packages; mixing branches causes conflicts).
- This changes: builds and installs the port, and any ports it needs to be
  built, under `/usr/local`. Downloaded source files stay in
  `/usr/ports/distfiles`.
- Time: seconds for a small program, much longer for large ones.
- Risk: low. Undo removes the program.

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

| The line starts with | Your release group | Use in step 4 |
|---|---|---|
| `14.0-`, `14.1-`, `14.2-` or `14.3-` (end of life as of 2026-09-24) | EoL | the command marked **EoL** |
| anything else (`14.4-`, `14.5-`, `15.`, `16.`) | current | the command marked **current** |

Why: the Ports Collection refuses to build anything on a release that has
reached end of life. It stops with `Ports Collection support for your FreeBSD
version has ended, and no ports are guaranteed to build on this system.` The
**EoL** command sets `ALLOW_UNSUPPORTED_SYSTEM=yes`, which lets the build go
ahead; the ports team gives no support for builds made that way.

## Step 2: Check the port exists

Run:

    ls -d /usr/ports; ls /usr/ports/PORT/Makefile; echo "exit=$?"

| If you see | Do this |
|---|---|
| `/usr/ports`, then `/usr/ports/PORT/Makefile`, then `exit=0` | go to step 3 |
| `ls: /usr/ports: No such file or directory` | there is no ports tree. Stop, and report it (see `ports/ports-tree-git`) |
| `/usr/ports`, then `ls: /usr/ports/PORT/Makefile: No such file or directory` | there is no such port. Stop, and report it |

## Step 3: Check it is not installed already

Run:

    pkg info -E $(make -C /usr/ports/PORT -V PKGBASE); echo "exit=$?"

| If you see | Do this |
|---|---|
| only `exit=1` | not installed. Go to step 4 |
| a line such as `figlet-2.2.5_1`, then `exit=0` | already installed. Stop, and report it: this skill does not reinstall |
| anything else | stop, and report the full output |

## Step 4: Build and install

Run the command for your release group. `BATCH=yes` makes the build use
default options instead of opening option menus that wait for keyboard input.
The build output is long, so it goes into a file in root's own home
directory (not `/tmp`, which every user can write to) and only the end is
shown:

- **current**: `make -C /usr/ports/PORT BATCH=yes install clean > /root/port-build.log 2>&1; echo "exit=$?"; tail -4 /root/port-build.log`
- **EoL**: `make -C /usr/ports/PORT BATCH=yes ALLOW_UNSUPPORTED_SYSTEM=yes install clean > /root/port-build.log 2>&1; echo "exit=$?"; tail -4 /root/port-build.log`

Expected, after anything from seconds to a long time, `exit=0` and last lines
such as (for `misc/figlet`):

    exit=0
    ===>   Registering installation for figlet-2.2.5_1
    Installing figlet-2.2.5_1...
    ===>  Cleaning for figlet-2.2.5_1

Lines in the log such as `=> Attempting to fetch ...` followed by an error are
normal: the build tries several download sites in turn.

| If you see | Do this |
|---|---|
| `exit=0` first | go to step 5 |
| `Ports Collection support for your FreeBSD version has ended` (you used the **current** command) | the release has reached end of life since this skill was written. Run the **EoL** command instead |
| anything else | stop: report the last lines shown, run no other command, and end with FAILED |

## Step 5: Verify

Run:

    pkg query '%n %v %o' $(make -C /usr/ports/PORT -V PKGBASE); echo "exit=$?"

Expected: one line with the name, the version and `PORT`, for example
`figlet 2.2.5_1 misc/figlet`, then `exit=0`. Otherwise stop and report.

## Undo

Remove the build log (`rm /root/port-build.log`), and remove the program with
the skill `ports/pkg-delete`, using the name shown in
step 5. Ports that were built only because this one needed them stay
installed; `ports/pkg-autoremove` removes them.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | Ports tree `main`. |
| 15.1-RELEASE | verified | 2026-09-24 | Ports tree `2026Q3`. |
| 15.0-RELEASE | verified | 2026-09-24 | As 15.1. |
| 14.5-RELEASE | verified | 2026-09-24 | As 15.1. |
| 14.4-RELEASE | verified | 2026-09-24 | As 15.1. |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | Needs the **EoL** command (`ALLOW_UNSUPPORTED_SYSTEM=yes`); without it the build stops at once. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill, the input
`PORT=sysutils/tree` (deliberately not the port in the skill's examples), and
a tool that runs one command on the test machine, followed it on a freshly
reset system of every release above, with the ports tree cloned beforehand. A
run counts only when the model said DONE AND the independent check
(`verify.sh`: tree installed with origin `sysutils/tree`, not from a
repository, its source downloaded into `/usr/ports/distfiles`, and running) passed: all 9 did. The first round failed on 14.0 to
14.3, where the Ports Collection refuses to build on an end-of-life release;
the skill then gained the **EoL** command. After review (log file moved out of
`/tmp`, clearer step 2, and `verify.sh` also requiring the downloaded source),
all 9 were run again with the final text and scripts and passed. A manual review of the command logs showed exactly the skill's five
commands on every release, with the **EoL** command on 14.0 to 14.3 only.

## Not verified

- The test network allows only FreeBSD's own servers. Each port's source was
  therefore fetched from FreeBSD's copy (`distcache.FreeBSD.org`) after the
  program's own download sites failed; with a normal internet connection the
  first site usually works.
- Large ports, and ports whose option menus matter, were not tried.

## Differences from the Handbook

- The Handbook's example, `sysutils/lsof`, does not build on a standard
  install: it stops with `lsof-4.99.5,8 requires kernel sources (or set
  SRC_BASE).` because `/usr/src` is not installed. The skill's example is
  `misc/figlet`.
- On 14.0 to 14.3 (end of life) the Ports Collection refuses to build unless
  `ALLOW_UNSUPPORTED_SYSTEM` is set; the Handbook does not mention this.
- The Handbook runs `make install` and then `make clean` interactively, in the
  port's directory. The skill uses `make -C` with `BATCH=yes`, so no menu can
  wait for input.

## Source

FreeBSD Handbook, "Using the Ports Collection",
https://docs.freebsd.org/en/books/handbook/ports/#ports-using
