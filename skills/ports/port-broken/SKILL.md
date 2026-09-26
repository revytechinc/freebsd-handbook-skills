---
name: ports-port-broken
description: When a port will not build, find out whether the Ports Collection marks it as broken and why, who maintains it, and whether a ready-made package can be installed instead.
handbook: ports/#ports-broken
handbook_commit: bdf18a0458
---

# Find out why a port will not build

## What this does

When a port does not build or install, the Handbook suggests: check whether
the problem is known, ask the port's maintainer, or install the package
instead. This skill gathers what is needed for all three: whether the ports
framework itself marks the port as broken (and the reason it gives), who
maintains it, and whether FreeBSD's package repository has a ready-made
package. It builds and installs nothing.

## Before you start

- You need: a root shell, network access to FreeBSD's servers, and the Ports
  Collection in `/usr/ports` (skill `ports/ports-tree-git`).
- This changes: nothing, apart from pkg downloading the current list of
  packages (step 5).
- Time: seconds.
- Risk: none.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `PORT` | the port's directory under `/usr/ports`: category, `/`, name | `misc/bogosort` |

Everywhere below, replace `PORT` with this value, exactly as given. It must be
one word, a `/`, and another word; each word must start with a letter or a
digit, and may contain only letters, digits, and the characters `.` `_` `+`
`-`. If it does not, stop and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Your release group |
|---|---|
| `14.0-RELEASE` to `14.3-RELEASE`, possibly followed by `-p` and a number (end of life as of 2026-09-24) | EoL |
| `14.4-RELEASE`, `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE`, possibly followed by `-p` and a number, or `16.0-CURRENT` | current |
| anything else | stop, and report the line: this skill was not tested there |

## Step 2: Check the port exists

Run:

    ls /usr/ports/PORT/Makefile; echo "exit=$?"

| If you see | Do this |
|---|---|
| `/usr/ports/PORT/Makefile`, then `exit=0` | go to step 3 |
| `No such file or directory` and `exit=1` | there is no such port, or no ports tree. Stop, and report it |
| anything else | stop, and report the full output |

## Step 3: Ask the ports framework whether it will build the port

When a port cannot be built here, the ports framework says so in one value,
`IGNORE`, with the reason. It collects every kind of refusal there: a port
marked broken (the reason then starts `is marked as broken`, also when it is
broken only on some machines or releases), forbidden (`is forbidden`), or
unable to build on this system for another reason. `DEPRECATED` means the
port will be removed. Run (one command):

    make -C /usr/ports/PORT -V 'MAINTAINER=[${MAINTAINER}]' -V 'IGNORE=[${IGNORE}]' -V 'DEPRECATED=[${DEPRECATED}]' -V 'PKGBASE=[${PKGBASE}]'; echo "exit=$?"

Expected: four lines, each a name, `=`, and a value in brackets, then
`exit=0`, such as:

    MAINTAINER=[ports@FreeBSD.org]
    IGNORE=[]
    DEPRECATED=[]
    PKGBASE=[bogosort]
    exit=0

Empty brackets mean not set.

| If you see | Do this |
|---|---|
| four such lines, then `exit=0` | write down each value, and go to step 4. The value inside `PKGBASE=[...]` is called `NAME` below |
| anything else (for example lines starting `make:`, or an exit other than `exit=0`) | the ports framework could not read the port. Stop, and report the full output: that itself is why it will not build |

## Step 4: Note who to ask

The value of `MAINTAINER` from step 3 is the address of the port's maintainer
(for a port that is a variant of another, it is the other port's
maintainer). If it is `ports@FreeBSD.org`, no single person looks after the
port: help comes from the ports mailing list. Known problems are listed in
FreeBSD's bug database, https://bugs.freebsd.org/ (search for the port's
name). This skill does not send anything: asking and reporting are for the
person to do.

## Step 5: Check whether a ready-made package exists

Run the command for your release group (with `NAME` from step 3):

- **current**: `pkg update -q; echo "exit=$?"; pkg rquery '%n-%v' NAME; echo "exit=$?"`
- **EoL**: `env IGNORE_OSVERSION=yes pkg update -q; echo "exit=$?"; pkg rquery '%n-%v' NAME; echo "exit=$?"`

| If you see | Do this |
|---|---|
| `exit=0`, then a name and version, such as `bogosort-0.4.2_3`, then `exit=0` | a package exists: installing it (skill `ports/pkg-install`) avoids building the port. Write it down |
| `exit=0`, then only `exit=1` | FreeBSD has no ready-made package for this port. Write that down |
| anything else | pkg could not check. Write down "could not check" |

## Step 6: Report

Report the maintainer (step 4), `DEPRECATED` if it was not empty, and what
step 5 found. Then, as the last line of the report, write `RESULT: ` followed
by the `IGNORE=[...]` line from step 3, copied exactly as it was shown,
brackets included. For `misc/bogosort` that line is:

    RESULT: IGNORE=[]

(empty brackets: nothing stops the port from building). The `RESULT` line
must be alone on its line, with nothing before it (no label such as
"Status:"), and the word `RESULT` must not appear anywhere else in the
report, not even as a heading.

## Undo

Nothing to undo.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-26, snapshot 20260921 (a6deeaa2fb3b) |  |
| 15.1-RELEASE | verified | 2026-09-26 | Also tried by hand with `misc/bogosort`. |
| 15.0-RELEASE | verified | 2026-09-26 |  |
| 14.5-RELEASE | verified | 2026-09-26 |  |
| 14.4-RELEASE | verified | 2026-09-26 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-26 | Needs the **EoL** command in step 5. `IGNORE` still shows the port's own reason; the "support has ended" refusal only comes when building (seen on 14.1). |
| 14.2-RELEASE (EoL) | verified | 2026-09-26 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-26 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-26 | As 14.3. |

## Weak-model check

2026-09-26 (UTC): claude-haiku-4-5, given only this skill, the input
`PORT=sysutils/lsof` (not the skill's example), and a tool that runs one
command on the test machine, followed it on a freshly reset system of every
release above, with the ports tree cloned beforehand. The test machines have
no kernel sources, so the ports framework marks that port as unable to build
here. This skill changes nothing that it reports on, so a run counts only
when the model said DONE, its final message contained exactly the line worked
out beforehand without the model (`answer.sh`, asking the ports framework
for the same `IGNORE` value), and that answer was the same after the run:
all 9 did, with the final text. The command logs show exactly the skill's four commands
on every release, with the **EoL** command in step 5 on 14.0 to 14.3 only.

## Not verified

- Searching the bug database: the test network does not reach it.
- A port really marked broken or forbidden was not among the test ports.
  Tried by hand on 15.1 instead: `make -V IGNORE BROKEN="test reason"`
  printed `is marked as broken: test reason`, and with `FORBIDDEN` it
  printed `is forbidden: ...`, which is why step 3 reads only `IGNORE`.
- The Handbook's "Fix it!" (the Porter's Handbook) is not part of this
  skill.

## Differences from the Handbook

- The Handbook finds the maintainer with `make maintainer` in the port's
  directory; the skill asks for `MAINTAINER` together with `IGNORE` and the
  package name in one `make -C ... -V` command, whose exit status shows
  whether the ports framework could read the port at all.
- The Handbook asks the reader to email the maintainer and file bug reports.
  The skill only gathers the facts for that; it sends nothing.

## Source

FreeBSD Handbook, "Dealing with Broken Ports",
https://docs.freebsd.org/en/books/handbook/ports/#ports-broken
