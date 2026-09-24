---
name: ports-pkg-info
description: Find out whether a package is installed, and if so its version and details, without changing anything.
handbook: ports/#pkgng-pkg-info
handbook_commit: bdf18a0458
---

# Show information about an installed package

## What this does

Checks whether one package is installed on this machine, and if it is, shows
its version, where it came from, and other details. Nothing is changed and
nothing is downloaded.

## Before you start

- You need: a root shell, and pkg itself installed (skill `ports/pkg-bootstrap`).
- This changes: nothing.
- Time: seconds.
- Risk: none.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `PACKAGE` | the exact package name, without a version | `curl` |

Everywhere below, replace `PACKAGE` with this value, exactly as given, with no
version number. `PACKAGE` must start with a lower-case letter or a digit, and
may contain only lower-case letters, digits, and the characters `.` `_` `+`
`-`. If it contains anything else (a space, `;`, `$`, `*`, a quote, `/`), stop
and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.
The commands below are the same on every release. (They only read the list of
installed packages on this machine, so the end-of-life setting some other pkg
skills need is not needed here.)

## Step 2: Is PACKAGE installed?

Run:

    pkg info -E PACKAGE; echo "exit=$?"

| If you see | Meaning | Do this |
|---|---|---|
| one line `PACKAGE-<version>` (for example `curl-8.22.0`), then `exit=0` | installed | go to step 3 |
| only `exit=1` | not installed | go to step 4 |
| anything else | unexpected | stop, and report the full output |

## Step 3: Show the details

Run:

    pkg info PACKAGE; echo "exit=$?"

Expected (for `PACKAGE` = `curl`; values differ by release and over time),
starting with:

    curl-8.22.0
    Name           : curl
    Version        : 8.22.0
    Installed on   : Thu Sep 24 15:44:40 2026 UTC
    Origin         : ftp/curl
    Architecture   : FreeBSD:15:amd64
    ...
    exit=0

The `Version` line is the installed version. `Origin` is where the package
comes from in the ports collection. If the last line is not `exit=0`, stop and
report the output.

## Step 4: Report

Write one of these lines in your final answer:

- if step 2 found it: `RESULT: PACKAGE VERSION installed`, copying VERSION
  exactly from the `Version` line of step 3, including any `_` or `,` part;
  for example `RESULT: curl 8.22.0 installed`
- if step 2 printed only `exit=1`: `RESULT: PACKAGE not installed`

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | |
| 15.1-RELEASE | verified | 2026-09-24 | |
| 15.0-RELEASE | verified | 2026-09-24 | |
| 14.5-RELEASE | verified | 2026-09-24 | |
| 14.4-RELEASE | verified | 2026-09-24 | |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | No special setting needed: `pkg info` only reads the local list. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill, the input
`PACKAGE=nginx-lite` (deliberately not the package in the skill's examples),
and a tool that runs one command on the test machine, followed it on a freshly
reset system of every release above, with nginx-lite installed beforehand.
This skill changes nothing, so the independent check is the answer itself: a
run counts only when the model said DONE AND its final message contained the
exact line `RESULT: nginx-lite <version> installed`, with the version read
separately on the machine (`answer.sh`): all 9 did. A manual review of the
command logs showed only the skill's three commands on every release.

## Not verified

- Step 2's `exit=1` branch was run by hand (for a package that is not
  installed and for a name that does not exist: `pkg info -E` printed nothing
  and exited with status 1 on 14.0, 14.5, 15.1 and 16.0-CURRENT), but not by
  the weak model.

## Differences from the Handbook

- The Handbook shows `pkg info` with no name, which lists every installed
  package. On 15.x and 16.0-CURRENT the base system itself is installed as
  packages, so that list is long: 510 lines on a fresh 15.1 with curl, 499 of
  them `FreeBSD-...` base packages.
- A version typed with the name does not match: `pkg info -e curl-8` exits
  with status 1 even when curl 8.22.0 is installed. Use the name alone.

## Source

FreeBSD Handbook, "Obtaining Information About Installed Packages",
https://docs.freebsd.org/en/books/handbook/ports/#pkgng-pkg-info
