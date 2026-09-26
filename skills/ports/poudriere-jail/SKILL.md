---
name: ports-poudriere-jail
description: Configure poudriere and create a build jail with the same FreeBSD release as the machine, ready for building packages.
handbook: ports/#poudriere-initialization
handbook_commit: bdf18a0458
---

# Set up poudriere and create a build jail

## What this does

poudriere builds packages inside *jails*: small, separate FreeBSD systems
that keep each build clean. This skill sets the two settings poudriere needs
in `/usr/local/etc/poudriere.conf` (where to download FreeBSD from, and
whether to use ZFS), then creates one jail with the same FreeBSD release as
this machine. Next steps: `ports/poudriere-ports-tree` (give poudriere a
ports tree) and `ports/poudriere-bulk` (build packages).

## Before you start

- You need: a root shell, network access to FreeBSD's servers, poudriere
  installed (skill `ports/pkg-install` with `PACKAGE=poudriere`), and about
  2 GB of free disk space for the jail.
- This changes: sets `FREEBSD_HOST` and `ZPOOL` or `NO_ZFS` in
  `/usr/local/etc/poudriere.conf`, creates `/usr/ports/distfiles` if it is
  missing, and creates the jail under `/usr/local/poudriere/jails/`. On an
  end-of-life release it also writes `/usr/local/etc/poudriere.d/JAIL-make.conf`.
- Time: a few minutes (downloading the base system).
- Risk: low. Undo deletes the jail.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `JAIL` | a name for the jail | `builder` |

Everywhere below, replace `JAIL` with this value, exactly as given. It must
be 1 to 20 characters: letters `a`-`z`, `A`-`Z` and digits only, and not
`JAILNAME` (the word poudriere uses as a heading). If it is not, stop and
report: do not run any command with it.

## Step 1: Identify the release and the machine type

Run:

    freebsd-version -u | sed 's/-p[0-9]*$//'; uname -m

Expected: two lines, such as `15.1-RELEASE` and `amd64`. The first line,
exactly as shown, is called `VERSION` below.

| The first line is | Your release group |
|---|---|
| exactly `14.0-RELEASE`, `14.1-RELEASE`, `14.2-RELEASE` or `14.3-RELEASE` (end of life as of 2026-09-24) | EoL |
| exactly `14.4-RELEASE`, `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT` | current |
| anything else (for example a `-STABLE`, `-BETA` or `-RC` version) | stop, and report it: this skill was not tested there |

If the second line is not `amd64`, stop and report it: this skill was only
tested on `amd64`.

Why: FreeBSD's download server keeps only supported releases. An end-of-life
release has to come from the archive server, and the Ports Collection
refuses to build on it unless told to (see step 6).

## Step 2: Check poudriere and the file system

Run:

    pkg info -E poudriere; echo "exit=$?"; zfs list -H -o name /; echo "exit=$?"

| If you see | Do this |
|---|---|
| a line such as `poudriere-3.4.8`, `exit=0`, then a name such as `zroot/ROOT/default` and `exit=0` | ZFS. The part before the first `/` (here `zroot`) is called `POOL`. Go to step 3 |
| a line such as `poudriere-3.4.8`, `exit=0`, then `'/': not a ZFS filesystem` and `exit=1` | no ZFS. Go to step 3 |
| `pkg: No package(s) matching poudriere` and `exit=1` first | poudriere is not installed. Stop, and report it (see `ports/pkg-install`) |
| anything else | stop, and report the full output |

## Step 3: Set poudriere's configuration

On a ZFS machine poudriere refuses to do anything (`ZPOOL variable is not
set`) until this is done. Run the command for your file system:

- **ZFS**: `sysrc -f /usr/local/etc/poudriere.conf FREEBSD_HOST=https://download.FreeBSD.org ZPOOL=POOL; echo "exit=$?"`
- **no ZFS**: `sysrc -f /usr/local/etc/poudriere.conf FREEBSD_HOST=https://download.FreeBSD.org NO_ZFS=yes; echo "exit=$?"`

Expected: one line per setting, showing the old and the new value, then
`exit=0`, such as:

    FREEBSD_HOST: _PROTO_://_CHANGE_THIS_ -> https://download.FreeBSD.org
    ZPOOL:  -> zroot
    exit=0

Anything else: stop and report.

## Step 4: Make the download folder, and check the jail name is free

poudriere keeps downloaded sources in `/usr/ports/distfiles`. Run:

    mkdir -p /usr/ports/distfiles && poudriere jail -l; echo "exit=$?"

| If you see | Do this |
|---|---|
| a header line starting `JAILNAME`, no line starting with `JAIL` followed by a space, then `exit=0` | go to step 5 |
| a line starting with `JAIL` followed by a space | a jail with that name exists. Stop, and report it |
| anything else | stop, and report the full output |

## Step 5: Create the jail

Run the command for your release group. The output is long, so it goes into
a file in root's home directory and only the end is shown:

- **current**: `poudriere jail -c -j JAIL -v VERSION > /root/poudriere-jail.log 2>&1; echo "exit=$?"; tail -3 /root/poudriere-jail.log`
- **EoL**: `poudriere jail -c -j JAIL -v VERSION -m url=https://archive.freebsd.org/old-releases/amd64/amd64/VERSION/ > /root/poudriere-jail.log 2>&1; echo "exit=$?"; tail -3 /root/poudriere-jail.log`

Expected, after a few minutes, `exit=0` and a last line such as:

    [00:01:45] Jail builder 15.1-RELEASE-p3 amd64 is ready to be used

(On a supported release the jail is updated to the newest patch level, so
the version may end in `-p` and a number.)

| If you see | Do this |
|---|---|
| `exit=0` and a last line ending in `is ready to be used` | EoL: go to step 6. current: go to step 7 |
| anything else | stop: report the lines shown, and end with FAILED |

## Step 6 (EoL only): Allow building on an end-of-life release

Without this, every build in the jail stops with `Failed: check-sanity`
(`Ports Collection support for your FreeBSD version has ended`). Run:

    ls /usr/local/etc/poudriere.d/JAIL-make.conf; echo "exit=$?"

If it shows `No such file or directory` and `exit=1`, run:

    printf '%s\n' 'ALLOW_UNSUPPORTED_SYSTEM=yes' > /usr/local/etc/poudriere.d/JAIL-make.conf; echo "exit=$?"

Expected: `exit=0`. If the file already existed, stop and report it: this
skill does not edit it.

## Step 7: Verify

Run:

    poudriere jail -l; echo "exit=$?"

Expected: a header line starting `JAILNAME`, a line starting with `JAIL`
that shows `VERSION` (possibly with `-p` and a number after it) and `amd64`,
then `exit=0`. Otherwise stop and report.

## Undo

Delete the jail (it does not ask for confirmation):

    poudriere jail -d -j JAIL; echo "exit=$?"

Expected: `Removing JAIL jail... done`, then `exit=0`.

On an end-of-life release also remove the file from step 6:
`rm /usr/local/etc/poudriere.d/JAIL-make.conf`. The settings from step 3 can
stay; they only matter to poudriere.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-25, snapshot 20260921 (a6deeaa2fb3b) | UFS and ZFS. The default method fetches the 16.0-CURRENT snapshot. |
| 15.1-RELEASE | verified | 2026-09-25 | UFS and ZFS. The jail comes up as `15.1-RELEASE-p3`. |
| 15.0-RELEASE | verified | 2026-09-25 | UFS and ZFS. |
| 14.5-RELEASE | verified | 2026-09-25 | UFS and ZFS. |
| 14.4-RELEASE | verified | 2026-09-25 | UFS and ZFS. |
| 14.3-RELEASE (EoL) | verified | 2026-09-25 | UFS and ZFS. Needs the **EoL** command: `download.FreeBSD.org` answers `Not Found` for the MANIFEST (seen on 14.1). Without step 6 a build fails `check-sanity` (seen on 14.1). |
| 14.2-RELEASE (EoL) | verified | 2026-09-25 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-25 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-25 | As 14.3. |

## Weak-model check

2026-09-25 (UTC): claude-haiku-4-5, given only this skill, the input
`JAIL=testjail` (not the skill's example), and a tool that runs one command
on the test machine, followed it on a freshly reset system of every release
above, once on a UFS machine and once on a ZFS machine (18 runs). Beforehand
poudriere was installed from packages, with its configuration as installed.
A run counts only when the model said DONE AND the independent check
(`verify.sh`: `FREEBSD_HOST` set; `ZPOOL` set to the root pool on ZFS, or
`NO_ZFS=yes` on UFS; the jail `testjail` listed with this machine's release
and `amd64`; its base system present and of that release; and the jail's
`make.conf` allowing builds on 14.0 to 14.3 only) passed: all 18 did, with
the final text and scripts. The command logs show the ZFS or UFS command
matching each machine, and the **EoL** commands on 14.0 to 14.3 only; on
one machine the model also read the configuration back with `grep`, which
changes nothing.

## Not verified

- Only `amd64` jails on `amd64` machines. The Handbook's `-a i386` was not
  tried.
- Jails for a release other than the machine's own were not tried.
- A jail from the archive server (end-of-life releases) is not updated to
  the newest patch level.

## Differences from the Handbook

- The Handbook says to copy `poudriere.conf.sample` to `poudriere.conf`.
  Installing the poudriere package now does that itself; the skill only
  sets the two values.
- The Handbook creates a `13.1-RELEASE` jail from the download server. For
  end-of-life releases that no longer works; the skill uses the archive
  server (`https://archive.freebsd.org/old-releases/`) with `-m url=`. The
  archive's other name, `ftp-archive.freebsd.org`, has a certificate for
  `archive.freebsd.org` only, so `https://ftp-archive...` fails.
- Not in the Handbook: on a ZFS machine, poudriere refuses every command
  (`ZPOOL variable is not set`) until `ZPOOL` is set, so the skill sets the
  configuration (step 3) before listing jails (step 4).
- Not in the Handbook: builds on an end-of-life release need
  `ALLOW_UNSUPPORTED_SYSTEM=yes` in the jail's `make.conf` (step 6).

## Source

FreeBSD Handbook, "Building Packages with poudriere",
https://docs.freebsd.org/en/books/handbook/ports/#poudriere-initialization
