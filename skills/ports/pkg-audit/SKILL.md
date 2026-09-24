---
name: ports-pkg-audit
description: Check the installed packages against FreeBSD's list of known security vulnerabilities, and report which packages are affected.
handbook: ports/#pkgng-auditing
handbook_commit: bdf18a0458
---

# Check installed packages for known vulnerabilities

## What this does

The FreeBSD project keeps a list of known security problems in packages (the
VuXML database). This skill downloads the current list and checks every
installed package against it, then reports which packages, if any, have known
problems. Nothing is upgraded or removed; fixing a problem is usually done
with `ports/pkg-upgrade`.

## Before you start

- You need: a root shell, network access to `vuxml.freebsd.org`, and pkg
  itself installed (skill `ports/pkg-bootstrap`).
- This changes: downloads the list to `/var/db/pkg/vuln.xml`. Nothing else.
- Time: under a minute.
- Risk: none.

## Inputs

None.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.
The commands below are the same on every release.

## Step 2: Download the list and check

Run. `-F` downloads the current list first:

    pkg audit -F; echo "exit=$?"

| If you see | Do this |
|---|---|
| `0 problem(s) in 0 package(s) found.` and `exit=0` | no installed package has a known problem. Go to step 4 |
| `<number> problem(s) in <number> package(s) found.` and `exit=1` | `exit=1` here means "problems were found". Go to step 3 |
| `cannot fetch vulnxml file`, `Network is unreachable` or `timed out` | the list could not be downloaded. Stop, and report the full output |
| anything else | stop, and report the full output |

With problems, the output lists each affected package and its problems, for
example:

    Fetching vuln.xml.xz: .......... done
    curl-7.50.0 is vulnerable:
      Vulnerabilities in Curl
      CVE: CVE-2016-5421
      ...
    33 problem(s) in 1 package(s) found.
    exit=1

## Step 3: List only the affected packages

Run. `-q` prints just the name and version of each affected package:

    pkg audit -q; echo "exit=$?"

Expected: one line per affected package, such as `curl-7.50.0`, then
`exit=1`. Write the lines down.

If any line starts with `pkg:` (for example
`pkg: vulnxml file /var/db/pkg/vuln.xml does not exist`), the check did not
run: stop, report the output, and end with FAILED.

## Step 4: Report

Write one line in your final answer:

- if step 2 found nothing: `RESULT: no known vulnerabilities`
- otherwise: `RESULT: VULNERABLE ` followed by the lines from step 3,
  separated by single spaces, in the order printed, for example
  `RESULT: VULNERABLE curl-7.50.0`

## Undo

None needed. The downloaded list can stay; it is refreshed by the next
`pkg audit -F`.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | |
| 15.1-RELEASE | verified | 2026-09-24 |  |
| 15.0-RELEASE | verified | 2026-09-24 |  |
| 14.5-RELEASE | verified | 2026-09-24 |  |
| 14.4-RELEASE | verified | 2026-09-24 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | No special setting needed: the list is not the package repository. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill and a tool that runs
one command on the test machine, followed it on a freshly reset system of
every release above (ZFS-root test machines), with curl installed and
libssh2's recorded version set to 1.8.0 (see Not verified). A run counts only
when the model said DONE AND the independent check (`verify.sh`: the list was
downloaded during the run) passed AND its final message contained the exact
line computed separately on the machine (`answer.sh`: the RESULT line naming
libssh2 at its recorded version, which the skill's own example does not
contain): all 9 did. A manual review of the command logs showed exactly the
skill's three commands on every release.

The committed test scripts were run once more on 15.1-RELEASE: passed.

## Not verified

- A fresh system had no affected packages. So that the tests had something to
  find, the recorded version of the installed `libssh2` was changed to an old
  one (1.8.0) in pkg's database; the package itself was not changed. Real old
  installed versions were not used.
- The "cannot fetch" row was seen by hand with the network cut
  (`pkg: ... Network is unreachable`, `pkg: cannot fetch vulnxml file`,
  exit status 1), not by the weak model.
- The base system's own security fixes are checked by a different command
  (`pkg audit` for packages only; on 15.x and later base updates come through
  `ports/pkg-upgrade`). Not covered here.

## Differences from the Handbook

- `pkg audit` exits with status 1 when it finds problems, and 0 when it finds
  none; it also exits with status 1 when it cannot download or read the list,
  so the text of the output, not only the status, tells the two apart. The
  Handbook does not say this.

## Source

FreeBSD Handbook, "Auditing Installed Packages",
https://docs.freebsd.org/en/books/handbook/ports/#pkgng-auditing
