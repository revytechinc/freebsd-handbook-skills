---
name: ports-pkg-autoremove
description: Remove the packages that were installed only as dependencies and that nothing needs any more, after checking the list.
handbook: ports/#pkgng-autoremove
handbook_commit: bdf18a0458
---

# Remove packages that are no longer needed

## What this does

When you install a package, pkg also installs the packages it needs (its
dependencies) and marks them as installed "automatically". Removing the
package leaves those dependencies behind. This skill finds the automatically
installed packages that nothing needs any more and removes them, after
showing the list.

## Before you start

- You need: a root shell, and pkg itself installed (skill `ports/pkg-bootstrap`).
- This changes: removes the unneeded dependency packages and their files.
- Time: seconds.
- Risk: low. The removed packages were not needed by anything installed.
  Undo reinstalls them if you want them back.

## Inputs

None.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`.
The commands below are the same on every release.

## Step 2: See what would be removed

Run. `-n` only shows the plan; nothing is removed:

    pkg autoremove -n; echo "exit=$?"

| If you see | Do this |
|---|---|
| `Nothing to do.` and `exit=0` | nothing to remove. The task is finished |
| `Installed packages to be REMOVED:`, a list, and `exit=1` | `exit=1` here only means "there is something to remove". Write the list down, and go to step 3 |
| anything else | stop, and report the full output |

Example with something to remove:

    Checking integrity... done (0 conflicting)
    Deinstallation has been requested for the following 1 packages:

    Installed packages to be REMOVED:
            pcre2: 10.47_1

    Number of packages to be removed: 1
    ...
    exit=1

## Step 3: Check the list

Look at every name under `Installed packages to be REMOVED:`.

| If | Do this |
|---|---|
| no name starts with `FreeBSD-` and none is `pkg` | go to step 4 |
| any name starts with `FreeBSD-`, or is `pkg` | that is part of the base system or the package manager. Do NOT go on. Stop, report the list, and end with FAILED |

## Step 4: Remove them

Run. `-y` answers "yes" to the question automatically:

    pkg autoremove -y; echo "exit=$?"

Expected: the same list as in step 2, lines such as
`[1/1] Deinstalling pcre2-10.47_1...`, and last `exit=0`. If the last line is
not `exit=0`, stop and report the output.

## Step 5: Verify

Run the same command as in step 2 again:

    pkg autoremove -n; echo "exit=$?"

Expected: `Nothing to do.` and `exit=0`. If a list is still shown, stop and
report it.

## Undo

Reinstall a removed package with the skill `ports/pkg-install`, using the
names written down in step 2. A package reinstalled that way is marked as
installed on purpose, not automatically.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | 515 base-system packages, none removed. |
| 15.1-RELEASE | verified | 2026-09-24 | 499 base-system packages, none removed. |
| 15.0-RELEASE | verified | 2026-09-24 | 486 base-system packages, none removed. |
| 14.5-RELEASE | verified | 2026-09-24 | |
| 14.4-RELEASE | verified | 2026-09-24 | |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | No special setting needed. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill and a tool that runs
one command on the test machine, followed it on a freshly reset system of
every release above. Beforehand, curl was installed on purpose and nginx-lite
was installed and then removed, leaving its dependency pcre2 unneeded. A run
counts only when the model said DONE AND the independent check (`verify.sh`:
pcre2 gone, curl still installed and working, the number of base-system
packages unchanged, nothing unneeded left) passed: all 9 did. A manual review
of the command logs showed exactly the skill's four commands on every
release.

## Not verified

- Step 3's stop row was never needed: in every test the list held only
  ordinary dependency packages. On 15.x and 16.0-CURRENT the base-system
  packages (`FreeBSD-...`, about 500) are marked as installed automatically,
  but `pkg autoremove` did not select any of them; their count was the same
  before and after on every run by hand (14.0, 14.5, 15.1, 16.0-CURRENT).

## Differences from the Handbook

- The Handbook runs `pkg autoremove` and answers its question by hand. Without
  a terminal that is not possible, so this skill previews with `-n` and then
  uses `-y`.
- `pkg autoremove -n` exits with status 1 when there is something to remove,
  and 0 when there is nothing. The Handbook does not mention this; a script
  that treats status 1 as an error would stop at the wrong place.

## Source

FreeBSD Handbook, "Automatically Removing Unused Packages",
https://docs.freebsd.org/en/books/handbook/ports/#pkgng-autoremove
