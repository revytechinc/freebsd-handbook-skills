---
name: ports-pkg-install
description: Install a binary package, and the packages it depends on, from the FreeBSD package repository, without any interactive prompt.
handbook: ports/#pkg-installing-fetching
handbook_commit: bdf18a0458
---

# Install a package

## What this does

Installs one package from the FreeBSD package repository, together with every
other package it needs (its "dependencies"). When you finish, the package is
listed as installed and its programs are under `/usr/local`.

## Before you start

- You need: a root shell, network access to `pkg.FreeBSD.org`, and pkg itself
  installed (skill `ports/pkg-bootstrap`).
- This changes: installs the package and its dependencies under `/usr/local`.
- Time: usually under two minutes.
- Risk: low. See Undo to remove the package again.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `PACKAGE` | the exact package name, without a version | `curl` |

Everywhere below, replace `PACKAGE` with this value, exactly as given, with no
version number. `PACKAGE` must start with a lower-case letter or a digit, and may contain only
lower-case letters, digits, and the characters
`.` `_` `+` `-`, for example `nginx-lite` or `py311-certbot`. If it contains
anything else (a space, `;`, `$`, `*`, a quote, `/`), stop and report: do not
run any command with it. If you do not know the exact name,
find it first with the skill `ports/pkg-search`.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`,
sometimes with `-p<number>` added. Write it down. The commands in this skill
are the same on every release; only some output lines differ, as noted.

## Step 2: Check whether PACKAGE is already installed

Run:

    pkg info -e PACKAGE; echo "exit=$?"

| The `exit=` line | Meaning | Do this |
|---|---|---|
| `exit=1` | not installed | go to step 3 |
| `exit=0` | already installed | skip step 3, go to step 4 |
| anything else | unexpected | stop, and report the full output |

## Step 3: Install PACKAGE

Run exactly this. The `-y` answers "yes" to the question
`Proceed with this action? [y/N]` automatically:

    pkg install -y PACKAGE; echo "exit=$?"

Expected (for `PACKAGE` = `curl`; the package list, the versions and the
numbers change over time). First, pkg updates its list of available packages
(the "catalogue"). Those first lines depend on the release:

| Release | First lines |
|---|---|
| 14.0, 14.1, 14.2 | `Updating FreeBSD repository catalogue...`, then `All repositories are up to date.` |
| 14.3, 14.4, 14.5 | `Updating FreeBSD repository catalogue...`, then the same for `FreeBSD-kmods`, then `All repositories are up to date.` |
| 15.0, 15.1, 16.0-CURRENT | `Updating FreeBSD-ports repository catalogue...`, then the same for `FreeBSD-ports-kmods` and `FreeBSD-base`, then `All repositories are up to date.` |

On 15.1 (with the pkg that came with the release) the next lines are
`New version of pkg detected; it needs to be installed first.` and
`[1/1] Upgrading pkg from 2.6.2_1 to 2.7.5...`. That is normal: pkg updates
itself first, and then continues with PACKAGE in the same command. Then, on
every release:

    The following 10 package(s) will be affected (of 0 checked):

    New packages to be INSTALLED:
            brotli: 1.2.0,1
            curl: 8.22.0
            ...

    Number of packages to be installed: 10
    ...
    [10/10] Installing curl-8.22.0...
    [10/10] Extracting curl-8.22.0: .......... done
    exit=0

| If you see | Do this |
|---|---|
| `exit=0` on the last line | go to step 4 |
| `pkg: No packages available to install matching 'PACKAGE' have been found in the repositories` and `exit=1` | there is no package with that exact name. Stop, and report it; find the right name with `ports/pkg-search` |
| `No address record`, `Network is unreachable`, `timed out` or `Could not connect` | the machine cannot reach the repository. Stop, and report the full output |
| `exit=` followed by anything other than `0` | stop, and report the full output |

Do NOT leave out `-y`. Without a terminal, pkg prints the question
`Proceed with this action? [y/N]:`, takes no answer as "no", exits with status
1, and installs nothing.

## Step 4: Verify

Run:

    pkg query '%n %v' PACKAGE; echo "exit=$?"

Expected: two lines. The first is the package name, a space, and its version,
for example `curl 8.22.0`. The second is `exit=0`. If you see only `exit=1`,
the package is not installed: stop and report.

## Undo

Only if step 3 installed the package. Do NOT undo if it was already installed
before you started (step 2 said `exit=0`).

Remove the package:

    pkg delete -y PACKAGE; echo "exit=$?"

Expected: `Installed packages to be REMOVED:` with the package, then `exit=0`.

Then ask pkg which packages it would remove as no longer needed, WITHOUT
removing them (`-n` is a dry run):

    pkg autoremove -n; echo "exit=$?"

| If you see | Do this |
|---|---|
| `Nothing to do.` and `exit=0` | nothing else to remove. Undo is finished |
| `Installed packages to be REMOVED:`, a list of packages, and `exit=1` | `exit=1` here only means "there is something to remove". Compare the list with the `New packages to be INSTALLED:` list that step 3 printed. If EVERY package in the list is also there, run `pkg autoremove -y; echo "exit=$?"` and expect `exit=0`. If ANY package in the list is not there, do NOT run it: something else on this machine left it behind. Stop, and report the list |
| anything else | stop, and report the full output |

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | Repositories `FreeBSD-ports`, `FreeBSD-ports-kmods`, `FreeBSD-base`. Some dependencies are newer than on 15.x. |
| 15.1-RELEASE | verified | 2026-09-24 | pkg upgrades itself (2.6.2_1 to 2.7.5) first, in the same command. |
| 15.0-RELEASE | verified | 2026-09-24 | Repositories `FreeBSD-ports`, `FreeBSD-ports-kmods`, `FreeBSD-base`. |
| 14.5-RELEASE | verified | 2026-09-24 | Repositories `FreeBSD`, `FreeBSD-kmods`. |
| 14.4-RELEASE | verified | 2026-09-24 | As 14.5. |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | As 14.5. The packages are built for 14.4; they install and run. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | Repository `FreeBSD` only. Packages built for 14.4; they install and run, and unlike `pkg search`, `pkg install` needs no `IGNORE_OSVERSION`. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.2. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.2. `curl --version` reports `amd64-portbld-freebsd14.4` and works. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill, the input
`PACKAGE=curl`, and a tool that runs one command on the test machine,
followed it on a freshly reset system of every release above. A run counts
only when the model said DONE AND the independent check (`verify.sh`: curl is
registered as installed and `/usr/local/bin/curl --version` works) passed:
all 9 did. A manual review of the command logs showed exactly the skill's four
commands on every release, none repeated or added.

## Not verified

- The network-failure row in step 3 was not provoked.
- Undo was run by hand, not by the weak model (2026-09-24 UTC). After
  installing `curl` on every release, `pkg delete` and `pkg autoremove`
  removed curl and exactly its 9 dependencies; on 15.0, 15.1 and 16.0-CURRENT,
  where the base system is itself installed as packages, no base-system
  package. The dry run `pkg autoremove -n` was run on 14.0, 15.1 and
  16.0-CURRENT: it listed the same 9 packages and exited with status 1, and
  with an unrelated leftover package on the machine it listed that one too.
- The `No packages available` row and the "without `-y`" behaviour were run by
  hand on 14.2 to 14.5 and 16.0-CURRENT (exactly the output shown), but not by
  the weak model.

## Differences from the Handbook

- The Handbook runs `pkg install curl` and answers the question by hand. Without
  a terminal that is not possible, so this skill uses `-y`.

## Source

FreeBSD Handbook, "Installing and Fetching Packages",
https://docs.freebsd.org/en/books/handbook/ports/#pkg-installing-fetching
