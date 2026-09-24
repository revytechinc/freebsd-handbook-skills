---
name: ports-pkg-add-offline
description: Install a package from .pkg files downloaded earlier with pkg fetch, on a machine that has no network access.
handbook: ports/#pkg-installing-fetching
handbook_commit: bdf18a0458
---

# Install a downloaded package without a network

## What this does

Installs a package, and the packages it depends on, from `.pkg` files that
were downloaded earlier with the skill `ports/pkg-fetch`. It does not use the
network at all, so it works on a machine that is offline.

## Before you start

- You need: a root shell, pkg itself installed (skill `ports/pkg-bootstrap`),
  and the directory made by `ports/pkg-fetch`, downloaded on a machine with
  the same release family and processor type and then copied to this machine.
- This changes: installs the package and its dependencies under `/usr/local`.
- Time: under a minute.
- Risk: low. See Undo to remove the package again.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `PACKAGE` | the exact package name, without a version | `nginx-lite` |
| `DIR` | the directory on this machine that holds the copied files (the one with `All/Hashed/` inside it) | `/root/packages` |

Everywhere below, replace `PACKAGE` and `DIR` with these values, exactly as
given. Check them first:

- `PACKAGE` must start with a lower-case letter or a digit, and may contain only
lower-case letters, digits, and the characters
  `.` `_` `+` `-`, for example `nginx-lite` or `py311-certbot`. If it contains
  anything else (a space, `;`, `$`, `*`, a quote, `/`), stop and report: do not
  run any command with it.
- `DIR` must start with `/`, must not be `/` alone, must not contain `..`,
  and may contain only letters, digits, and the characters `/` `.` `_` `-`. If it does not, stop and
  report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`,
sometimes with `-p<number>` added.

| The line starts with | Your release group | Use in step 3 |
|---|---|---|
| `14.0-`, `14.1-`, `14.2-` or `14.3-` | EoL | the command marked **EoL** |
| anything else (`14.4-`, `14.5-`, `15.`, `16.`) | current | the command marked **current** |

Why: releases 14.0 to 14.3 have reached end of life. The downloaded packages
were built for a newer 14.x, and `pkg add` refuses them unless it is told to
accept that (`IGNORE_OSVERSION=yes`). Packages for 14.x work on every 14.x.

## Step 2: Find the downloaded files

Run:

    ls DIR/All/Hashed/; echo "exit=$?"

Expected: one file per package, and `exit=0`. For `PACKAGE` = `nginx-lite`:

    nginx-lite-1.30.4,3~52205125ee.pkg
    pcre2-10.47_1~c63c0c0fc7.pkg
    exit=0

Count the lines that start with `PACKAGE-` followed by a digit (for
`nginx-lite`: lines starting `nginx-lite-1`, `nginx-lite-2`, and so on).

| You count | Do this |
|---|---|
| exactly 1 | go to step 3 |
| 0, or `No such file or directory` | the files are not there. Stop, and report the output |
| more than 1 | several versions were downloaded. Stop, and report the output |

## Step 3: Install from the files

Run the command for your release group, exactly as written. The
`PACKAGE-[0-9]*.pkg` part is a pattern that matches the one file you counted
in step 2, so you never type its full name:

- **current**: `pkg add DIR/All/Hashed/PACKAGE-[0-9]*.pkg; echo "exit=$?"`
- **EoL**: `env IGNORE_OSVERSION=yes pkg add DIR/All/Hashed/PACKAGE-[0-9]*.pkg; echo "exit=$?"`

`pkg add` finds the dependencies in the same directory and installs them
first. Expected, for `PACKAGE` = `nginx-lite` (a package may also print a
message of its own; the last line is what matters):

    Installing nginx-lite-1.30.4,3...
    `-- Installing pcre2-10.47_1...
    `-- Extracting pcre2-10.47_1: .......... done
    ...
    Extracting nginx-lite-1.30.4,3: .......... done
    ...
    exit=0

| If you see | Do this |
|---|---|
| `exit=0` on the last line | go to step 4 |
| `the most recent version of PACKAGE-... is already installed` and `exit=0` | it was already installed before you started. Go to step 4, and do NOT run Undo afterwards |
| `Newer FreeBSD version for package` and `exit=1` | you used the **current** command on an EoL release. Run the **EoL** command instead |
| `exit=` followed by anything else | stop, and report the full output |

Do NOT use `pkg install` here. `pkg install`
first tries to contact the package repository and, offline, stops with
`Unable to update repository` and `Error updating repositories!`.

## Step 4: Verify

Run:

    pkg query '%n %v' PACKAGE; echo "exit=$?"

Expected: two lines. The first is the package name, a space, and its version,
for example `nginx-lite 1.30.4,3`. The second is `exit=0`. If you see only
`exit=1`, the package is not installed: stop and report.

## Undo

Only if step 3 installed the package. This works offline. Remove the package:

    pkg delete -y PACKAGE; echo "exit=$?"

Expected: `Installed packages to be REMOVED:` with the package, then `exit=0`.

Then ask pkg which packages it would remove as no longer needed, WITHOUT
removing them (`-n` is a dry run):

    pkg autoremove -n; echo "exit=$?"

| If you see | Do this |
|---|---|
| `Nothing to do.` and `exit=0` | nothing else to remove. Undo is finished |
| `Installed packages to be REMOVED:`, a list of packages, and `exit=1` | `exit=1` here only means "there is something to remove". Compare the list with the packages named in the `Installing` lines that step 3 printed (for `nginx-lite`: `pcre2`). If EVERY package in the list is also there, run `pkg autoremove -y; echo "exit=$?"` and expect `exit=0`. If ANY package in the list is not there, do NOT run it: something else on this machine left it behind. Stop, and report the list |
| anything else | stop, and report the full output |

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | The file names contain `$`; the pattern in step 3 handles it. |
| 15.1-RELEASE | verified | 2026-09-24 | |
| 15.0-RELEASE | verified | 2026-09-24 | |
| 14.5-RELEASE | verified | 2026-09-24 | |
| 14.4-RELEASE | verified | 2026-09-24 | |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | Needs the **EoL** command. Without it: `Newer FreeBSD version for package nginx-lite`, exit status 1, nothing installed. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.3 (package built for 1404000, userland 1400097). |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill, the inputs
`PACKAGE=nginx-lite` and `DIR=/root/packages`, and a tool that runs one command
on the test machine, followed it on a freshly reset system of every release
above. Before each run the files had been downloaded and the machine's network
cut off (its default routes removed, checked by a download that worked before
and failed after), and the independent check confirmed afterwards that it was
still offline. A run
counts only when the model said DONE AND the independent check (`verify.sh`:
nginx-lite and pcre2 installed, `nginx -v` works) passed: all 9 did. A manual
review of the command logs showed only the skill's four commands, with the
**EoL** command on 14.0 to 14.3 and the **current** one everywhere else.

Undo, offline, was run by hand (not by the weak model) on every release:
`pkg delete` and `pkg autoremove` removed nginx-lite, then pcre2, each with
`exit=0`. The dry run `pkg autoremove -n` is described under the same check
in `ports/pkg-install`.

## Not verified

- Files downloaded on a different machine. Every test downloaded the files on
  the machine itself, then cut its network off (removed its default routes)
  before this skill ran.

## Differences from the Handbook

- The Handbook installs a downloaded file with
  `pkg install nginx-lite-1.22.1,3.pkg`, run inside the download directory.
  That does not work offline on any release tested: `pkg install` first tries
  to update the repository catalogue and stops with `Error updating
  repositories!` (exit status 3). `pkg install -U`, which skips that update,
  still tries to download the dependencies (and on 15.1, a newer pkg) and also
  fails. `pkg add` works.
- The file is not in the download directory but in `All/Hashed/` under it,
  with a `~<code>` part in its name.

## Source

FreeBSD Handbook, "Installing and Fetching Packages",
https://docs.freebsd.org/en/books/handbook/ports/#pkg-installing-fetching
