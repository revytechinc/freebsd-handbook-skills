---
name: ports-poudriere-bulk
description: Build packages for a list of ports with poudriere, in an existing jail and ports tree, into a package repository.
handbook: ports/#poudriere-initialization
handbook_commit: bdf18a0458
---

# Build packages with poudriere

## What this does

Writes the list of ports to build into a file, then has poudriere build
them, and everything they need, inside a jail. The result is a package
repository in `/usr/local/poudriere/data/packages/JAIL-TREE/`, laid out like
FreeBSD's own, which pkg can install from (skill `ports/poudriere-repo`).

## Before you start

- You need: a root shell, network access to FreeBSD's servers, a poudriere
  jail (skill `ports/poudriere-jail`) and a poudriere ports tree (skill
  `ports/poudriere-ports-tree`).
- This changes: creates `/usr/local/etc/poudriere.d/JAIL-TREE-pkglist` and
  the repository, and leaves build logs under
  `/usr/local/poudriere/data/logs/`.
- Time: minutes for small ports; hours for large ones. poudriere first
  builds `pkg` itself.
- Risk: low. Nothing is installed on this machine.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `JAIL` | the name of the jail | `builder` |
| `TREE` | the name of the ports tree | `local` |
| `PORTS` | one to five ports, each as category `/` name, separated by single spaces | `misc/figlet editors/nano` |

Everywhere below, replace `JAIL`, `TREE` and `PORTS` with these values,
exactly as given. Check them first:

- `JAIL` and `TREE`: 1 to 20 characters, letters `a`-`z`, `A`-`Z` and digits
  only.
- `PORTS`: one to five entries separated by single spaces. Each entry is one
  word, a `/`, and another word; each word starts with a letter or a digit,
  and may contain only letters, digits, and the characters `.` `_` `+` `-`.

If any of them does not, stop and report: do not run any command with it.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24) | go to step 2. The steps are the same on every release |
| anything else | stop, and report the line: this skill was not tested there |

On 14.0 to 14.3 the jail must have been made as `ports/poudriere-jail`
describes, with `ALLOW_UNSUPPORTED_SYSTEM=yes` in its `make.conf`; without it
every build fails `check-sanity`.

## Step 2: Check the jail and the ports tree

Run:

    poudriere jail -l && poudriere ports -l; echo "exit=$?"

| If you see | Do this |
|---|---|
| a `JAILNAME` header with a line starting with `JAIL` followed by a space, a `PORTSTREE` header with a line starting with `TREE` followed by a space, then `exit=0` | go to step 3 |
| no line for `JAIL`, or no line for `TREE` | stop, and report which is missing (see `ports/poudriere-jail`, `ports/poudriere-ports-tree`) |
| anything else | stop, and report the full output |

## Step 3: Check the ports exist in the tree

Run:

    for p in PORTS; do ls /usr/local/poudriere/ports/TREE/$p/Makefile; done

Expected: one line per port, each a path ending in `/Makefile`, such as
`/usr/local/poudriere/ports/local/misc/figlet/Makefile`.

| If you see | Do this |
|---|---|
| one path per port, and nothing else | go to step 4 |
| any line with `No such file or directory` | that port does not exist in the tree. Stop, and report it |
| anything else | stop, and report the full output |

## Step 4: Write the list of ports to build

`set -C` makes the shell refuse to overwrite a list that is already there.
Run:

    (set -C; printf '%s\n' PORTS > /usr/local/etc/poudriere.d/JAIL-TREE-pkglist); echo "exit=$?"; cat /usr/local/etc/poudriere.d/JAIL-TREE-pkglist

Expected: `exit=0`, then the ports, one per line.

| If you see | Do this |
|---|---|
| `exit=0`, then exactly the ports from `PORTS`, one per line | go to step 5 |
| `File exists` and `exit=1` | a list with that name already exists. Stop, and report it and its contents: this skill does not change it |
| anything else | stop, and report the full output |

## Step 5: Build

The output is long, so it goes into a file in root's home directory, and
only poudriere's summary is shown. Run:

    poudriere bulk -j JAIL -p TREE -f /usr/local/etc/poudriere.d/JAIL-TREE-pkglist > /root/poudriere-bulk.log 2>&1; echo "exit=$?"; grep -e 'Built ports:' -e 'Failed ports:' -e 'Skipped ports:' -e 'Ignored ports:' /root/poudriere-bulk.log; grep 'Queued:' /root/poudriere-bulk.log | tail -1

Expected, after minutes (or hours for big ports), such as:

    exit=0
    [00:03:24] Built ports: ports-mgmt/pkg print/indexinfo misc/figlet devel/gettext-runtime devel/gmake editors/nano
    [builder-local] [2026-09-26_07h43m20s] [committing] Queued: 6  Built: 6  Failed: 0  Skipped: 0  Ignored: 0  Fetched: 0  Tobuild: 0   Time: 00:03:20

The `Built ports:` line also names the ports that yours needed.

| If you see | Do this |
|---|---|
| `exit=0`, a `Built ports:` line naming every port in `PORTS`, and a last line with `Failed: 0  Skipped: 0  Ignored: 0` | go to step 6 |
| `exit=0`, no `Built ports:` line, and a last line with `Queued: 0` and `Failed: 0` | everything was already built. Go to step 6 |
| anything else, such as `Failed ports:`, or an exit other than 0 | stop: run `tail -20 /root/poudriere-bulk.log`, report both outputs, and end with FAILED. The build logs of each port are under the folder named on the `Logs:` line |

## Step 6: Verify

Run:

    ls /usr/local/poudriere/data/packages/JAIL-TREE/All/; echo "exit=$?"

Expected: a list of files ending in `.pkg`, including one for each port in
`PORTS` (the port's name, a `-`, and a version, such as
`figlet-2.2.5_1.pkg`), and one starting `pkg-`, then `exit=0`. If a port's
file is missing, stop and report the list.

## Undo

Remove the list, the log, and the repository (a plain folder, also on ZFS):

    rm /usr/local/etc/poudriere.d/JAIL-TREE-pkglist /root/poudriere-bulk.log; rm -rf /usr/local/poudriere/data/packages/JAIL-TREE; echo "exit=$?"

Expected: `exit=0`. The build logs under `/usr/local/poudriere/data/logs/`
stay.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-26, snapshot 20260921 (a6deeaa2fb3b) | UFS and ZFS. Ports tree `main`. |
| 15.1-RELEASE | verified | 2026-09-26 | UFS and ZFS. Two ports, six packages, about 3 minutes. Run again, it builds nothing (`Queued: 0`); a port that does not exist gives exit 1 (tried by hand). |
| 15.0-RELEASE | verified | 2026-09-26 | UFS and ZFS. |
| 14.5-RELEASE | verified | 2026-09-26 | UFS and ZFS. |
| 14.4-RELEASE | verified | 2026-09-26 | UFS and ZFS. |
| 14.3-RELEASE (EoL) | verified | 2026-09-26 | UFS and ZFS, in a jail with `ALLOW_UNSUPPORTED_SYSTEM=yes` in its `make.conf`. |
| 14.2-RELEASE (EoL) | verified | 2026-09-26 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-26 | As 14.3. About 6 minutes. |
| 14.0-RELEASE (EoL) | verified | 2026-09-26 | As 14.3. |

## Weak-model check

2026-09-26 (UTC): claude-haiku-4-5, given only this skill, the inputs
`JAIL=testjail`, `TREE=testtree`, `PORTS=sysutils/tree devel/gmake` (not the
skill's examples), and a tool that runs one command on the test machine,
followed it on a freshly reset system of every release above, once on a UFS
machine and once on a ZFS machine (18 runs). Beforehand the jail and the
ports tree were made as `ports/poudriere-jail` and
`ports/poudriere-ports-tree` make them. A run counts only when the model said
DONE AND the independent check (`verify.sh`: the list holds exactly the two
ports; the repository has its catalogue; and pkg, reading the built package
files themselves, finds packages built from `sysutils/tree`, `devel/gmake`
and `ports-mgmt/pkg`) passed: all 18 did, with the final text and scripts.
The command logs show exactly the skill's six commands on every run.

The host of the test machines went down during the first round; the runs it
interrupted were repeated. One ZFS 14.2 run was not counted although the
check passed and the model ended with DONE, because its summary said "no
failed ports", which the test harness treats as a possible failure; the run
was repeated and passed.

## Not verified

- Build options for the list (`poudriere options`) and sets (`-z`) from the
  Handbook were not tried; the ports are built with default options.
- `poudriere pkgclean -A -y` was tried as an undo on 15.1: it printed
  `Cleaned all packages` but the packages stayed, so the skill removes the
  folder instead.
- Only small ports; a port whose package name differs from its directory
  name (for example `py311-` packages) makes step 6's file harder to find.

## Differences from the Handbook

- The Handbook names the list `13amd64-local-workstation-pkglist` for a set
  called `workstation`. The skill uses no set, and names the list after the
  jail and tree.
- The Handbook runs `poudriere options` before building; the skill builds
  with default options.

## Source

FreeBSD Handbook, "Building Packages with poudriere",
https://docs.freebsd.org/en/books/handbook/ports/#poudriere-initialization
