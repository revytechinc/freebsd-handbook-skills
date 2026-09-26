---
name: ports-poudriere-repo
description: Make pkg on this machine use a package repository built by poudriere here, and install one package from it.
handbook: ports/#ports-poudriere
handbook_commit: bdf18a0458
---

# Install packages from your own poudriere repository

## What this does

poudriere (skill `ports/poudriere-bulk`) leaves a package repository in
`/usr/local/poudriere/data/packages/JAIL-TREE/`. This skill adds it to pkg as
a repository called `poudriere`, read straight from the disk (`file://`), and
installs one package from it. FreeBSD's own repositories stay enabled; the
package is taken from `poudriere` because the install names it.

## Before you start

- You need: a root shell and a repository built with `ports/poudriere-bulk`
  on this machine.
- This changes: creates `/usr/local/etc/pkg/repos/poudriere.conf` and
  installs `PACKAGE` (and any packages it needs from the same repository).
- Time: seconds.
- Risk: low. Undo removes the package and the file.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `JAIL` | the jail the packages were built in | `builder` |
| `TREE` | the ports tree they were built from | `local` |
| `PACKAGE` | the name of one package in that repository | `figlet` |

Everywhere below, replace `JAIL`, `TREE` and `PACKAGE` with these values,
exactly as given. `JAIL` and `TREE`: 1 to 20 characters, letters `a`-`z`,
`A`-`Z` and digits only. `PACKAGE`: starts with a letter or a digit, and
contains only letters, digits, and the characters `.` `_` `+` `-`. If any of
them does not, stop and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24) | go to step 2. The steps are the same on every release |
| anything else | stop, and report the line: this skill was not tested there |

## Step 2: Check the repository, the setting file, and the package

Run:

    ls /usr/local/poudriere/data/packages/JAIL-TREE/packagesite.pkg; echo "exit=$?"; ls /usr/local/etc/pkg/repos/poudriere.conf; echo "exit=$?"; pkg info -e PACKAGE; echo "exit=$?"; pkg -vv | grep -c '^  poudriere:'

The last command asks pkg itself whether any of its setting files already
defines a repository called `poudriere`: pkg reads every file in its
`repos` folders and merges repositories of the same name, so checking only
for `poudriere.conf` is not enough.

| If you see | Do this |
|---|---|
| the `packagesite.pkg` path and `exit=0`, then `No such file or directory` for `poudriere.conf` and `exit=1`, then `exit=1`, then `0` | go to step 3 |
| `No such file or directory` for `packagesite.pkg` | there is no such repository. Stop, and report it (see `ports/poudriere-bulk`) |
| the `poudriere.conf` path and `exit=0` (second) | a repository called `poudriere` is already set up. Stop, and report its contents (`cat /usr/local/etc/pkg/repos/poudriere.conf`): this skill does not change it |
| `exit=0` just before the last line | `PACKAGE` is already installed. Stop, and report it: this skill does not reinstall |
| a last line other than `0` | another setting file already defines a repository called `poudriere`. Stop, and report it (`pkg -vv` shows it): this skill does not change it |
| anything else | stop, and report the full output |

## Step 3: Add the repository

`set -C` makes the shell refuse to overwrite an existing file. Run:

    mkdir -p /usr/local/etc/pkg/repos && (set -C; printf '%s\n' 'poudriere: {' '    url: "file:///usr/local/poudriere/data/packages/JAIL-TREE",' '    enabled: yes' '}' > /usr/local/etc/pkg/repos/poudriere.conf); echo "exit=$?"; cat /usr/local/etc/pkg/repos/poudriere.conf

Expected: `exit=0`, then:

    poudriere: {
        url: "file:///usr/local/poudriere/data/packages/JAIL-TREE",
        enabled: yes
    }

with `JAIL` and `TREE` filled in. Anything else: stop and report.

## Step 4: Read the repository's catalogue

Run:

    pkg update -r poudriere; echo "exit=$?"

Expected, ending:

    poudriere repository update completed. 6 packages processed.
    poudriere is up to date.
    exit=0

(the number of packages varies). Anything else: stop and report.

## Step 5: Check the package is in it

Run:

    pkg rquery -r poudriere '%n-%v %o' PACKAGE; echo "exit=$?"

Expected: one line with the name, the version and the port, such as
`figlet-2.2.5_1 misc/figlet`, then `exit=0`. If only `exit=` is shown, or
anything else, stop and report: the package is not in this repository.

## Step 6: Check pkg itself would not be replaced

poudriere always builds pkg too, so the new repository contains a pkg
package. If it is newer than the pkg installed here, installing from it
would replace pkg itself first. Run:

    pkg query %v pkg; pkg rquery -r poudriere %v pkg; echo "exit=$?"

| If you see | Do this |
|---|---|
| two lines with the same version, such as `2.7.5` and `2.7.5`, then `exit=0` | go to step 7 |
| two different versions | installing would also replace pkg with the one built here. Stop, and report both versions |
| anything else | stop, and report the full output |

## Step 7: Install it

Run:

    pkg install -y -r poudriere PACKAGE > /root/pkg-poudriere.log 2>&1; echo "exit=$?"; tail -3 /root/pkg-poudriere.log

Expected: `exit=0`, and lines such as `Installing figlet-2.2.5_1...` and
`Extracting figlet-2.2.5_1: ...... done`. Anything else: stop, report the
lines, and end with FAILED.

## Step 8: Verify

Run:

    pkg query '%n %v %R' PACKAGE; echo "exit=$?"; pkg -vv | grep -A1 '^  poudriere:'

Expected: one line with the name, the version and `poudriere` (the
repository it came from), such as `figlet 2.2.5_1 poudriere`, then `exit=0`,
then pkg's view of that repository, whose `url` line must be:

    url             : "file:///usr/local/poudriere/data/packages/JAIL-TREE",

with `JAIL` and `TREE` filled in. Otherwise stop and report.

## Undo

Undo only what this run made. Remove the package only if step 7 showed
`exit=0`; remove the file only if step 3 showed `exit=0`. If the run stopped
at step 2 because the package or the file was already there, they are not
this skill's to remove.

    pkg delete -y PACKAGE; echo "exit=$?"

Expected: `exit=0` (if not, the package is still installed: stop and
report). Then:

    rm /usr/local/etc/pkg/repos/poudriere.conf; echo "exit=$?"; rm -f /root/pkg-poudriere.log

Expected: `exit=0`.

Packages installed only because `PACKAGE` needed them stay;
`ports/pkg-autoremove` removes them.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-26, snapshot 20260921 (a6deeaa2fb3b) | UFS and ZFS. |
| 15.1-RELEASE | verified | 2026-09-26 | UFS and ZFS. |
| 15.0-RELEASE | verified | 2026-09-26 | UFS and ZFS. |
| 14.5-RELEASE | verified | 2026-09-26 | UFS and ZFS. |
| 14.4-RELEASE | verified | 2026-09-26 | UFS and ZFS. |
| 14.3-RELEASE (EoL) | verified | 2026-09-26 | UFS and ZFS. Unlike FreeBSD's own repository on an end-of-life release, no `IGNORE_OSVERSION` is needed: the packages were built for this release. |
| 14.2-RELEASE (EoL) | verified | 2026-09-26 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-26 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-26 | As 14.3. |

## Weak-model check

2026-09-26 (UTC): claude-haiku-4-5, given only this skill, the inputs
`JAIL=testjail`, `TREE=testtree`, `PACKAGE=tree` (not the skill's examples),
and a tool that runs one command on the test machine, followed it on a
freshly reset system of every release above, once on a UFS machine and once
on a ZFS machine (18 runs). Beforehand a repository was built from
`sysutils/tree` as `ports/poudriere-bulk` builds it. A run counts only when
the model said DONE AND the independent check (`verify.sh`: the setting file
is exactly as the skill writes it; `pkg -vv` shows the `poudriere` repository
with its `file://` URL and enabled; pkg itself was not replaced; `tree` is
installed, recorded as coming from
`poudriere`, with the version that repository holds; and it runs) passed:
all 18 did, with the final text and scripts. The command logs show the
skill's commands on every run; on one, the model ran step 2's checks one at
a time, which changes nothing.

## Not verified

- Tried by hand on 15.1: with a dependency already installed from FreeBSD's
  repository (`indexinfo`, needed by `gmake`) and a newer build of it in the
  local repository, `pkg install -r poudriere gmake` installed only `gmake`
  and left `indexinfo` as it was. Only pkg itself is replaced first when a
  newer one is offered, which step 6 guards.
- Step 2's last command reports `0` also if `pkg -vv` itself fails; a broken
  setting file then makes step 4 fail, so the run still stops.

- Serving the repository to other machines over HTTP, as the Handbook
  suggests, and signing it, were not tried; `file://` works only on the
  machine that holds the repository.
- Disabling FreeBSD's own repository (the Handbook's `FreeBSD: { enabled:
  no }`) was not tried. On 15 and 16 the base system also comes from pkg
  (`FreeBSD-base`), so check what else that would affect first.

## Differences from the Handbook

- The Handbook's example repository is called `custom`; the skill calls it
  `poudriere` and uses the `file://` form.
- The skill keeps FreeBSD's repositories enabled and installs with `-r
  poudriere`, so the package asked for, and any packages it needs that are
  not installed yet, come from the local repository.

## Source

FreeBSD Handbook, "Building Packages with poudriere",
https://docs.freebsd.org/en/books/handbook/ports/#ports-poudriere
