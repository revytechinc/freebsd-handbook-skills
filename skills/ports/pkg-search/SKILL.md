---
name: ports-pkg-search
description: Find out whether a binary package is available for this FreeBSD machine, and which version, without installing anything.
handbook: ports/#pkg-search
handbook_commit: bdf18a0458
---

# Search for a package

## What this does

Asks the package repository which packages match a word, then checks one exact
package name and reports its version. Nothing is installed or changed, except
that pkg downloads the repository's list of packages (the "catalogue") to
`/var/db/pkg` the first time.

## Before you start

- You need: a root shell, network access to `pkg.FreeBSD.org`, and pkg itself
  installed (skill `ports/pkg-bootstrap`).
- This changes: only the downloaded catalogue under `/var/db/pkg`.
- Time: under a minute.
- Risk: none.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `WORD` | a word to look for in package names | `nginx` |
| `PACKAGE` | the exact package name to check, without a version | `nginx-lite` |

Everywhere below, replace `WORD` and `PACKAGE` with these values, exactly as
given, with no version number. Each must start with a lower-case letter or a
digit, and may contain only lower-case letters,
digits, and the characters `.` `_` `+` `-`. If either contains anything else
(a space, `;`, `$`, `*`, a quote, `/`), stop and report: do not run any command
with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`,
sometimes with `-p<number>` added (for example `14.4-RELEASE-p3`).

| The line starts with | Your release group | Use in steps 2 and 3 |
|---|---|---|
| `14.0-`, `14.1-`, `14.2-` or `14.3-` | EoL | the command marked **EoL** |
| anything else (`14.4-`, `14.5-`, `15.`, `16.`) | current | the command marked **current** |

Why: releases 14.0 to 14.3 have reached end of life. The repository now holds
packages built for a newer 14.x, and pkg refuses to search it unless it is told
to accept that (`IGNORE_OSVERSION=yes`). Packages for 14.x work on every 14.x.

## Step 2: List the packages that match WORD

Run the command for your release group:

- **current**: `pkg search WORD; echo "exit=$?"`
- **EoL**: `env IGNORE_OSVERSION=yes pkg search WORD; echo "exit=$?"`

Expected: one line per matching package, the name and version first, then a
short description, and last a line `exit=0`. For `WORD` = `nginx`:

    freenginx-1.30.1_2             Robust and small WWW server
    ...
    nginx-1.30.4,3                 Robust and small WWW server
    nginx-full-1.30.4,3            Robust and small WWW server (full package)
    nginx-lite-1.30.4,3            Robust and small WWW server (lite package)
    ...
    exit=0

The versions change over time. Each line reads `<name>-<version>`: in
`nginx-lite-1.30.4,3` the name is `nginx-lite` and the version is `1.30.4,3`.

| If you see | Do this |
|---|---|
| package lines, then `exit=0` | go to step 3 |
| only `exit=1` | nothing matches WORD. Go to step 3 anyway |
| `wrong OS version` | you used the **current** command on an EoL release. Run the **EoL** command instead |
| `No address record`, `Network is unreachable`, `timed out` or `Could not connect` | the machine cannot reach the repository. Stop and report the output |
| `exit=` with any other number | stop and report the output |

## Step 3: Check the exact package name

Run the command for your release group:

- **current**: `pkg search -S name -e -Q version PACKAGE; echo "exit=$?"`
- **EoL**: `env IGNORE_OSVERSION=yes pkg search -S name -e -Q version PACKAGE; echo "exit=$?"`

`-S name -e` means "the package name is exactly PACKAGE". `-Q version` adds
the version line. Expected, for `PACKAGE` = `nginx-lite`:

    nginx-lite
    Version        : 1.30.4,3
    Comment        : Robust and small WWW server (lite package)
    exit=0

| If you see | Do this |
|---|---|
| the name, a `Version` line and `exit=0` | the package exists. Go to step 4 |
| only `exit=1` | there is no package with exactly that name. Go to step 4 |
| anything else | stop and report the output |

## Step 4: Report

Write this line in your final answer, copying the version exactly as the
`Version` line shows it, including any `_` or `,` part:

- if step 3 found it: `RESULT: PACKAGE VERSION`, for example
  `RESULT: nginx-lite 1.30.4,3`
- if step 3 printed only `exit=1`: `RESULT: PACKAGE not available`

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | Repository branch `latest`: newer versions (`nginx-lite 1.30.5,3`) and more matches than the other releases. |
| 15.1-RELEASE | verified | 2026-09-24 | |
| 15.0-RELEASE | verified | 2026-09-24 | |
| 14.5-RELEASE | verified | 2026-09-24 | |
| 14.4-RELEASE | verified | 2026-09-24 | |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | Needs the **EoL** commands. Without them: `wrong OS version`, exit status 1. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | Needs the **EoL** commands. Without them: `wrong OS version`, exit status 3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.2. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.2. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill, the inputs
`WORD=curl` and `PACKAGE=curl` (deliberately not the examples in the skill, so
that the answer could not be copied from them), and a tool that runs one command on the
test machine, followed it on a freshly reset system of every release above.
A run counts only when the model said DONE, the independent check (`verify.sh`:
the catalogue was downloaded) passed, AND its final answer contained the
`RESULT:` line computed separately on the machine (`answer.sh`): all 9 did.
A manual review of the command logs showed exactly three commands per run,
all the skill's own, with the **EoL** commands chosen on 14.0 to 14.3 and the
**current** ones everywhere else.

## Not verified

- The network-failure row in step 2 was not provoked.
- Step 4's `not available` branch was run by hand (an exact search for a name
  that does not exist printed only `exit=1` on 14.0, 14.5, 15.1 and
  16.0-CURRENT), but not by the weak model.

## Differences from the Handbook

- The Handbook shows only `pkg search nginx`. On releases 14.0 to 14.3 that
  command now fails with `pkg: repository FreeBSD contains packages for wrong
  OS version: FreeBSD:14:amd64` (exit status 3 on 14.0 to 14.2, 1 on 14.3),
  which is why
  step 1 picks a different command there.
- `pkg search -e nginx-lite` (exact match without `-S name`) finds nothing: it
  compares against name and version together. Step 3 uses `-S name -e`.

## Source

FreeBSD Handbook, "Searching Packages",
https://docs.freebsd.org/en/books/handbook/ports/#pkg-search
