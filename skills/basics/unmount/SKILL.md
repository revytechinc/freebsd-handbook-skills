---
name: basics-unmount
description: Unmount a file system mounted at a folder under /mnt, safely - only when no program is using it, and never by force - noting how to mount it again.
handbook: basics/#disks-umount
handbook_commit: bdf18a0458
---

# Unmount a file system

## What this does

Unmounts the file system mounted at one folder under `/mnt` (for example a
disk mounted with skill `basics/mount-ufs`), so its files are no longer
shown there and the disk can be removed or used otherwise. Pending changes
are written to the disk first. The skill first checks that no program has a
file or folder open on it, and never forces the unmount.

## Before you start

- You need: a root shell.
- This changes: unmounts one file system. The folder itself stays.
- Time: seconds.
- Risk: low for file systems on disks. Undo mounts it again with the same
  general options (the ones `mount -p` shows, such as `rw`, `ro`, `nosuid`);
  options special to one kind of file system are not shown there and are
  not restored. (Memory file systems, `tmpfs`, are refused: their files would
  be lost.)

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `MOUNTPOINT` | the folder the file system is mounted at | `/mnt/data` |

Everywhere below, replace `MOUNTPOINT` with this value, exactly as given.
Check it first: exactly `/mnt`, or `/mnt/` followed by 1 to 32 letters,
digits or the characters `_` `-`. If it does not, stop and report: do not run
any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24) | go to step 2. The steps are the same on every release |
| anything else | stop, and report the line: this skill was not tested there |

## Step 2: Check what is mounted there

This also lists anything mounted inside the folder, which would have to be
unmounted first. Run:

    m=$(mount -p) || echo "MOUNTLIST-UNREADABLE"; printf '%s\n' "$m" | awk '$2 == "MOUNTPOINT" || index($2, "MOUNTPOINT/") == 1'; echo "end"

Expected, such as:

    /dev/ada1p1		/mnt/data		ufs	rw,nosuid 	2 2
    end

Go through these rows in order and use the first that matches:

| If you see | Do this |
|---|---|
| `MOUNTLIST-UNREADABLE` | the list of mounts could not be read. Stop, and report the full output |
| a line whose third column is `tmpfs` | a memory file system: its files are lost when it is unmounted, and Undo would bring back an empty one. Stop, and report it |
| any line whose second column starts with `MOUNTPOINT/` | another file system is mounted inside it. Stop, and report the lines: that one must be unmounted first (this skill again, with its folder) |
| two or more lines whose second column is `MOUNTPOINT` | several file systems are mounted on top of each other there. Stop, and report the lines |
| a line whose first column is not `/dev/` followed by only letters, digits and `/` `.` `_` `-`, or whose third column is not only lower-case letters and digits, or whose fourth column has characters other than letters, digits and `,` `_` `-` | Undo could not safely use these values. Stop, and report the line |
| a single line, whose second column is `MOUNTPOINT`, and then `end` | write down the first column (the device, DEVICE below), the third (the type, TYPE) and the fourth (the options, OPTIONS): Undo needs them. Go to step 3 |
| only `end` | nothing is mounted there. Stop, and report it: nothing needs doing |
| anything else | stop, and report the full output |

## Step 3: Check no program is using it

Only after step 2 found the mount (otherwise this lists the whole system).
Run:

    fstat -m -f MOUNTPOINT 2>&1; echo "end"

| If you see | Do this |
|---|---|
| a line starting with `fstat:` | `fstat` could not look at some program (often one that ended while it looked). Run this step once more; if such a line comes again, stop, and report the full output |
| only the header line (`USER     CMD          PID   FD MOUNT ...`), then `end` | no program that `fstat` can see is using it (step 4 still refuses if something else does). Go to step 4 |
| more lines between the header and `end` | those programs (the `CMD` and `PID` columns) have files or folders open there, are running from there, or have a file from there loaded in memory (`mmap`). Stop, and report them: they must be ended first (for example, a shell whose current folder is inside it must change folder) |
| anything else | stop, and report the full output |

## Step 4: Unmount

Run:

    umount MOUNTPOINT; echo "exit=$?"

| If you see | Do this |
|---|---|
| only `exit=0` | go to step 5 |
| `Device busy` and `exit=1` | something still uses it: a program that started after step 3, or something that `fstat` does not show, such as another mount whose source is inside it (look for lines of `mount -p` whose first column starts with `MOUNTPOINT/`) or a memory disk whose image file is inside it (look for `MOUNTPOINT/` in `mdconfig -lv`). Stop, and report it |
| anything else | stop, report the output, and end with FAILED |

Never use `umount -f`: programs using the file system can lose data they
have not yet written.

## Step 5: Verify

Run:

    m=$(mount -p) || echo "MOUNTLIST-UNREADABLE"; printf '%s\n' "$m" | awk '$2 == "MOUNTPOINT"'; echo "end"; ls -ld MOUNTPOINT

Expected: `end` with no line before it (no `MOUNTLIST-UNREADABLE` either), then the
folder's line (starting with `d`). Otherwise stop, report the output, and end
with FAILED.

Report that it is unmounted, and the DEVICE, TYPE and OPTIONS written down in
step 2 (needed to mount it again).

## Undo

Only if step 4 showed `exit=0`: mount it again with the values written down
in step 2 (which step 2 checked are safe to use; tried with UFS only):

    mount -t TYPE -o OPTIONS DEVICE MOUNTPOINT; echo "exit=$?"

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-28, snapshot 20260921 (a6deeaa2fb3b) | Also tried by hand (see below). |
| 15.1-RELEASE | verified | 2026-09-28 |  |
| 15.0-RELEASE | verified | 2026-09-28 |  |
| 14.5-RELEASE | verified | 2026-09-28 |  |
| 14.4-RELEASE | verified | 2026-09-28 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.2-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.1-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.0-RELEASE (EoL) | verified | 2026-09-28 |  |

## Weak-model check

2026-09-28 (UTC): claude-haiku-4-5, given only this skill, the input
`MOUNTPOINT=/mnt/hbdata` (not the skill's example), and a tool that runs one
command on the test machine, followed it on a freshly reset system of every
release above (UFS), where a memory disk backed by a file (the test machines
have no spare disk), holding a UFS file system with one file, was mounted
`rw,nosuid` there. A run counts only when the model said DONE AND the
independent check (`verify.sh`: the mount table is exactly the one from
before, without that mount; `/etc/fstab` is unchanged; the folder is still
there and empty; the file system is clean by `fsck -n` and still holds its
file) passed: all 9 did, with this version of the skill and scripts. The
command logs show exactly the skill's commands on every release.

## Not verified

- Tried by hand on 16.0 and 14.0 (with skill `basics/mount-ufs`): while a
  program's current folder is inside, `umount` gives `Device busy` and
  `fstat -f` lists the program; on a folder with nothing mounted, `fstat -f`
  lists the programs of the whole root file system, which is why step 3 comes
  after step 2; a second `umount` gives `not a file system root directory`.
- Undo was tried by hand on 16.0 and 14.0; the model did not run it.
- Step 2's command on a `tmpfs` mount was tried by hand on 16.0 (third
  column `tmpfs`); the model was not tested on any stop.
- File systems mounted outside `/mnt` (such as `/usr` or `/var`) are refused
  by the input rules: unmounting those can stop the running system.

## Differences from the Handbook

- The Handbook lists `umount` with a mount point, a device, `-a` or `-A`, and
  `-f`. The skill unmounts one folder under `/mnt`, checks with `fstat` that
  nothing uses it, and never uses `-f` (the Handbook itself warns against it)
  or `-a`/`-A`.

## Source

FreeBSD Handbook, "Using umount(8)",
https://docs.freebsd.org/en/books/handbook/basics/#disks-umount
