---
name: ports-pkg-kmods-repo
description: Make sure pkg can install ready-built kernel modules (graphics and hardware drivers) matching this release, adding the kernel-module repository where it is missing.
handbook: ports/#kmod-repository
handbook_commit: bdf18a0458
---

# Enable the kernel-module package repository

## What this does

Some drivers, such as graphics drivers, are kernel modules installed as
packages. They must be built for the exact release the machine runs, so they
come from a separate repository. On most releases that repository is already
set up; on 14.2 it has to be added. This skill checks, adds it where needed,
and confirms that pkg can see the modules. It does not install any module.

## Before you start

- You need: a root shell, network access to `pkg.FreeBSD.org`, and pkg itself
  installed (skill `ports/pkg-bootstrap`).
- This changes: on 14.2 only, creates `/usr/local/etc/pkg/repos/kmods.conf`.
- Time: under a minute.
- Risk: low. Undo removes the file.

## Inputs

None.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.2-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.

| The line starts with | Do this |
|---|---|
| `14.0-` or `14.1-` | no kernel-module repository exists for these releases. Say so in your final answer and end with DONE: reporting this is the correct result here |
| `14.2-` | EoL; the repository exists but is not set up. Go to step 2 |
| `14.3-` | EoL; already set up, named `FreeBSD-kmods`. Go to step 4 |
| `14.4-` or `14.5-` | already set up, named `FreeBSD-kmods`. Go to step 4 |
| `15.` or `16.` | already set up, named `FreeBSD-ports-kmods`. Go to step 4 |

## Step 2: Check that the file does not exist yet (14.2 only)

Run:

    ls /usr/local/etc/pkg/repos/kmods.conf; echo "exit=$?"

| If you see | Do this |
|---|---|
| `No such file or directory` and `exit=1` | go to step 3 |
| the file name and `exit=0` | it exists already. Go to step 4 |
| anything else | stop, and report the full output |

## Step 3: Add the repository (14.2 only)

Run exactly this, in one go:

    mkdir -p /usr/local/etc/pkg/repos && printf '%s\n' 'FreeBSD-kmods: {' '  url: "pkg+https://pkg.FreeBSD.org/${ABI}/kmods_quarterly_2",' '  mirror_type: "srv",' '  signature_type: "fingerprints",' '  fingerprints: "/usr/share/keys/pkg",' '  enabled: yes' '}' > /usr/local/etc/pkg/repos/kmods.conf; echo "exit=$?"

Expected: only `exit=0`. The `_2` at the end of `kmods_quarterly_2` is the
minor version of 14.2: modules are built for each minor version separately.

## Step 4: Download the catalogues

pkg must download the repository's list of modules before it can show them.
Run the command for your release (14.2 and 14.3 have reached end of life, so
pkg needs the setting that accepts that):

- **14.2, 14.3**: `env IGNORE_OSVERSION=yes pkg update -f; echo "exit=$?"`
- **14.4, 14.5, 15.x, 16.0-CURRENT**: `pkg update -f; echo "exit=$?"`

Expected: among the lines, `FreeBSD-kmods repository update completed. <number>
packages processed.` (on 15.x and 16.0-CURRENT: `FreeBSD-ports-kmods ...`),
then `exit=0`. Anything else: stop and report the output.

## Step 5: Verify

Run the command for your release. It counts the modules the repository
offers:

- **14.2, 14.3**: `env IGNORE_OSVERSION=yes pkg rquery -r FreeBSD-kmods %n | wc -l; echo "exit=$?"`
- **14.4, 14.5**: `pkg rquery -r FreeBSD-kmods %n | wc -l; echo "exit=$?"`
- **15.x, 16.0-CURRENT**: `pkg rquery -r FreeBSD-ports-kmods %n | wc -l; echo "exit=$?"`

Expected: a number above 0 (about 200 to 300), then `exit=0`. If the number
is 0, stop and report.

## Undo

On 14.2, only if step 3 created the file:

    rm /usr/local/etc/pkg/repos/kmods.conf; echo "exit=$?"

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | Already set up (`FreeBSD-ports-kmods`, `kmods_latest`): 280 modules. |
| 15.1-RELEASE | verified | 2026-09-24 | Already set up (`FreeBSD-ports-kmods`): 239 modules. |
| 15.0-RELEASE | verified | 2026-09-24 | Already set up (`FreeBSD-ports-kmods`): 240 modules. |
| 14.5-RELEASE | verified | 2026-09-24 | Already set up (`FreeBSD-kmods`): 288 modules. |
| 14.4-RELEASE | verified | 2026-09-24 | Already set up (`FreeBSD-kmods`): 289 modules. |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | Already set up (`FreeBSD-kmods`, `kmods_quarterly_3`): 245 modules; needs `IGNORE_OSVERSION`. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | Added by this skill (`kmods_quarterly_2`): 209 modules. |
| 14.1-RELEASE (EoL) | verified (no-op) | 2026-09-24 | No kernel-module repository exists; the skill reports that. |
| 14.0-RELEASE (EoL) | verified (no-op) | 2026-09-24 | As 14.1. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill and a tool that runs
one command on the test machine, followed it on a freshly reset system of
every release above. A run counts only when the model said DONE AND the
independent check (`verify.sh`: pkg sees modules in the release's module
repository; on 14.0 and 14.1, nothing was added) passed: all 9 did. A manual
review of the command logs showed each release taking its own branch of
step 1: one command on 14.0 and 14.1, the five steps on 14.2, and steps 4 and
5 elsewhere, with the end-of-life setting on 14.2 and 14.3 only.

## Not verified

- Installing and loading an actual kernel module is not part of this skill
  and was not tested.

## Differences from the Handbook

- The Handbook says to add `kmods.conf`; on 14.3 and later the repository is
  already configured by the release (`FreeBSD-kmods` in 14.x,
  `FreeBSD-ports-kmods` in 15.x and 16.0-CURRENT), so there is nothing to add.
- For 14.0 and 14.1 no kernel-module repository exists on pkg.FreeBSD.org
  (`kmods_quarterly_0` and `kmods_quarterly_1`: `Not Found`, 2026-09-24).
- On 14.2 and 14.3 a plain `pkg update -f` updates the module repository but
  still ends with `Error updating repositories!`, because they are end of
  life; the skill uses `IGNORE_OSVERSION=yes`.
- `pkg rquery -r REPO` does not download a repository's catalogue that was
  never downloaded: it prints nothing and still exits 0. Step 4 exists to
  avoid that silent empty answer.

## Source

FreeBSD Handbook, "Kernel modules repositories",
https://docs.freebsd.org/en/books/handbook/ports/#kmod-repository
