---
name: ports-pkg-post-install
description: After installing a package or port, list what needs attention - its install message, its configuration files, its documentation, and the services it can run - without changing anything.
handbook: ports/#ports-nextsteps
handbook_commit: bdf18a0458
---

# Check what a newly installed package needs

## What this does

Most programs need some setting up after they are installed. This skill
shows, for one installed package, everything the Handbook says to look at:
the message the package printed when it was installed, its configuration
files, its documentation, and the services (programs that run in the
background, started by a script in `/usr/local/etc/rc.d`) it provides.
Nothing is changed.

## Before you start

- You need: a root shell, and the package installed (skill
  `ports/pkg-install` or `ports/port-install`).
- This changes: nothing, apart from saving the package's file list in
  `/root/pkg-files.txt`.
- Time: seconds.
- Risk: none.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `PACKAGE` | the exact package name, without a version | `nginx-lite` |

Everywhere below, replace `PACKAGE` with this value, exactly as given.
`PACKAGE` must start with a lower-case letter or a digit, and may contain only
lower-case letters, digits, and the characters `.` `_` `+` `-`. If it
contains anything else, stop and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24) | go to step 2. The steps are the same on every release |
| anything else | stop, and report the line: this skill was not tested there |

## Step 2: Check the package is installed

Run:

    pkg info -e PACKAGE; echo "exit=$?"

| If you see | Do this |
|---|---|
| only `exit=0` | go to step 3 |
| only `exit=1` | the package is not installed. Stop, and report it |
| anything else | stop, and report the full output |

## Step 3: Read the install message

Packages can print a message when they are installed: notes on setting them
up, or warnings. It is easy to miss, so read it again. Run:

    pkg info -D PACKAGE

Expected: the package name and version, then the message (possibly empty),
for example for `nginx-lite`:

    nginx-lite-1.30.4,3:
    On install:
    Recent version of the NGINX introduces dynamic modules support.  ...

Write the message down (or "no message" if only the first line is shown).

## Step 4: List the package's files, and its configuration files

The list of files the package installed is saved once, with pkg's status, so
the next steps read a list that is known to be complete. Run:

    pkg info -l PACKAGE > /root/pkg-files.txt; echo "exit=$?"; grep '/usr/local/etc/' /root/pkg-files.txt | grep -v '/usr/local/etc/rc.d/'

| If you see | Do this |
|---|---|
| `exit=0`, then the package's files under `/usr/local/etc` (the place for configuration), one per line, or nothing if it has none | go to step 5 |
| any exit other than `exit=0` | pkg could not list the files (for example, another pkg command holds its database). Stop, and report the output: the rest of the report would be wrong |

Files ending in `.sample` or `-dist` are *templates*: the package's original
settings.

## Step 5: Check the working copies of the templates exist

Most ports mark their templates so that pkg also creates the working file
(the same name without `.sample` or `-dist`) at installation, unless one was
already there. That working file is the one to edit. Run:

    sed -nE 's#^[[:space:]]*(/usr/local/etc/.*)(\.sample|-dist)$#\1#p' /root/pkg-files.txt | while read -r f; do ls -l "$f"; done

Expected: one line per template, each showing the working file, such as
`-rw-r--r--  1 root wheel 2963 ... /usr/local/etc/nginx/nginx.conf`, or
nothing if the package has no templates.

| If you see | Do this |
|---|---|
| only lines starting with `-` or `l` (a file, or a link to one) | the working files exist. Go to step 6 |
| nothing | the package has no templates. Go to step 6 |
| a line ending in `No such file or directory` | that working file is missing. Write down its name (it can be made by copying the template, for example `cp -n /usr/local/etc/X.sample /usr/local/etc/X`), and go to step 6 |
| anything else | stop, and report the full output |

## Step 6: Count its documentation

Run:

    grep -c '/usr/local/share/doc/' /root/pkg-files.txt

Expected: a number, the count of documentation files (`0` if none). They are
under `/usr/local/share/doc/`; manual pages are read with `man`.

## Step 7: List its services

Run:

    sed -n 's#^[[:space:]]*/usr/local/etc/rc.d/##p' /root/pkg-files.txt | LC_ALL=C sort

Expected: the name of each startup script the package installed, one per
line (such as `nginx`), or nothing if it provides no service. A service does
not start by itself after installation: it must be enabled in `/etc/rc.conf`
and started (see "Starting Services" in the Handbook's configuration
chapter).

## Step 8: Report

Report the message (step 3), any missing working files (step 5), the
documentation count (step 6), and then, on its own line, the services from
step 7 in the order shown, separated by single spaces:

    RESULT: services NAME1 NAME2

or, if step 7 showed nothing:

    RESULT: services none

For `nginx-lite` the line is `RESULT: services nginx`.

The word `RESULT` must appear only on that one line: do not use it as a
heading or anywhere else in the report.

## Undo

This skill changes nothing on the system; it leaves the file list in
`/root/pkg-files.txt`, which can be removed with `rm /root/pkg-files.txt`.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-26, snapshot 20260921 (a6deeaa2fb3b) |  |
| 15.1-RELEASE | verified | 2026-09-26 | Also tried by hand with `nginx-lite`. |
| 15.0-RELEASE | verified | 2026-09-26 |  |
| 14.5-RELEASE | verified | 2026-09-26 |  |
| 14.4-RELEASE | verified | 2026-09-26 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-26 |  |
| 14.2-RELEASE (EoL) | verified | 2026-09-26 |  |
| 14.1-RELEASE (EoL) | verified | 2026-09-26 | Also tried by hand with `nginx-lite`. |
| 14.0-RELEASE (EoL) | verified | 2026-09-26 |  |

## Weak-model check

2026-09-26 (UTC): claude-haiku-4-5, given only this skill, the input
`PACKAGE=rsync` (not the skill's example), and a tool that runs one command
on the test machine, followed it on a freshly reset system of every release
above, with `rsync` installed from packages beforehand. This skill changes
nothing, so a run counts only when the model said DONE, its final message
contained exactly the line worked out beforehand without the model
(`answer.sh`, from the package's own file list: the `RESULT: services` line
naming its one startup script),
and that answer was the same after the run: all 9 did, with the final text. The command logs show
exactly the skill's commands on every release.

## Not verified

- The test package has exactly one service, so the sorting and joining of
  several names in the `RESULT` line, and the `none` case, were not
  exercised by the model runs.

- A package whose working configuration file is missing (step 5's third
  row) was not seen; both test packages had theirs.
- Templates named in other ways than `.sample` or `-dist` are not found by
  step 5.

## Differences from the Handbook

- The Handbook says to copy a `.sample` file to the name without `.sample`
  before editing. Ports that mark a template as a sample (with `@sample` in
  their file list; rsync and nginx do) have pkg create the working file at
  installation when it does not exist (tried on 15.1 and 14.1: `rsyncd.conf`
  next to `rsyncd.conf.sample`, `nginx.conf` next to `nginx.conf-dist`).
  Ports that do not mark it get no working copy, so step 5 checks.
- Templates can also end in `-dist` (nginx), not only `.sample`.
- The Handbook's note for csh users (`rehash`) is not part of the skill: it
  only matters in an interactive csh session.

## Source

FreeBSD Handbook, "Post-Installation Considerations",
https://docs.freebsd.org/en/books/handbook/ports/#ports-nextsteps
