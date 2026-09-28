---
name: bsdinstall-media-download
description: Download a FreeBSD installation image and its checksum file from the FreeBSD servers, check the image against the checksum, and unpack it, ready to be written to a USB stick or disc.
handbook: bsdinstall/#bsdinstall-installation-media
handbook_commit: bdf18a0458
---

# Download and check a FreeBSD installation image

## What this does

Downloads one installation image of a FreeBSD release for 64-bit PCs
(`amd64`) into the folder `/var/tmp/freebsd-media`, together with the list of
checksums the FreeBSD project publishes for it. It checks that the image
matches its checksum (a corrupted download does not), unpacks it
(the images are compressed with `xz`), and checks the unpacked image too.

The image types:

| `TYPE` | What it is | Written to |
|---|---|---|
| `mini-memstick` | the installer only; downloads the rest during installation (needs a network) | a USB stick |
| `memstick` | the installer and everything to install | a USB stick |
| `bootonly` | like `mini-memstick` | a CD |
| `disc1` | like `memstick` | a CD |
| `dvd1` | like `disc1`, plus some packages | a DVD |

## Before you start

- You need: a root shell on a FreeBSD machine with Internet access, and free
  space in `/var/tmp`: about 1 GB for `mini-memstick` or `bootonly`, 3 GB for
  `memstick` or `disc1`, 10 GB for `dvd1`.
- This changes: creates the folder `/var/tmp/freebsd-media` and the files in
  it.
- Time: a few seconds to several minutes, depending on the image and the
  connection.
- Risk: low. Step 2 checks there is room before starting.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `VERSION` | the FreeBSD release to download | `15.1` |
| `TYPE` | the kind of image (see the table above) | `mini-memstick` |

Check them first: `VERSION` is exactly one of `14.0`, `14.1`, `14.2`, `14.3`,
`14.4`, `14.5`, `15.0`, `15.1`; `TYPE` is exactly one of `mini-memstick`,
`memstick`, `bootonly`, `disc1`, `dvd1`. If either is not, stop and report:
do not run any command with it.

Then work out these three values, and use them everywhere below:

- `BASEURL`: for `VERSION` `14.0`, `14.1`, `14.2` or `14.3` (end of life as of
  2026-09-24, so moved to the archive):
  `https://archive.freebsd.org/old-releases/amd64/amd64/ISO-IMAGES/VERSION`;
  for the others: `https://download.freebsd.org/releases/amd64/amd64/ISO-IMAGES/VERSION`
  (with `VERSION` filled in).
- `SUMFILE`: `CHECKSUM.SHA256-FreeBSD-VERSION-RELEASE-amd64`.
- `IMGFILE`: `FreeBSD-VERSION-RELEASE-amd64-TYPE.img` if `TYPE` is
  `mini-memstick` or `memstick`; `FreeBSD-VERSION-RELEASE-amd64-TYPE.iso`
  otherwise.

For example, `VERSION=15.1` and `TYPE=mini-memstick` give `BASEURL`
`https://download.freebsd.org/releases/amd64/amd64/ISO-IMAGES/15.1`, `SUMFILE`
`CHECKSUM.SHA256-FreeBSD-15.1-RELEASE-amd64` and `IMGFILE`
`FreeBSD-15.1-RELEASE-amd64-mini-memstick.img`.

## Step 1: Identify the release of this machine

Run:

    freebsd-version -u

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number | go to step 2. The steps are the same on every release |
| anything else | stop, and report the line: this skill was not tested there |

## Step 2: Check the free space

Run:

    df -k /var/tmp | awk 'NR == 2 { print "free=" int($4 / 1024) " MB" }'

| If you see | Do this |
|---|---|
| `free=` at least 1000 MB for `mini-memstick` or `bootonly`, 3000 MB for `memstick` or `disc1`, 10000 MB for `dvd1` | go to step 3 |
| a smaller number | not enough space: downloading would fill the disk. Stop, report it, and end with FAILED |
| anything else | stop, report the output, and end with FAILED |

## Step 3: Download

The folder must not exist yet, so nothing earlier is mixed in. Run:

    mkdir /var/tmp/freebsd-media && cd /var/tmp/freebsd-media && env -i PATH=/usr/bin:/bin fetch BASEURL/SUMFILE && env -i PATH=/usr/bin:/bin fetch BASEURL/IMGFILE.xz; echo "exit=$?"; ls -l /var/tmp/freebsd-media

Expected: a line for each file as it arrives, `exit=0`, then the two files
listed: `SUMFILE` (about 1 KB) and `IMGFILE.xz`.

| If you see | Do this |
|---|---|
| `exit=0` and both files listed | go to step 4 |
| `mkdir: /var/tmp/freebsd-media: File exists` | the folder is left from an earlier download, perhaps of another image. Stop, report it, and end with FAILED: it must be removed first (Undo), then the skill run again |
| `fetch: ... Not Found` | that release or image is not on the server. Stop, report the output, and end with FAILED |
| anything else | stop, report the output, and end with FAILED (Undo removes what was downloaded) |

## Step 4: Check the download

The command takes the published checksum from the line for exactly
`IMGFILE.xz` in `SUMFILE`, computes the file's own checksum, and prints `OK`
only if the two are equal. Run:

    cd /var/tmp/freebsd-media && want=$(awk -v f="(IMGFILE.xz)" '$1 == "SHA256" && $2 == f && $3 == "=" { print $4 }' SUMFILE) && { [ -n "$want" ] || { echo "IMGFILE.xz: not in SUMFILE"; false; }; } && [ "$(sha256 -q IMGFILE.xz)" = "$want" ] && echo "IMGFILE.xz: OK"; echo "exit=$?"

| If you see | Do this |
|---|---|
| `IMGFILE.xz: OK`, then `exit=0` | the download is intact. Go to step 5 |
| `IMGFILE.xz: not in SUMFILE` | the checksum file does not list that image (check `VERSION` and `TYPE`). Stop, report it, and end with FAILED |
| anything else (such as only `exit=1`) | the download is damaged. Stop, report the output, and end with FAILED: remove the folder (Undo) and download again |

## Step 5: Unpack and check again

`xz -dk` unpacks the image and keeps the compressed file; then the unpacked
image is checked the same way. Run:

    cd /var/tmp/freebsd-media && xz -dk IMGFILE.xz && want=$(awk -v f="(IMGFILE)" '$1 == "SHA256" && $2 == f && $3 == "=" { print $4 }' SUMFILE) && { [ -n "$want" ] || { echo "IMGFILE: not in SUMFILE"; false; }; } && [ "$(sha256 -q IMGFILE)" = "$want" ] && echo "IMGFILE: OK"; echo "exit=$?"

Expected:

    IMGFILE: OK
    exit=0

(with `IMGFILE` filled in). Anything else: stop, report the output, and end
with FAILED.

Report where the image is: `/var/tmp/freebsd-media/IMGFILE`.

## Undo

Remove the folder and everything in it:

    rm -r /var/tmp/freebsd-media; echo "exit=$?"

## Release results

The machine the skill runs on:

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-28, snapshot 20260921 (a6deeaa2fb3b) | Also tried by hand: 15.1 `mini-memstick` (about 116 MB, 3 seconds). |
| 15.1-RELEASE | verified | 2026-09-28 |  |
| 15.0-RELEASE | verified | 2026-09-28 |  |
| 14.5-RELEASE | verified | 2026-09-28 |  |
| 14.4-RELEASE | verified | 2026-09-28 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.2-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.1-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.0-RELEASE (EoL) | verified | 2026-09-28 | Also tried by hand: 15.1 `mini-memstick`. |

## Weak-model check

2026-09-28 (UTC): claude-haiku-4-5, given only this skill, the inputs
`VERSION=14.3`, `TYPE=bootonly` (not the skill's example; an end-of-life
release, so the archive server), and a tool that runs one command on the test
machine, followed it on a freshly reset system of every release above. A run
counts only when the model said DONE AND the independent check (`verify.sh`:
the unpacked and the compressed image are in `/var/tmp/freebsd-media`, and
both match the checksums in a copy of the checksum file the check downloads
itself) passed: all 9 did, with this version of the skill and scripts.

## Not verified

- Tried by hand on 16.0: after one byte of the unpacked image was changed,
  step 5's check printed no `OK` line and `exit=1`; for a file name not in
  the checksum file, the check also stops with `exit=1`. The model was not
  tested on a damaged download.
- `memstick`, `disc1` and `dvd1` (larger downloads) were not tried; nor
  other architectures (such as `arm64`).
- The checksum file comes from the same server as the image, so the check
  shows the image arrived intact, not that it is genuine: that rests on the
  `https` connection to the FreeBSD servers. The fetch commands run with an
  empty environment (`env -i`), so no setting such as `SSL_NO_VERIFY_PEER` or
  `SSL_CA_CERT_FILE` can weaken the certificate check; for the same reason a
  proxy set in the environment is not used (not tried behind a proxy). The FreeBSD project also
  publishes PGP-signed release announcements with the checksums; checking
  those needs a package (`gnupg`) and is not part of this skill.
- The size of the unpacked image is not checked before unpacking; the
  compressed image has already been checked against the published
  checksum by then.
- 14.0 to 14.3 are on `archive.freebsd.org`; the older
  `ftp-archive.freebsd.org` host does not accept `https`.

## Differences from the Handbook

- The Handbook points to the download page and shows the check. The skill
  gives the exact file names and servers (the archive for end-of-life
  releases), downloads into its own folder, and also checks the unpacked
  image.

## Source

FreeBSD Handbook, "Prepare the Installation Media",
https://docs.freebsd.org/en/books/handbook/bsdinstall/#bsdinstall-installation-media
