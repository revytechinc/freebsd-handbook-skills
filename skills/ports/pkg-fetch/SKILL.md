---
name: ports-pkg-fetch
description: Download a binary package and all the packages it depends on into a directory, without installing them, so they can be installed later or on a machine with no network.
handbook: ports/#pkg-installing-fetching
handbook_commit: bdf18a0458
---

# Download a package without installing it

## What this does

Downloads one package, and every package it depends on, as `.pkg` files into a
directory you choose. Nothing is installed. Copy the directory to another
machine (or keep it), and install from it with the skill
`ports/pkg-add-offline`, which needs no network.

## Before you start

- You need: a root shell, network access to `pkg.FreeBSD.org`, and pkg itself
  installed (skill `ports/pkg-bootstrap`).
- This changes: creates the new directory `DIR` and writes `.pkg` files into
  it.
  Nothing is installed.
- Time: under a minute for a small package.
- Risk: none.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `PACKAGE` | the exact package name, without a version | `nginx-lite` |
| `DIR` | the directory to download into; a full path starting with `/` | `/root/packages` |

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

pkg downloads the packages built for the machine it runs on: its release
family and processor type, which pkg calls the ABI, for example
`FreeBSD:14:amd64` (the repository URL in the output shows it). Install the
files only on a machine with the same ABI. Installing them on a different one
was not tested.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`,
sometimes with `-p<number>` added. Write it down: it is the release family the
downloaded files are for. The commands are the same on every release.

## Step 2: Check that DIR does not exist yet

`DIR` must be a new directory, so that everything in it comes from this skill
and Undo can remove it safely. Run:

    ls -d DIR; echo "exit=$?"

| If you see | Do this |
|---|---|
| `ls: DIR: No such file or directory` and `exit=1` | good: go to step 3 |
| `DIR` and `exit=0` | the directory already exists. Stop, and report it: ask for a new directory |
| anything else | stop, and report the full output |

## Step 3: Download

Run exactly this. `-d` also downloads the dependencies, `-o DIR` chooses the
directory, and `-y` answers "yes" to the question
`Proceed with fetching packages? [y/N]` automatically:

    pkg fetch -y -d -o DIR PACKAGE; echo "exit=$?"

Expected, for `PACKAGE` = `nginx-lite` (versions and sizes change over time):
first some lines about updating the catalogue, then

    New packages to be FETCHED:
            nginx-lite: 1.30.4,3 (383 KiB: 20.67% of the 2 MiB to download)
            pcre2: 10.47_1 (1 MiB: 79.33% of the 2 MiB to download)

    Number of packages to be fetched: 2
    ...
    Fetching nginx-lite-1.30.4,3: .......... done
    Fetching pcre2-10.47_1: .......... done
    exit=0

| If you see | Do this |
|---|---|
| `exit=0` on the last line | go to step 4 |
| `No address record`, `Network is unreachable`, `timed out` or `Could not connect` | the machine cannot reach the repository. Stop, and report the full output |
| `exit=` followed by anything other than `0` | stop, and report the full output |

## Step 4: Verify

Run:

    ls DIR/All/Hashed/; echo "exit=$?"

The files are NOT directly in `DIR`. pkg puts them in the subdirectory
`All/Hashed`, and adds `~` and a short code to each name. Expected, for
`PACKAGE` = `nginx-lite`:

    nginx-lite-1.30.4,3~52205125ee.pkg
    pcre2-10.47_1~c63c0c0fc7.pkg
    exit=0

The code after `~` differs between releases, and on 16.0-CURRENT it can contain
a `$` (for example `nginx-lite-1.30.5,3~2$9qs541dg.pkg`). Never type these file
names by hand; the install skill uses a pattern instead.

The task succeeded if there is a file whose name starts with `PACKAGE-` and a
digit, and `exit=0`. Otherwise stop and report the output.

## Undo

Only if step 2 showed that `DIR` did not exist before. Delete the downloaded
files, then each directory, which `rmdir` removes only if it is empty:

    rm DIR/All/Hashed/*.pkg; echo "exit=$?"
    rmdir DIR/All/Hashed DIR/All DIR; echo "rmdir-exit=$?"

Expected: `exit=0` and `rmdir-exit=0`. If `rmdir` prints `Directory not empty`,
something else was put in `DIR` since: leave it, and report it.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | Newer versions (`nginx-lite-1.30.5,3`, `pcre2-10.48`); the `~` code in file names contains `$`. |
| 15.1-RELEASE | verified | 2026-09-24 | |
| 15.0-RELEASE | verified | 2026-09-24 | |
| 14.5-RELEASE | verified | 2026-09-24 | |
| 14.4-RELEASE | verified | 2026-09-24 | |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | The plain command works; no `IGNORE_OSVERSION` needed. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill, the inputs
`PACKAGE=nginx-lite` and `DIR=/root/packages`, and a tool that runs one command
on the test machine, followed it on a freshly reset system of every release
above. A run counts only when the model said DONE AND the independent check
(`verify.sh`: the nginx-lite and pcre2 files are in `DIR/All/Hashed/` and
nothing was installed) passed: all 9 did. A manual review of the command logs
showed exactly the skill's four commands on every release.

## Not verified

- The network-failure row in step 3 was not provoked.
- Undo was run by hand on 14.0, 15.1 and 16.0-CURRENT (2026-09-24 UTC), not by
  the weak model. With another file placed in `DIR/All`, `rmdir` printed
  `Directory not empty` and the file was left in place.
- Installing the files on a different machine than the one that downloaded
  them. `ports/pkg-add-offline` was tested on the same machine, with its
  network cut off.

## Differences from the Handbook

- The Handbook says to `cd` into the download directory and run
  `pkg install nginx-lite-1.22.1,3.pkg`. In every release tested, the files
  are not in that directory but in `DIR/All/Hashed/`, and their names have a
  `~<code>` part, so that file name does not exist. Also, `pkg install` with a
  file name still tries to contact the repository, and fails without a
  network. See `ports/pkg-add-offline` for what does work.

## Source

FreeBSD Handbook, "Installing and Fetching Packages",
https://docs.freebsd.org/en/books/handbook/ports/#pkg-installing-fetching
