---
name: ports-pkg-set-origin
description: After a port has moved to a new origin in the ports collection, record the new origin for the installed package and reinstall it.
handbook: ports/#pkgng-set
handbook_commit: bdf18a0458
---

# Change a package's recorded origin

## What this does

Every package records its **origin**, its place in the ports collection, such
as `lang/ruby31`. Sometimes a port moves to a new origin (for example
`lang/ruby31` to `lang/ruby32`). This skill changes the origin recorded for
the installed package from the old one to the new one, then reinstalls that
package from the repository.

## Before you start

- You need: a root shell, network access to `pkg.FreeBSD.org`, and pkg itself
  installed (skill `ports/pkg-bootstrap`).
- This changes: the origin recorded in pkg's database, then reinstalls the
  package (same files, from the repository).
- Time: under a minute.
- Risk: low. Undo sets the old origin back.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `OLD` | the origin recorded now | `lang/ruby31` |
| `NEW` | the origin the port has moved to | `lang/ruby32` |

Everywhere below, replace `OLD` and `NEW` with these values, exactly as given.
Each must be one word, a `/`, and another word (like `lang/ruby32`); each word
must start with a letter, and may contain only letters, digits, and the
characters `.` `_` `+` `-`; there must be exactly one `/`. If either does not, stop and report: do not run any command
with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.

| The line starts with | Your release group | Use in step 3 |
|---|---|---|
| `14.0-`, `14.1-`, `14.2-` or `14.3-` | EoL | the command marked **EoL** |
| anything else | current | the command marked **current** |

## Step 2: Find the package that has the old origin

Run:

    pkg query '%n %o' OLD; echo "exit=$?"

| If you see | Do this |
|---|---|
| one line: a package name, a space, `OLD`; then `exit=0` | write the package name down. Go to step 3 |
| only `exit=1` | no installed package has the origin `OLD`. Stop, and report it. (Do not go on: step 4 would report success while changing nothing.) |
| anything else | stop, and report the full output |

## Step 3: Check that the repository has the new origin

Run the command for your release group:

- **current**: `pkg rquery '%n %v %o' NEW; echo "exit=$?"`
- **EoL**: `env IGNORE_OSVERSION=yes pkg rquery '%n %v %o' NEW; echo "exit=$?"`

| If you see | Do this |
|---|---|
| one line: the SAME package name you wrote down in step 2, a version and `NEW`; then `exit=0` | go to step 4 |
| one line with a different package name | the port was renamed, not only moved; this skill does not handle that. Stop, and report it |
| only `exit=1` | the repository has nothing at `NEW`. Stop, and report it |
| anything else | stop, and report the full output |

## Step 4: Record the new origin

Run exactly this. The `-y` is required:

    pkg set -y -o OLD:NEW; echo "exit=$?"

Expected: only `exit=0`. Anything else: stop and report the output.

Do NOT leave out `-y`. Without a terminal, `pkg set -o OLD:NEW` prints its
question, cannot get an answer, and fails (`Package database is busy while
closing!`, exit status 1).

## Step 5: Reinstall the package from its new origin

Run:

    pkg install -y -Rf NEW; echo "exit=$?"

Expected: `Installed packages to be REINSTALLED:` with the package and a line
such as `[1/1] Reinstalling ...` (or, if the new origin has a newer version,
`Installed packages to be UPGRADED:` and `[1/1] Upgrading ...`), then
`exit=0`. Anything else: stop, report the output, and run the Undo below.

## Step 6: Verify

Run:

    pkg query '%n %o' NEW; echo "exit=$?"

Expected: exactly one line, the package name from step 2, a space, `NEW`; then
`exit=0`. If you see only `exit=1`, or more than one line, the task did not
succeed: stop and report.

## Undo

Record the old origin again:

    pkg set -y -o NEW:OLD; echo "exit=$?"

Expected: `exit=0`.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | |
| 15.1-RELEASE | verified | 2026-09-24 |  |
| 15.0-RELEASE | verified | 2026-09-24 |  |
| 14.5-RELEASE | verified | 2026-09-24 |  |
| 14.4-RELEASE | verified | 2026-09-24 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | Needs the **EoL** repository query in step 3. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill, the inputs
`OLD=devel/pcre2-old` and `NEW=devel/pcre2` (deliberately not the origins in
the skill's examples), and a tool that runs one command on the test machine,
followed it on a freshly reset system of every release above, with nginx-lite
installed and pcre2's recorded origin changed to `devel/pcre2-old`. A run
counts only when the model said DONE AND the independent check (`verify.sh`:
pcre2 records `devel/pcre2` again and was reinstalled during the run, and the
nginx program still starts) passed: all 9 did. A manual review of the command logs showed
exactly the skill's six commands on every release, with the **EoL** query on
14.0 to 14.3 only.

## Not verified

- No port had really moved on the test systems. The test recorded a made-up
  old origin for pcre2 (`devel/pcre2-old`, set with `pkg set -y -o`), and the
  task was to record its real origin `devel/pcre2` again.
- The moved origin in the test had the same version, so step 5 reinstalled.
  A move to a newer version (step 5 printing `UPGRADED`) was not tried.
- `verify.sh` checks the end state (origin, reinstall, program working). A
  forced reinstall by name alone would reach the same end state, so that the
  model really ran steps 2 to 4 rests on the manual review of the command
  logs.
- Undo (the same command with the origins swapped) was run by hand on 14.0,
  14.5, 15.1 and 16.0-CURRENT (exit status 0, origin changed), not by the
  weak model.

## Differences from the Handbook

- The Handbook's examples (`lang/python3`, `lang/ruby31`) are not installed on
  a fresh system. Run as written, `pkg set -o lang/ruby31:lang/ruby32` does
  nothing and still exits 0 when nothing has that origin; step 2 exists to
  catch that.
- The Handbook says `pkg install -Rf NEW` reinstalls the packages that depend
  on the moved one. In the tests it reinstalled only the moved package itself
  (pcre2); nginx-lite, which depends on it, was not reinstalled
  (14.0, 14.5, 15.1, 16.0-CURRENT).
- With current pkg, a wrong recorded origin did not stop `pkg upgrade` from
  treating the package as up to date: packages are matched by name. A forced
  reinstall by name (`pkg install -y -Rf pcre2`) also put the repository's
  origin back, without `pkg set`.

## Source

FreeBSD Handbook, "Modifying Package Metadata",
https://docs.freebsd.org/en/books/handbook/ports/#pkgng-set
