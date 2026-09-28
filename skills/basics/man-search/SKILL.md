---
name: basics-man-search
description: Find which manual pages cover a word (man -k), building the manual-page search database first if the system does not have one yet, as on a new 15.0 or later system.
handbook: basics/#basics-more-information
handbook_commit: bdf18a0458
---

# Search the manual pages

## What this does

Lists the manual pages whose name or one-line description contains a word,
such as `crontab` or `mount`, with the section each is in (`crontab(1)` is
the command, `crontab(5)` the file format). This is the Handbook's `man -k`.

`man -k` searches a database, `/usr/share/man/mandoc.db`. From 15.0 on, a new
system has no such database until the weekly maintenance job
(`periodic weekly`) has built it, and `man -k` then finds nothing for any
word. The skill builds the database in that case, the same way the weekly
job does, and searches again.

## Before you start

- You need: a root shell whenever step 2 finds nothing or shows a
  `NOT indexed` folder (step 3 builds the databases; searching alone needs
  no root).
- This changes: nothing, or (step 3) rebuilds the search database of every
  manual-page folder, as the weekly job does (a few seconds).
- Time: seconds.
- Risk: none. The weekly job rebuilds the database anyway.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `KEYWORD` | the word to look for | `chmod` |

Everywhere below, replace `KEYWORD` with this value, exactly as given. Check
it first: 1 to 32 letters, digits or the characters `_` `-`, not starting
with `-`. If it is not, stop and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24) | go to step 2. The steps are the same on every release |
| anything else | stop, and report the line: this skill was not tested there |

## Step 2: Search

The command searches with `man -k` and prints its exit status and the pages
it found. It then joins those pages into one `RESULT:` line, separated by
`; ` (one page can have several names, separated by `, `), and names any
manual-page folder whose search database is missing or does not have the
usual mode `644` (`NOT indexed`). Run:

    r=$(env -u MANPATH man -k -- 'KEYWORD' 2>&1); echo "exit=$?"; printf '%s\n' "$r"; printf '%s\n' "$r" | awk -F ' - ' '/\([^)]*\) - / { printf "%s%s", (n++ ? "; " : "RESULT: "), $1 } END { if (n) print "" }'; [ -n "$(env -u MANPATH /usr/bin/manpath -q)" ] || echo "MANPATH-EMPTY"; for d in $(env -u MANPATH /usr/bin/manpath -q | tr ':' ' '); do [ -f "$d/mandoc.db" ] && [ "$(stat -f %Lp "$d/mandoc.db")" = 644 ] || echo "NOT indexed $d"; done

Expected, such as:

    exit=0
    chmod(1) - change file modes
    chmod, fchmod, fchmodat, lchmod(2) - change mode of file
    RESULT: chmod(1); chmod, fchmod, fchmodat, lchmod(2)

Go through these rows in order and use the first that matches:

| If you see | Do this |
|---|---|
| `MANPATH-EMPTY` | no manual-page folders were found. Stop, and report the full output |
| a `NOT indexed` line, and you have not done step 3 yet | a folder has no search database, so its pages were not searched. Go to step 3 |
| any line that is none of: `NAME(SECTION) - description`, `RESULT: ...`, `exit=...`, `apropos: nothing appropriate`, `NOT indexed ...` (such as `apropos: /usr/local/share/man/mandoc.db: ...`) | a folder's database could not be read. Stop, and report the full output |
| `exit=0`, one or more lines of the form `NAME(SECTION) - description`, then a `RESULT:` line (and, after step 3, possibly `NOT indexed` lines) | go to step 4 |
| `exit=5` and `apropos: nothing appropriate` (and no `RESULT:` line) | nothing was found. If you have not done step 3 yet, go to step 3: the search database of one of the manual-page folders may be missing. If you have, go to step 4: nothing matches `KEYWORD` |
| anything else | stop, and report the full output |

## Step 3: Build the search databases

Each folder of manual pages (`manpath -q` lists them: the base system's, the
packages' in `/usr/local/share/man`, and others) has its own database. This
builds all of them, as the weekly job does; it is harmless when they exist
already. `umask 022` makes the new databases readable by every user; a database
with another mode is shown as `NOT indexed`. Run:

    umask 022; /usr/libexec/makewhatis.local "$(env -u MANPATH /usr/bin/manpath -q)"; echo "exit=$?"; for d in $(env -u MANPATH /usr/bin/manpath -q | tr ':' ' '); do if [ -f "$d/mandoc.db" ] && [ "$(stat -f %Lp "$d/mandoc.db")" = 644 ]; then echo "indexed $d"; else echo "NOT indexed $d"; fi; done

Expected: `exit=0`, then one `indexed` line for each folder, such as:

    exit=0
    indexed /usr/share/man
    indexed /usr/local/share/man
    indexed /usr/share/openssl/man

Then go back to step 2 (once). A `NOT indexed` line for another folder means
that folder's pages cannot be searched (for example a folder on a network
file system), or that the folder holds no pages at all (no database is made
for an empty folder); write it down for step 4. No
`indexed /usr/share/man` line (the base system's own pages), anything else,
or no `exit=0`: stop, report the output, and end with FAILED.

## Step 4: Report

Report the pages found, by copying the `RESULT:` line from step 2 exactly as
it was printed, on a line of its own. Write `RESULT:` on that one line only;
anywhere else, call it "the result line". If nothing was found even after step 3,
report that nothing matches `KEYWORD` in the folders that were searched. In
both cases, name any folder still shown as `NOT indexed` in step 2: its pages
were not searched (or, for a folder that holds no pages, there was nothing to
search). A page is read with `man SECTION NAME` (such as `man 5 crontab`);
the section number picks between pages of the same name.

## Undo

None needed. (The databases built in step 3 can stay: the weekly job keeps
it up to date.)

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-28, snapshot 20260921 (a6deeaa2fb3b) | No database on a new system. |
| 15.1-RELEASE | verified | 2026-09-28 | No database on a new system; building it took about 3 seconds. |
| 15.0-RELEASE | verified | 2026-09-28 | No database on a new system. |
| 14.5-RELEASE | verified | 2026-09-28 | The database comes with the system. |
| 14.4-RELEASE | verified | 2026-09-28 | As 14.5. |
| 14.3-RELEASE (EoL) | verified | 2026-09-28 | As 14.5. |
| 14.2-RELEASE (EoL) | verified | 2026-09-28 | As 14.5. |
| 14.1-RELEASE (EoL) | verified | 2026-09-28 | As 14.5. |
| 14.0-RELEASE (EoL) | verified | 2026-09-28 | As 14.5. |

## Weak-model check

2026-09-28 (UTC): claude-haiku-4-5, given only this skill, the input
`KEYWORD=crontab` (not the skill's example), and a tool that runs one command
on the test machine, followed it on a freshly reset system of every release
above, with the search database removed first so every release took the path
through step 3. A run counts only when the model said DONE AND its final message contained
the true `RESULT:` line (`answer.sh`: the two base pages `crontab(1)` and
`crontab(5)`, fixed in the test, which holds with no packages installed) AND the independent check (`verify.sh`:
every folder of manual pages has its database again, the base one owned by
root with mode `644`, and `man -k crontab` finds `crontab(1)` and
`crontab(5)`) passed: all 9 did, with this version of the skill and scripts.

## Not verified

- Seen on the test machines: 14.0 to 14.5 come with
  `/usr/share/man/mandoc.db`; 15.0, 15.1 and 16.0 do not, until `periodic
  weekly` (`320.whatis`, enabled by default) builds it.
- A database that exists but is older than packages installed since
  (packages do not update it; the weekly job does) counts as indexed, so
  those packages' pages may be missing from the result until the next
  weekly run, or until step 3 is run by hand.
- A folder of manual pages on a network file system (NFS) is skipped by
  `makewhatis.local`, so its pages are not found even after step 3; not
  tried.
- Manual pages of other languages (`manpath -qL`), which the weekly job also
  indexes, are not part of this skill.
- GNU `info`, which the Handbook mentions, is not in the base system of any
  release above (`which info` finds nothing), so it has no skill here.

## Differences from the Handbook

- The Handbook shows `man -k mail` and does not mention the database. On 15.0
  and later that finds nothing on a new system; the skill builds the
  database first when it is missing.

## Source

FreeBSD Handbook, "Manual Pages",
https://docs.freebsd.org/en/books/handbook/basics/#basics-more-information
