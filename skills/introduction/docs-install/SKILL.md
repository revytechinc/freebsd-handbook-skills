---
name: introduction-docs-install
description: Install FreeBSD's own documentation (the Handbook, the FAQ and other books and articles, in English) on this machine, to read it without a network connection.
handbook: introduction/#_additional_documentation
handbook_commit: bdf18a0458
---

# Install the FreeBSD documentation locally

## What this does

Installs the package `en-freebsd-doc`, which puts FreeBSD's books and
articles, including this Handbook and the FAQ, under
`/usr/local/share/doc/freebsd`, as web pages and as PDF files. Then checks
the Handbook and FAQ are there.

## Before you start

- You need: a root shell, network access to FreeBSD's servers, and pkg
  installed (skill `ports/pkg-bootstrap`). About 110 MB of free disk space.
- This changes: installs one package.
- Time: under a minute.
- Risk: low. Undo removes the package.

## Inputs

None.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Your release group |
|---|---|
| `14.0-RELEASE` to `14.3-RELEASE`, possibly followed by `-p` and a number (end of life as of 2026-09-24) | EoL |
| `14.4-RELEASE`, `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE`, possibly followed by `-p` and a number, or `16.0-CURRENT` | current |
| anything else | stop, and report the line: this skill was not tested there |

Why: on an end-of-life release pkg refuses to use FreeBSD's repository
unless told to (`IGNORE_OSVERSION=yes`); see `ports/pkg-install`.

## Step 2: Check it is not installed already

Run:

    pkg info -e en-freebsd-doc; echo "exit=$?"

| If you see | Do this |
|---|---|
| only `exit=1` | not installed. Go to step 3 |
| only `exit=0` | already installed. Go to step 4 to check the files |
| anything else | stop, and report the full output |

## Step 3: Install it

Run the command for your release group. The output goes into a file in
root's home directory, and only the end is shown:

- **current**: `pkg install -y en-freebsd-doc > /root/freebsd-doc-install.log 2>&1; echo "exit=$?"; tail -2 /root/freebsd-doc-install.log`
- **EoL**: `env IGNORE_OSVERSION=yes pkg install -y en-freebsd-doc > /root/freebsd-doc-install.log 2>&1; echo "exit=$?"; tail -2 /root/freebsd-doc-install.log`

Expected: `exit=0`, then lines such as:

    [1/1] Installing en-freebsd-doc-20260814,1...
    [1/1] Extracting en-freebsd-doc-20260814,1: .......... done

(the date in the version changes as the documentation is updated).
Anything else: stop, report the lines, and end with FAILED.

## Step 4: Verify

Run:

    ls /usr/local/share/doc/freebsd/en/books/handbook/handbook_en.pdf /usr/local/share/doc/freebsd/en/books/handbook/index.html /usr/local/share/doc/freebsd/en/books/faq/faq_en.pdf /usr/local/share/doc/freebsd/en/books/faq/index.html; echo "exit=$?"

Expected: the four paths, then `exit=0`. Otherwise stop and report.

The Handbook can now be read offline: open
`/usr/local/share/doc/freebsd/en/books/handbook/index.html` in a web browser,
or the PDF in a PDF reader.

## Undo

Only if step 3 showed `exit=0` (if step 2 found the package already
installed, it is not this skill's to remove):

    pkg delete -y en-freebsd-doc; echo "exit=$?"; rm -f /root/freebsd-doc-install.log

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-26, snapshot 20260921 (a6deeaa2fb3b) | `en-freebsd-doc-20260814,1`, 108 MiB. |
| 15.1-RELEASE | verified | 2026-09-26 | As 16.0. |
| 15.0-RELEASE | verified | 2026-09-26 | As 16.0. |
| 14.5-RELEASE | verified | 2026-09-26 | As 16.0. |
| 14.4-RELEASE | verified | 2026-09-26 | As 16.0. |
| 14.3-RELEASE (EoL) | verified | 2026-09-26 | As 16.0, with the **EoL** command (`IGNORE_OSVERSION=yes`). |
| 14.2-RELEASE (EoL) | verified | 2026-09-26 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-26 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-26 | As 14.3. |

## Weak-model check

2026-09-26 (UTC): claude-haiku-4-5, given only this skill and a tool that
runs one command on the test machine, followed it on a freshly reset system of
every release above. A run counts only when the model said DONE AND the
independent check (`verify.sh`: `en-freebsd-doc` installed from FreeBSD's
repository, and the Handbook and FAQ present as PDF files of a plausible size
and as web pages) passed: all 9 did. The command logs show exactly the
skill's four commands on every release, with the **EoL** command on 14.0 to
14.3 only.

## Not verified

- Other languages (the Handbook: replace `en` with another language's
  prefix) were not tried.
- Installing the documentation from the installer (bsdinstall), which the
  Handbook also mentions, belongs to chapter 2 and is not part of this skill.

## Differences from the Handbook

- On 14.0 to 14.3 (end of life) the install needs `IGNORE_OSVERSION=yes`,
  as every package install there does.
- The Handbook names only the PDF files; the package also has the web-page
  versions (`index.html` in each book's folder).

## Source

FreeBSD Handbook, "Additional Documentation" (in "About the FreeBSD Project"),
https://docs.freebsd.org/en/books/handbook/introduction/#_additional_documentation
