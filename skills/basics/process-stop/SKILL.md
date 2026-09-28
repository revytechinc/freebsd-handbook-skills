---
name: basics-process-stop
description: Stop one running program of an ordinary user, found by its name and owner - politely first (TERM), and by force (KILL) only if allowed - without touching other users' programs or the system's.
handbook: basics/#basics-processes
handbook_commit: bdf18a0458
---

# Stop a user's program

## What this does

Ends one running program (a *process*) that belongs to an ordinary user
account, such as a program that hangs. It first sends the signal `TERM`,
which asks the program to finish: it can save its work and close its files.
Only if it is still running after that, and only if allowed, it sends `KILL`,
which ends it at once (unsaved work is lost).

The program is found by its name and its owner. Its process number (PID) is
written down, and each signal is sent only if, at that moment, that same
number is still the one and only program of that name and owner. That makes
hitting a second program of the same name, or a number reused by another
program, very unlikely. Programs in jails are left out (`-j none`), and a program only counts as
the user's if both its real and its effective user are `OWNER` (`-U`, `-u`). Programs of `root` and
of system accounts are refused: system services are stopped with `service`
instead.

## Before you start

- You need: a root shell.
- This changes: ends one program. Programs it started itself (its child
  processes) are not stopped and may keep running.
- Time: about 20 seconds.
- Risk: medium: whatever the program had not saved is lost, and it does not
  come back by itself. There is no Undo; its user has to start it again.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `NAME` | the program's name as the system knows it: the name `ps -o comm= -U OWNER` or `pgrep -l -u OWNER .` shows (not a path, and not a title the program gives itself) | `vim` |
| `OWNER` | the login name of the user it belongs to | `jru` |
| `FORCE` | `yes` to allow `KILL` if `TERM` did not end it, `no` otherwise | `no` |

Everywhere below, replace `NAME`, `OWNER` and `FORCE` with these values,
exactly as given. Check them first:

- `NAME`: 1 to 19 characters; starts with a letter or digit; only letters,
  digits and the characters `_` `-` after that. (A name with a `.` in it,
  such as `python3.11`, is not supported: `pgrep` would read the `.` as
  "any character".)
- `OWNER`: 1 to 16 characters; starts with a lower-case letter; only
  lower-case letters `a`-`z`, digits and `_` after that.
- `FORCE`: exactly `yes` or exactly `no`.

If any of them does not, stop and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24) | go to step 2. The steps are the same on every release |
| anything else | stop, and report the line: this skill was not tested there |

## Step 2: Check the owner and find the program

`pgrep -x` matches the whole name. Normally it never lists itself or the
programs it was started from (the login session running these commands);
the second `pgrep`, with `-a`, lists those too, so the two can be compared.
Run:

    u=$(pw usershow OWNER) && echo "user ok"; printf '%s\n' "$u" | awk -F: '{print "uid=" $3}'; pgrep -l -x -j none -u OWNER -U OWNER -- NAME; echo "pgrep=$?"; pgrep -a -x -j none -u OWNER -U OWNER -- NAME; echo "all=$?"

| If you see | Do this |
|---|---|
| `user ok`, `uid=` a number from 1000 to 60000, then exactly one line of a number and `NAME` (such as `2961 hbworker`), then `pgrep=0`, then that same number alone, then `all=0` | write down the number (only digits): it is the program's PID (PID below). Go to step 3 |
| `uid=` any other number (such as `0` for root) | a system account. Stop, and report it: this skill does not stop the system's programs (a service is stopped with `service` instead) |
| `pw: no such user` and no `user ok` | there is no such account. Stop, and report it |
| `user ok`, a `uid=` from 1000 to 60000, `pgrep=1`, then a number and `all=0` | that program is one this login session was itself started from. Stop, and report it: it has to be stopped from another login |
| `user ok`, a `uid=` from 1000 to 60000, `pgrep=1`, then only `all=1` | that user has no program of that name running. Stop, and report it: nothing needs doing |
| two or more lines of a number and `NAME` | that user runs several programs of that name. Stop, and report them all: this skill stops exactly one |
| anything else | stop, and report the full output |

## Step 3: Ask it to finish (TERM)

The command checks, at that moment, that `OWNER` is an ordinary account
(UID 1000 to 60000) and that PID is still the one and only program called
`NAME` of `OWNER`; only then it prints `guard ok` and sends `TERM`. The
signal is sent as `OWNER` (with `su`), not as root, so the system refuses it
if the number belongs by then to a program `OWNER` may not signal (such as
another user's or root's). Run:

    if id=$(id -u OWNER) && [ "$id" -ge 1000 ] && [ "$id" -le 60000 ]; then p=$(pgrep -x -j none -u OWNER -U OWNER -- NAME); r=$?; if [ $r = 0 ] && [ "$p" = "PID" ]; then echo "guard ok"; env -i PATH=/bin:/usr/bin su -m OWNER -c '/bin/kill -s TERM PID'; echo "exit=$?"; else echo "guard: not that program (pgrep=$r)"; fi; else echo "guard: account"; fi

| If you see | Do this |
|---|---|
| `guard ok`, then `exit=0` | `TERM` was sent. Write down: **TERM sent**. Go to step 4 |
| `guard ok`, then `Operation not permitted` and `exit=1` | the number belonged to another user's program at that moment. Nothing was sent. Stop, and report it |
| `guard: not that program (pgrep=1)` or `(pgrep=0)` | the program is no longer exactly the one found in step 2 (it ended, or another of that name started). Nothing was sent. Go to step 6 |
| `guard ok`, then `No such process` and `exit=1` | it ended just before the signal. Go to step 6 |
| `guard: not that program` with another `pgrep=` number | `pgrep` itself failed. Nothing was sent. Stop, and report the output |
| `guard: account` | `OWNER` does not exist, or is not an ordinary account. Nothing was sent. Stop, and report it |
| anything else | stop, report the output, and end with FAILED |

## Step 4: Wait, and look again

Run:

    sleep 10; pgrep -x -j none -u OWNER -U OWNER -- NAME; echo "pgrep=$?"; ps -o state= -p PID

| If you see | Do this |
|---|---|
| only `pgrep=1` (no state line after it) | it has ended. Go to step 6 |
| `pgrep=1`, then a state line | PID still exists but is no longer `OWNER`'s `NAME` (it changed its name, or the number was reused). Stop, and report the output of `ps -o user= -o comm= -p PID` |
| exactly PID on a line by itself, then `pgrep=0`, then a state starting with `Z` | it has ended; it only waits to be cleared away by the system. Go to step 6 |
| exactly PID on a line by itself, then `pgrep=0`, then a state not starting with `Z` (such as `S` or `Ss`) | it is still there 10 seconds after `TERM`: it ignores `TERM`, or is still finishing its work. If `FORCE` is `yes`, go to step 5. If `FORCE` is `no`, stop, and report that it is still running and would need `KILL` |
| any other number (alone or together with PID), then `pgrep=0` | another program of that name is running now. Stop, and report it: do not signal it |
| anything else | stop, and report the full output |

## Step 5: End it at once (KILL; only if FORCE is yes)

The command itself also checks `FORCE`, the account, and that PID is still
the one and only such program. Run:

    if [ "FORCE" = yes ]; then if id=$(id -u OWNER) && [ "$id" -ge 1000 ] && [ "$id" -le 60000 ]; then p=$(pgrep -x -j none -u OWNER -U OWNER -- NAME); r=$?; if [ $r = 0 ] && [ "$p" = "PID" ]; then echo "guard ok"; env -i PATH=/bin:/usr/bin su -m OWNER -c '/bin/kill -s KILL PID'; echo "exit=$?"; else echo "guard: not that program (pgrep=$r)"; fi; else echo "guard: account"; fi; else echo "force=no"; fi

| If you see | Do this |
|---|---|
| `force=no` | `FORCE` is not `yes`: nothing was sent. Stop, and report that it is still running and would need `KILL` |
| `guard ok`, then `exit=0` | `KILL` was sent. Write down: **KILL sent**. Go to step 6 |
| `guard ok`, then `Operation not permitted` and `exit=1` | the number belonged to another user's program at that moment. Nothing was sent. Stop, and report it |
| `guard: not that program (pgrep=1)` or `(pgrep=0)` | nothing was sent (it ended in the meantime, or it is no longer exactly that program). Go to step 6 |
| `guard ok`, then `No such process` and `exit=1` | it ended just before the signal. Go to step 6 |
| `guard: not that program` with another `pgrep=` number | `pgrep` itself failed. Nothing was sent. Stop, and report the output |
| `guard: account` | `OWNER` does not exist, or is not an ordinary account. Nothing was sent. Stop, and report it |
| anything else | stop, report the output, and end with FAILED |

## Step 6: Verify

Run:

    sleep 1; pgrep -x -j none -u OWNER -U OWNER -- NAME; echo "pgrep=$?"; ps -o state= -p PID

| If you see | Do this |
|---|---|
| only `pgrep=1` (no state line after it) | it has ended. Go on below |
| `pgrep=1`, then a state line | PID still exists but is no longer `OWNER`'s `NAME`. Stop, report the output of `ps -o user= -o comm= -p PID`, and end with FAILED |
| exactly PID on a line by itself, `pgrep=0`, then a state starting with `Z` | it has ended (it only waits to be cleared away). Go on below |
| anything else | stop, report the output, and end with FAILED |

Report that the program was stopped, and what was sent (**TERM sent**, and
**KILL sent** if written down). If neither was written down, report that it
ended by itself before any signal.

## Undo

None: a stopped program cannot be brought back. Its user can start it again.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-28, snapshot 20260921 (a6deeaa2fb3b) |  |
| 15.1-RELEASE | verified | 2026-09-28 | Also tried by hand on ZFS (see below). |
| 15.0-RELEASE | verified | 2026-09-28 |  |
| 14.5-RELEASE | verified | 2026-09-28 |  |
| 14.4-RELEASE | verified | 2026-09-28 |  |
| 14.3-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.2-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.1-RELEASE (EoL) | verified | 2026-09-28 |  |
| 14.0-RELEASE (EoL) | verified | 2026-09-28 |  |

## Weak-model check

2026-09-28 (UTC): claude-haiku-4-5, given only this skill, the inputs
`NAME=hbworker`, `OWNER=hbtest7`, `FORCE=yes` (not the skill's example), and a
tool that runs one command on the test machine, followed it on a freshly
reset system of every release above (UFS). Two accounts each ran a program
called `hbworker` that ignores `TERM`, so the whole path including `KILL` was
needed. A run counts only when the model said DONE AND the independent check
(`verify.sh`: `hbtest7`'s `hbworker` is gone; the other account's `hbworker`
still runs with the same PID; `init`, `sshd`, `cron` and `syslogd` still run)
passed: all 9 did, with this version of the skill and scripts. The command
logs show exactly the skill's commands on every release.

## Not verified

- Tried by hand on 15.1 (ZFS): `pgrep -x -u` found only the given user's
  program, not the other account's program of the same name; `TERM` left
  the program that ignores it running, and `KILL` ended it; `pgrep -x sshd`
  and `pgrep -x init` found nothing when run over ssh, because `pgrep` leaves
  out its own ancestors.
- A program that ends on `TERM` (the usual case), and `FORCE=no`, were not
  tried by the model: they take the step 4 "only `pgrep=1`" row and the
  step 4 stop.
- Tried by hand on 16.0 (ZFS) with root's login shell set to `tcsh` (the
  default before 14.0): `su -m` then runs `tcsh`, and `/bin/kill -s TERM`
  with the number in the text works, while `kill ... "$1"` with the number
  passed separately fails, which is why the skill uses the former. The
  number is safe to put in the text: the check before it only passes when
  it equals `pgrep`'s output, which is digits only.
- Tried by hand on 16.0 and 14.0 (ZFS): `kill` run as the owner with
  `su -m` works for the owner's program (also with the shell
  `/usr/sbin/nologin`) and gives `Operation not permitted` for PID 1;
  `pgrep` also lists a finished program that is waiting to be cleared away
  (state `Z`), which is why steps 4 and 6 show the state.
- Tried by hand on 16.0 (ZFS): step 2's two `pgrep` commands run from
  inside the user's program show `pgrep=1`, then its number and `all=0`
  (the "started from" row); `-j none` and `-a` work on 16.0 and 14.0.
- Tried by hand on 16.0 (ZFS): the step 3 command with `root` as `OWNER`
  gives `guard: account`; with a wrong PID, or with a second program of the
  same name running, it gives `guard: not that program (pgrep=0)`; nothing is
  sent. `kill` given a number with no program gives `No such process`.
- Programs that are stuck waiting for a disk or network (state `D` in `ps`)
  may not end even on `KILL` until the wait times out.

## Differences from the Handbook

- The Handbook explains signals and `kill` with a PID. The skill finds the
  PID by name and owner, re-checks in the same command before each signal
  that it is still the one and only such program and that the account is an
  ordinary one,
  sends `TERM` first and `KILL` only when allowed, and refuses root's and system accounts'
  programs (the Handbook warns never to kill random processes, and PID 1
  above all).
- The Handbook's `SIGHUP` example (telling a daemon to re-read its
  configuration) belongs to the services the skill refuses; it is left to
  the chapters on those services.

## Source

FreeBSD Handbook, "Processes and Daemons" and "Killing Processes",
https://docs.freebsd.org/en/books/handbook/basics/#basics-processes
