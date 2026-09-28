---
name: basics-mount-ufs
description: Mount a UFS file system from a disk partition at an empty folder under /mnt, read-write or read-only, so its files can be used; unmounting is the Undo.
handbook: basics/#mount-unmount
handbook_commit: bdf18a0458
---

# Mount a UFS file system

## What this does

Makes the files on a disk partition that holds a UFS file system (FreeBSD's
usual file system) appear in a folder under `/mnt`, until it is unmounted or
the system restarts. The mount uses `nosuid`, so programs on it cannot gain
extra rights (the Handbook calls it a useful security option). It can be
mounted read-only, so nothing on it can be changed.

This skill does not change `/etc/fstab`, so the file system is not mounted
again after a restart.

## Before you start

- You need: a root shell, and the name of the partition, such as `/dev/ada1p1`
  (`gpart show` lists the disks and partitions).
- This changes: mounts one file system; may create one empty folder under
  `/mnt`.
- Time: seconds.
- Risk: low. Undo unmounts it.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `DEVICE` | the partition's device | `/dev/ada1p1` |
| `MOUNTPOINT` | the folder to show its files in | `/mnt/data` |
| `ACCESS` | `rw` to allow changes, `ro` for read-only | `ro` |

Everywhere below, replace `DEVICE`, `MOUNTPOINT` and `ACCESS` with these
values, exactly as given. Check them first:

- `DEVICE`: `/dev/`, then only letters, digits and the characters `/` `.`
  `_` `-` (such as `/dev/ada1p1` or `/dev/gpt/data`); does not contain `..`
  and does not end with `/`.
- `MOUNTPOINT`: exactly `/mnt`, or `/mnt/` followed by 1 to 32 letters,
  digits or the characters `_` `-`.
- `ACCESS`: exactly `rw` or exactly `ro`.

If any of them does not, stop and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u; uname -m

| The lines are | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24), then `amd64` | go to step 2. The steps are the same on every release |
| anything else (another release, or a machine type other than `amd64`) | stop, and report the lines: this skill was not tested there (step 3 depends on how `amd64` stores numbers) |

## Step 2: Check the device

Run:

    ls -l DEVICE; echo "exit=$?"; fstyp DEVICE; echo "fstyp=$?"

| If you see | Do this |
|---|---|
| a line starting with `c` (a device) ending in `DEVICE`, `exit=0`, then `ufs`, `fstyp=0` | a UFS file system. Go to step 3 |
| `zfs` | part of a ZFS pool, which is not mounted this way. Stop, and report it |
| another word (such as `msdosfs`, `ntfs` or `cd9660`) | a different kind of file system, not covered by this skill. Stop, and report it |
| `No such file or directory` | there is no such device. Stop, and report it |
| anything else (such as `fstyp: DEVICE: filesystem not recognized`) | stop, and report the full output |

## Step 3: Check nothing is mounted there already

A partition can be reached by several names (such as `/dev/ada1p1` and a
label like `/dev/gpt/data`), so the command reads the file system's own
number (`fsid`) from the device and looks for it among everything mounted,
whatever name it was mounted by. It also looks for `DEVICE` and `MOUNTPOINT`
by name. Run:

    f=$(dumpfs DEVICE | awk '/superblock location/ { for (i = 1; i < NF; i++) if ($i == "[") { a = $(i+1); b = $(i+2) } } END { f = ""; n = split(a " " b, w, " "); for (j = 1; j <= n; j++) { x = w[j]; while (length(x) < 8) x = "0" x; f = f substr(x,7,2) substr(x,5,2) substr(x,3,2) substr(x,1,2) } print "fsid " f }'); echo "$f"; case "$f" in "fsid "????????????????) mount -v | grep -F "$f" ;; esac; mount -p | awk '$1 == "DEVICE" || $2 == "MOUNTPOINT"'; echo "end"

Go through these rows in order and use the first that matches:

| If you see | Do this |
|---|---|
| a line starting with `dumpfs:`, or `fsid` followed by fewer than 16 characters, or an `fsid` whose first 8 or last 8 characters are all `0` | the file system's number could not be read (or is one the system replaces when mounting). Stop, and report the full output |
| the `fsid` line, then one or more lines before `end` | the file system is already mounted (perhaps under another of its names), or something is mounted at `MOUNTPOINT`. Stop, and report the lines |
| `fsid ` followed by 16 characters `0`-`9` and `a`-`f`, then only `end` | go to step 4 |
| anything else | stop, and report the full output |

## Step 4: Check the folder

Run:

    ls -A MOUNTPOINT; echo "exit=$?"; ls -ld MOUNTPOINT

| If you see | Do this |
|---|---|
| `exit=0`, then a line starting with `d` ending in `MOUNTPOINT`, and nothing else | an empty folder. Go to step 6 |
| `MOUNTPOINT: No such file or directory` (twice), `exit=1`, and `MOUNTPOINT` is not exactly `/mnt` | the folder does not exist yet. Write down: **created**. Go to step 5 |
| any other lines before `exit=0` | the folder is not empty: mounting would hide its files. Stop, and report them |
| a line starting with `l` (a link) or `-` (a file) | not a folder. Stop, and report it |
| anything else | stop, and report the full output |

## Step 5: Create the folder (only if step 4 said so)

Run:

    mkdir MOUNTPOINT; echo "exit=$?"

Expected: only `exit=0`. Anything else: stop, report the output, and end with
FAILED.

## Step 6: Mount it

Run:

    mount -t ufs -o nosuid,ACCESS DEVICE MOUNTPOINT; echo "exit=$?"

Expected: only `exit=0`. Anything else: stop, report the output, and end with
FAILED (if step 5 created the folder, say that Undo removes it).

## Step 7: Verify

Run:

    mount -p | awk '$2 == "MOUNTPOINT"'; df -h MOUNTPOINT

Expected: one line showing `DEVICE`, `MOUNTPOINT`, `ufs` and options that
include `ACCESS` and `nosuid`, then the `df` lines showing the file system's
size and use, such as:

    /dev/ada1p1		/mnt/data		ufs	ro,nosuid 	2 2
    Filesystem     Size    Used   Avail Capacity  Mounted on
    /dev/ada1p1     62M    8.0K     57M     0%    /mnt/data

Otherwise stop, report the output, and end with FAILED: say that Undo
unmounts it.

Report where the files are now, and that the mount lasts until it is
unmounted (Undo) or the system restarts.

## Undo

**If step 6 showed `exit=0`** (it is mounted): first check nothing is using
it:

    fstat -f MOUNTPOINT

If it shows lines other than the header line (`USER CMD PID ...`), those
programs have files or folders open there: stop, and report them. Otherwise:

    umount MOUNTPOINT; echo "exit=$?"

Never use `umount -f`: programs using the file system can lose data they
have not yet written.

**If step 5 created the folder** (whether or not step 6 worked), and nothing
is mounted there (after `umount` above showed `exit=0`, or because step 6
failed), remove it:

    rmdir MOUNTPOINT; echo "exit=$?"

`rmdir` fails on a folder that something is mounted on (`Device busy`), and
never removes files.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-27, snapshot 20260921 (a6deeaa2fb3b) | Also tried by hand (see below). |
| 15.1-RELEASE | verified | 2026-09-27 |  |
| 15.0-RELEASE | verified | 2026-09-27 |  |
| 14.5-RELEASE | verified | 2026-09-27 |  |
| 14.4-RELEASE | verified | 2026-09-27 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-27 |  |
| 14.2-RELEASE (EoL) | verified | 2026-09-27 |  |
| 14.1-RELEASE (EoL) | verified | 2026-09-27 |  |
| 14.0-RELEASE (EoL) | verified | 2026-09-27 | Also tried by hand on a ZFS-root system. |

## Weak-model check

2026-09-27 (UTC): claude-haiku-4-5, given only this skill, the inputs
`DEVICE=/dev/md9`, `MOUNTPOINT=/mnt/hbdata`, `ACCESS=rw` (not the skill's
example), and a tool that runs one command on the test machine, followed it
on a freshly reset system of every release above (UFS). The test machines have
no spare disk, so `md9` was a memory disk backed by a file, holding a UFS file
system with one file. A run counts only when the model said DONE AND the
independent check (`verify.sh`: the mount table is the one from before plus
exactly `md9` on `/mnt/hbdata`, `ufs`, with `rw` and `nosuid`; the file is
readable there, and it is writable; `/etc/fstab` is unchanged) passed: all 9 did, with this version of
the skill and scripts. The command logs show exactly the skill's commands on
every release, including step 5.

## Not verified

- Only a memory disk (`md`) was used, not a real disk partition; the
  commands are the same for both.
- Tried by hand on 16.0 (UFS) and 14.0 (ZFS root): mounting the same device a
  second time gives `Device busy`; `umount` while a program is in the folder
  gives `Device busy`, and `fstat -f` shows the program; after it ends,
  `umount` works; a read-only mount refuses writes (`Read-only file system`).
- Tried by hand on 16.0: a device mounted read-write under a label
  (`/dev/label/...`) could still be mounted a second time read-only under its
  other name, `/dev/md8` (a read-write second mount gave `Device busy`).
  Step 3's command found the mount under either name, and matched the
  partition `/dev/vtbd0p4` to the root file system mounted as
  `/dev/gpt/rootfs`. The `fsid` in `mount -v` is the superblock `id` from
  `dumpfs` with the bytes of each half reversed, as on amd64 (the only
  platform tried); `mount -v` showed it for read-write and quiet read-only
  mounts alike;
  a file system whose number is shared with one already mounted (such as
  an exact copy of a disk, made with `dd`) gets a new number when mounted,
  so a mount of the copy is not found by number, only by name; other names (gmirror, geli, `diskid`) were not tried.
- A file system that was not cleanly unmounted may be refused for `rw` until
  it is checked with `fsck`; not tried.
- `/etc/fstab` (mounting at every start) needs a real disk to test across a
  restart, and is left for the Handbook's storage chapter.

## Differences from the Handbook

- `nodev` is not added: FreeBSD's `mount` rejects it (`mount option <nodev>
  is unknown`), and a device file on UFS cannot be opened (`Operation not
  supported`); tried on 16.0 and 14.0. Only devfs (`/dev`) gives access to
  devices.
- The Handbook shows `mount device mountpoint` and lists the options. The
  skill always adds `-t ufs` and `-o nosuid`, checks the device holds UFS and
  the folder is empty, and makes read-only a choice (`ro`, the Handbook's
  `-r`).

## Source

FreeBSD Handbook, "Mounting and Unmounting File Systems",
https://docs.freebsd.org/en/books/handbook/basics/#mount-unmount
