---
name: ports-pkg-branch-latest
description: Switch pkg from the Quarterly package branch to the Latest branch, without disabling any other repository.
handbook: ports/#quarterly-latest-branch
handbook_commit: bdf18a0458
---

# Switch packages from the Quarterly branch to the Latest branch

## What this does

FreeBSD builds its packages on two branches. **Quarterly** changes little
during each three-month period: mostly security and bug fixes. **Latest** has
the newest versions of everything. Most releases use Quarterly by default. This
skill switches the machine's package repository to Latest by adding one small
file, and leaves every other repository setting, including updates to the base
system, as it was.

## Before you start

- You need: a root shell, network access to `pkg.FreeBSD.org`, and pkg itself
  installed (skill `ports/pkg-bootstrap`).
- This changes: creates the file `/usr/local/etc/pkg/repos/latest.conf`. Later
  installs and upgrades take packages from Latest.
- Time: about a minute.
- Risk: low. Undo removes the file. Packages already installed are not changed
  until the next upgrade.

## Inputs

None.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`,
sometimes with `-p<number>` added.

| The line starts with | Your release group | Do this |
|---|---|---|
| `14.0-`, `14.1-`, `14.2-` or `14.3-` | EoL 14 | go to step 2, then use the commands marked **14** and **EoL** |
| `14.4-` or `14.5-` | current 14 | go to step 2, then use the commands marked **14** and **current** |
| `15.` | 15 | go to step 2, then use the commands marked **15** and **current** |
| `16.` | 16 | 16.0-CURRENT already uses Latest. Skip to step 5 |

Why two kinds of command: on 14.x the package repository is named `FreeBSD`;
on 15.x and later it is named `FreeBSD-ports`. The file must use the right
name, or pkg ignores it.

## Step 2: Check that the file does not exist yet

Run:

    ls /usr/local/etc/pkg/repos/; echo "exit=$?"

| If you see | Do this |
|---|---|
| no `latest.conf` in the list (the list may be empty, may show `No such file or directory`, or may show `FreeBSD.conf`) | go to step 3 |
| `latest.conf` | the machine may already be switched. Skip to step 5 |

Do NOT change or remove `FreeBSD.conf` if it is there. On 15.x it holds the
line that turns on updates for the base system.

## Step 3: Add the file

Run exactly one of these, for your release group. Type it exactly, with the
single quotes: the `${ABI}` part must stay as it is.

- **14**: `mkdir -p /usr/local/etc/pkg/repos && echo 'FreeBSD: { url: "pkg+https://pkg.FreeBSD.org/${ABI}/latest" }' > /usr/local/etc/pkg/repos/latest.conf; echo "exit=$?"`
- **15**: `mkdir -p /usr/local/etc/pkg/repos && echo 'FreeBSD-ports: { url: "pkg+https://pkg.FreeBSD.org/${ABI}/latest" }' > /usr/local/etc/pkg/repos/latest.conf; echo "exit=$?"`

Expected: `exit=0`. Anything else: stop and report the output.

## Step 4: Download the Latest catalogue

Run the command for your release group:

- **current**: `pkg update -f; echo "exit=$?"`
- **EoL**: `env IGNORE_OSVERSION=yes pkg update -f; echo "exit=$?"`

Expected: one `Updating ... repository catalogue...` and one `... update
completed. <number> packages processed.` for each repository, then `exit=0`.

| If you see | Do this |
|---|---|
| `exit=0` and no line with `Unable` or `Error` | go to step 5 |
| also `pkg: Repository ... has a wrong packagesite, need to re-create database` | normal when a Quarterly catalogue was downloaded before: pkg replaces it. Look at the other rows |
| on 14.0 to 14.3: `wrong OS version`, or `Unable to update repository FreeBSD` | you used the **current** command on an EoL release. Run the **EoL** command |
| on any other release: `Unable to update repository`, `Error updating repositories!`; or `exit=` with any other number | stop, and report the full output |

## Step 5: Verify

Run:

    pkg -vv | grep -E '^  [A-Za-z-]+:|url|enabled'; echo "exit=$?"

Expected: for each repository, a line with its name, a `url` line and an
`enabled` line, then `exit=0`. Check two things:

1. The package repository (`FreeBSD` on 14.x, `FreeBSD-ports` on 15.x and
   16.0-CURRENT) has a `url` that ends in `/latest"`.
2. If there is a repository named `FreeBSD-base`, its `enabled` line says
   `yes,`.

Example, 15.1:

    FreeBSD-ports: {
      url             : "pkg+https://pkg.FreeBSD.org/FreeBSD:15:amd64/latest",
      enabled         : yes,
    FreeBSD-ports-kmods: {
      url             : "pkg+https://pkg.FreeBSD.org/FreeBSD:15:amd64/kmods_quarterly_1",
      enabled         : yes,
    FreeBSD-base: {
      url             : "pkg+https://pkg.FreeBSD.org/FreeBSD:15:amd64/base_release_1",
      enabled         : yes,
    exit=0

If both are true, the task succeeded. Otherwise stop and report the output.

## Undo

Only if step 3 created the file. Remove it, then download the Quarterly
catalogue again (use the **EoL** form on 14.0 to 14.3, as in step 4):

    rm /usr/local/etc/pkg/repos/latest.conf; echo "exit=$?"
    pkg update -f; echo "exit=$?"

Expected: `exit=0` twice. Packages installed from Latest stay installed; they
are replaced by Quarterly versions only when those become newer.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified (no-op) | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | Already uses Latest (`FreeBSD-ports`, `FreeBSD-ports-kmods` and `FreeBSD-base` all on latest branches); the skill skips to step 5. |
| 15.1-RELEASE | verified | 2026-09-24 | `FreeBSD-base` stays enabled. |
| 15.0-RELEASE | verified | 2026-09-24 | As 15.1. |
| 14.5-RELEASE | verified | 2026-09-24 | Repository name `FreeBSD`. |
| 14.4-RELEASE | verified | 2026-09-24 | As 14.5. |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | Needs the **EoL** `pkg update`. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. Without `IGNORE_OSVERSION`, `pkg update -f` ends with `Unable to update repository FreeBSD` and `Error updating repositories!`. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill and a tool that runs
one command on the test machine, followed it on a freshly reset system of
every release above (ZFS-root test machines; the skill does not depend on the
file system). A run counts only when the model said DONE AND the independent
check (`verify.sh`: the package repository uses Latest, and `FreeBSD-base`, if
present, is still enabled) passed: all 9 did, 16.0-CURRENT as a no-op. A
manual review of the command logs showed only the skill's commands, with the
right repository name for each release, the **EoL** command on 14.0 to 14.3,
and on 16.0-CURRENT a direct skip to step 5.

## Not verified

- Undo was run by hand (14.0 and 15.1), not by the weak model: both commands
  printed `exit=0` and the package repository was back on `quarterly`.
- The kernel-module repository (`FreeBSD-kmods` on 14.x, `FreeBSD-ports-kmods`
  on 15.x) stays on its Quarterly branch. This skill does not change it.

## Differences from the Handbook

The Handbook's command is

    echo 'FreeBSD-ports: { url: "pkg+https://pkg.FreeBSD.org/${ABI}/latest" }' > /usr/local/etc/pkg/repos/FreeBSD.conf

Run exactly as written, it did not work on any release tested (2026-09-24 UTC):

- **14.x**: the repository is named `FreeBSD`, not `FreeBSD-ports`. The
  command adds a third, broken repository: `pkg update -f` then prints
  `packagesite URL error ... pkg+:// implies SRV mirror type` and
  `Unable to update repository FreeBSD-ports`, and packages keep coming from
  Quarterly.
- **15.x and 16.0-CURRENT**: the installed system already has a file
  `/usr/local/etc/pkg/repos/FreeBSD.conf` containing
  `FreeBSD-base: { enabled: yes }`, which turns on updates for the base
  system. The `>` replaces that file, so base-system updates, including
  security fixes, silently stop (`FreeBSD-base` becomes `enabled: no`).

This skill writes a separate file, `latest.conf`, with the repository name
that matches the release.

## Source

FreeBSD Handbook, "Quarterly and Latest Ports Branches",
https://docs.freebsd.org/en/books/handbook/ports/#quarterly-latest-branch
