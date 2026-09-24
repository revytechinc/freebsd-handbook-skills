---
name: ports-pkg-bootstrap
description: Make sure the pkg package manager is installed on FreeBSD, installing it if it is missing, without any interactive prompt.
handbook: ports/#pkgng-initial-setup
handbook_commit: f55737d391
---

# Install the pkg package manager (bootstrap)

## What this does

FreeBSD ships a small program at `/usr/sbin/pkg` whose only job is to download
and install the real package manager, `pkg`. This skill checks whether the real
`pkg` is already installed and, if it is not, installs it. When you finish,
`pkg` works and reports its version.

## Before you start

- You need: a root shell, and network access to `pkg.FreeBSD.org`.
- This changes: installs the `pkg` package under `/usr/local` if it is missing.
- Time: under a minute.
- Risk: none. If `pkg` is already installed, nothing is changed.

## Inputs

None.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.4-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`
(sometimes with `-p<number>` added, for example `14.4-RELEASE-p3`). Write it
down. This skill works the same way on every release; the value is only used
in the Verify step.

## Step 2: Check whether pkg is already installed

Run:

    pkg -N; echo "exit=$?"

Find the line that starts with `exit=`. (Another line, such as
`pkg: 500 packages installed`, may be printed before or after it.)

| The `exit=` line | Meaning | Do this |
|---|---|---|
| `exit=1` | pkg is NOT installed | go to step 3 |
| `exit=0` | pkg is already installed | skip step 3, go to step 4 |
| anything else | unexpected | stop, and report the full output |

## Step 3: Install pkg

Run exactly this. The `ASSUME_ALWAYS_YES=yes` part answers "yes" to the
installation question automatically:

    env ASSUME_ALWAYS_YES=yes pkg bootstrap; echo "exit=$?"

Expected output (the numbers and the `14` may differ):

    pkg: pkg is not installed
    Installing pkg-2.7.5...
    Extracting pkg-2.7.5: .......... done
    Bootstrapping pkg from pkg+https://pkg.FreeBSD.org/FreeBSD:14:amd64/quarterly, please wait...
    Verifying signature with trusted certificate pkg.freebsd.org.2013102301... done
    exit=0

| If you see | Do this |
|---|---|
| `exit=0` on the last line | go to step 4 |
| `pkg already bootstrapped at /usr/local/sbin/pkg` and `exit=0` | pkg was already there; go to step 4 |
| `No address record` or `Network is unreachable` or `timed out` | the machine cannot reach `pkg.FreeBSD.org`; stop, and report the full output |
| `exit=` followed by anything other than `0` | stop, and report the full output |

Do NOT run plain `pkg` here to answer a question interactively. Without a
terminal it does not ask. It prints `Please set ASSUME_ALWAYS_YES=yes
environment variable to be able to bootstrap in non-interactive (stdin not
being a tty)` and exits with status 1.

## Step 4: Verify

Run:

    pkg -N >/dev/null 2>&1; echo "installed-exit=$?"; pkg -v

Expected: two lines. The first is exactly `installed-exit=0`. The second is a
version number of the form `2.<number>.<number>`, for example `2.7.5`.

Versions seen on each release, on the date in the table below:

| Release | `pkg -v` |
|---|---|
| 14.0 to 14.5, 15.0 | `2.7.5` |
| 15.1 | `2.6.2` (pkg came preinstalled in the image tested; it is not upgraded by this skill) |
| 16.0-CURRENT | `2.8.4` |

A different `2.x.y` number is fine: pkg is updated over time. If the first line
is not `installed-exit=0`, or the second line is not a version number, the task
did not succeed. Stop and report the output.

## Undo

Only if step 3 installed pkg. Do NOT undo if pkg was already installed before
you started (step 2 said `exit=0`): other software may depend on it.

pkg refuses to remove itself without the force flag `-f`, so run:

    pkg delete -fy pkg; echo "exit=$?"; pkg -N; echo "installed-exit=$?"

Expected: `exit=0`, then `pkg: pkg is not installed`, then `installed-exit=1`.
Do not leave out `-f`: without it pkg prints
`pkg: Cannot delete pkg itself without force flag`, exits with status 3, and
removes nothing.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified (no-op) | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | pkg preinstalled in the VM image: the skill correctly skipped step 3. Repository branch `latest`. |
| 15.1-RELEASE | verified (no-op) | 2026-09-24 | pkg preinstalled in the VM image: the skill correctly skipped step 3. |
| 15.0-RELEASE | verified | 2026-09-24 | Base system is installed as packages (487 of them), but pkg itself was missing: step 3 installed it. Repository name `FreeBSD-ports`. |
| 14.5-RELEASE | verified | 2026-09-24 | |
| 14.4-RELEASE | verified | 2026-09-24 | |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | Downloads over plain `http://` (`pkg+http://pkg.FreeBSD.org/...`); later releases use `https://`. |

Undo was run by hand on 14.0 to 15.0 (2026-09-24 UTC), with and without `-f`:
the output matched the Undo section exactly on every one.

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill and a tool that runs
one command on the test machine, followed it on a freshly reset system of
every release in the table above. A run counts only when the model finished and
said DONE AND the independent check (`verify.sh`) passed afterwards: all 9 did.
A manual review of each run's command log showed the model ran only the
skill's own commands, in order, and took the step-2 decision correctly each
time. On 14.0 to 15.0 it installed pkg. On 15.1 and
16.0-CURRENT pkg was already installed before the run, so the check shows the
model correctly detected that and skipped step 3, not that it installed pkg.

## Not verified

- Step 3's network-failure branch (`No address record`, `Network is
  unreachable`, `timed out`): not provoked. The messages listed are what
  `fetch(3)` reports for those failures, but they were not observed here.
- Undo on 15.1 and 16.0-CURRENT: not run, on purpose. pkg came preinstalled
  there, and this skill says not to remove it in that case.
- The interactive question shown in the Handbook (`Do you want to fetch and
  install it now? [y/N]`) only appears when pkg is run from a terminal. This
  skill avoids it on purpose with `ASSUME_ALWAYS_YES=yes`.

## Source

FreeBSD Handbook, "Getting Started with pkg",
https://docs.freebsd.org/en/books/handbook/ports/#pkgng-initial-setup
