---
name: bsdinstall-media-write-usb
description: Write a downloaded FreeBSD memstick installation image to a USB stick with dd, only after checking the stick is not in use and is big enough, and read it back to check the copy.
handbook: bsdinstall/#bsdinstall-usb-dd
handbook_commit: bdf18a0458
---

# Write an installation image to a USB stick

## What this does

Copies a FreeBSD `memstick` or `mini-memstick` image, byte for byte, onto a
USB stick, so a computer can start the FreeBSD installer from it. Everything
on the stick is lost. The skill first checks that nothing on the machine is
using the stick (so it cannot be the disk the system runs from) and that it
is big enough, then writes, then reads the stick back and compares it with
the image.

## Before you start

- You need: a root shell, the image (skill `bsdinstall/media-download`), and
  the USB stick plugged in. Its name is `da` and a number, such as `da0`:
  `geom disk list` shows each disk's name (`Geom name:`), size
  (`Mediasize:`) and maker (`descr:`); the stick is the one that appeared when
  it was plugged in.
- This changes: **erases the USB stick** and writes the image to it.
- Time: about a minute per GB, depending on the stick.
- Risk: high if the wrong device is given; the checks in step 3 refuse any
  disk that is in use, which includes the one the system runs from.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `IMGPATH` | the full path of the image | `/var/tmp/freebsd-media/FreeBSD-14.5-RELEASE-amd64-memstick.img` |
| `DEVNAME` | the USB stick's device name, without `/dev/` | `da0` |

Everywhere below, replace `IMGPATH` and `DEVNAME` with these values, exactly
as given. Check them first:

- `IMGPATH`: `/var/tmp/freebsd-media/`, then a name of letters, digits and
  the characters `.` `_` `-` ending in `memstick.img`.
- `DEVNAME`: `da` followed by 1 to 3 digits. (`md` followed by 1 to 3
  digits, a memory disk, is also accepted, for trying the skill out.)

If either does not, stop and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24) | go to step 2. The steps are the same on every release |
| anything else | stop, and report the line: this skill was not tested there |

## Step 2: Check the image

Run:

    stat -f "type=%HT size=%z" IMGPATH; echo "exit=$?"

| If you see | Do this |
|---|---|
| `type=Regular File size=` a number above 0, then `exit=0` | write down the size (IMGSIZE below). Go to step 3 |
| anything else (such as `No such file or directory`) | stop, and report the output |

## Step 3: Check the stick

`geom -p` shows how the system sees the device. `Mode: r0w0e0` means nothing
has it open: no file system on it is mounted, and it is not part of a ZFS
pool or used for swap. The disk the system runs from always shows other
numbers. Run:

    geom -p DEVNAME; echo "exit=$?"; geom -p DEVNAME | awk '$1 == "Mediasize:" || $1 == "descr:" || $1 == "ident:" || $1 == "lunid:" || $1 == "file:"' | sha256 | sed 's/^/devid=/'

The last line is a fingerprint of the device: a checksum of its size, maker
description, serial number and similar lines. Expected, such as:

    Geom class: DISK
    Geom name: da0
    Providers:
    1. Name: da0
       Mediasize: 15518924800 (14G)
       Sectorsize: 512
       Mode: r0w0e0
       descr: SanDisk Cruzer Blade
    ...
    exit=0
    devid=4f0c2a…(64 characters 0-9 and a-f)

| If you see | Do this |
|---|---|
| `Geom class: DISK` (or `MD` for an `md` device), `Mode: r0w0e0`, a `Mediasize:` of at least IMGSIZE, then `exit=0`, then `devid=` and 64 characters `0`-`9` and `a`-`f` | nothing uses the device and the image fits. Write down the 64 characters after `devid=` (DEVID below) and the `descr:` line, if there is one, to report which device was written. Go to step 4 |
| a `Mode:` other than `r0w0e0` (such as `r3w3e8`) | something on the machine is using this device: it may be the system's own disk, or the stick is mounted. Stop, and report it: do not write |
| a `Mediasize:` smaller than IMGSIZE | the image does not fit. Stop, and report it |
| `geom: Cannot find provider 'DEVNAME'.` (with the name filled in), or another `Geom class:` | no such disk (or not a whole disk). Stop, and report the output |
| anything else | stop, and report the full output |

## Step 4: Write the image

The command checks once more that nothing uses the device and that it is
still the same device (the same fingerprint), and only then writes. `bs=1M`
writes in large blocks; `conv=sync` fills the last block with zeros. Run:

    if [ "$(geom -p DEVNAME | awk '$1 == "Mode:" { print $2 }')" = r0w0e0 ] && [ "$(geom -p DEVNAME | awk '$1 == "Mediasize:" || $1 == "descr:" || $1 == "ident:" || $1 == "lunid:" || $1 == "file:"' | sha256)" = "DEVID" ]; then dd if=IMGPATH of=/dev/DEVNAME bs=1M conv=sync 2>&1; echo "dd exit=$?"; else echo "refused: in use, changed, or gone"; fi

Expected, such as:

    648+0 records in
    648+0 records out
    679477248 bytes transferred in 6.998893 secs (97083536 bytes/sec)
    dd exit=0

| If you see | Do this |
|---|---|
| the three `dd` lines, then `dd exit=0` | written. Go to step 5 |
| `refused: in use, changed, or gone` | the device came into use since step 3, is not the same device any more, or is gone: nothing was written. Stop, and report it |
| `dd exit=` another number (with an error such as `Operation not permitted` or `Input/output error`) | stop, report the output, and end with FAILED: the stick may be partly written |
| anything else | stop, report the output, and end with FAILED |

## Step 5: Read it back

This reads as many bytes from the stick as the image has, and compares their
checksum with the image's. Run:

    [ "$(head -c IMGSIZE /dev/DEVNAME | sha256)" = "$(sha256 -q IMGPATH)" ] && echo "same as the image"; echo "exit=$?"

Expected: `same as the image`, then `exit=0`. Otherwise stop, report the
output, and end with FAILED: the stick does not hold the image (try another
stick).

Report that the image was written, to which device (and its `descr:`), and
that the stick can now be removed and used to start the installer.

## Undo

None: the stick's earlier contents are gone. The stick can be used again for
something else by writing to it or formatting it.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-28, snapshot 20260921 (a6deeaa2fb3b) |  |
| 15.1-RELEASE | verified | 2026-09-28 |  |
| 15.0-RELEASE | verified | 2026-09-28 |  |
| 14.5-RELEASE | verified | 2026-09-28 |  |
| 14.4-RELEASE | verified | 2026-09-28 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.2-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.1-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.0-RELEASE (EoL) | verified | 2026-09-28 | Also tried by hand (see below). |

## Weak-model check

2026-09-28 (UTC): claude-haiku-4-5, given only this skill, the inputs
`IMGPATH=/var/tmp/freebsd-media/FreeBSD-15.1-RELEASE-amd64-mini-memstick.img`
and `DEVNAME=md7` (not the skill's example), and a tool that runs one command
on the test machine, followed it on a freshly reset system of every release
above. The test machines have no USB stick, so `md7` was a 1 GB memory disk
backed by a file, filled with a pattern beforehand. A run counts only when
the model said DONE AND the independent check (`verify.sh`: `md7` is still the
memory disk made for the test, and the first bytes read from `md7`, as many
as the image has, match the image's published checksum;
`md7` is not in use; the image file is unchanged) passed: all 9 did, with
this version of the skill and scripts.

## Not verified

- No real USB stick was used: only a memory disk (`md`). The commands are the
  same for `da` devices.
- Tried by hand on 14.0 and 16.0: `geom -p` shows the system's own disk as
  `Mode: r3w3e8` (UFS) or `r3w3e7` (ZFS), an unused memory disk as
  `r0w0e0`, and one with a mounted file system as `r1w1e1`.
- Tried by hand on 16.0: after the memory disk was detached and attached
  again with another backing file under the same name, step 4's command
  refused to write (the fingerprint differed). A USB stick's fingerprint
  (its serial number) was not tried; sticks without one still differ by
  size or description only.
- Between step 4's check and the moment `dd` opens the device there is a
  very short gap; a stick unplugged and another plugged in under the same
  name in exactly that moment would not be noticed. Step 5 reads back
  through the same name.
- Starting a computer from the written stick was not tried.

## Differences from the Handbook

- The Handbook shows `dd if=... of=/dev/da0 bs=1M conv=sync` and warns to use
  the right device. The skill checks with `geom -p` that nothing uses the
  device (so the system disk is refused) and that the image fits, repeats the
  check (and that it is the same device, by a fingerprint of its size,
  description and serial) in the same command as `dd`, and reads the stick back afterwards.
- Writing with Windows (Image Writer) is not covered.

## Source

FreeBSD Handbook, "Writing an Image File to USB",
https://docs.freebsd.org/en/books/handbook/bsdinstall/#bsdinstall-usb-dd
