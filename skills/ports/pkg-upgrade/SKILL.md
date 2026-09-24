---
name: ports-pkg-upgrade
description: Upgrade every installed package, and on 15.x and later the base system itself, after first taking a ZFS boot environment snapshot to roll back to; restart if the kernel was upgraded.
handbook: ports/#pkgng-upgrading
handbook_commit: bdf18a0458
---

# Upgrade installed packages (with a snapshot first)

## What this does

Brings every installed package up to the newest version in the package
repository. On FreeBSD 15.0 and later the base system (the kernel and the core
programs) is itself installed as packages, so this also installs base-system
updates, including security fixes. Before changing anything, on a ZFS system,
the skill saves a **boot environment**: a snapshot of the whole system that
you can start again if the upgrade causes trouble. If the kernel was upgraded,
the skill restarts the machine at the end.

## Before you start

- You need: a root shell, network access to `pkg.FreeBSD.org`, and pkg itself
  installed (skill `ports/pkg-bootstrap`).
- This changes: upgrades packages; on 15.x and later, the base system too.
  Creates the boot environment `before-pkg-upgrade` (ZFS only). May restart
  the machine.
- Time: from one minute to about fifteen, depending on what is upgraded.
- Risk: medium. On ZFS it can be rolled back (see Undo). On UFS it cannot.

## Inputs

None.

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line such as `14.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`,
sometimes with `-p<number>` added.

| The line starts with | Your release group | Use in steps 4 to 6 |
|---|---|---|
| `14.0-`, `14.1-`, `14.2-` or `14.3-` | EoL | the command marked **EoL** |
| anything else (`14.4-`, `14.5-`, `15.`, `16.`) | current | the command marked **current** |

## Step 2: Find out the file system

Run:

    df -T /

Expected: two lines. Look at the `Type` column of the second line:

| Type | Do this |
|---|---|
| `zfs` | go to step 3 |
| `ufs` | this system cannot take a boot environment, so the upgrade cannot be rolled back. Say so in your final answer, and go to step 4 |
| anything else | stop, and report the output |

## Step 3: Take the snapshot (boot environment)

Run:

    bectl create before-pkg-upgrade; echo "exit=$?"

| If you see | Do this |
|---|---|
| only `exit=0` | go to step 4 |
| `boot environment name already taken` | a snapshot from an earlier upgrade exists. Stop, and report it: do not upgrade without a fresh snapshot |
| anything else | stop, and report the full output |

## Step 4: See what would be upgraded

Run the command for your release group. `-n` only shows the plan; nothing is
changed:

- **current**: `pkg upgrade -n; echo "exit=$?"`
- **EoL**: `env IGNORE_OSVERSION=yes pkg upgrade -n; echo "exit=$?"`

| If you see | Do this |
|---|---|
| `Your packages are up to date.` and `exit=0` | nothing to upgrade. Go to step 7 |
| `Installed packages to be UPGRADED:` with a list, and `exit=0` | go to step 5 |
| `New version of pkg detected; it needs to be installed first.` and `exit=0` | pkg will update itself first. Go to step 5 |
| `wrong OS version` | you used the **current** command on an EoL release. Run the **EoL** command |
| anything else | stop, and report the full output |

Lines such as `FreeBSD-kernel-generic: 15.1 -> 15.1p3 [FreeBSD-base]` are
base-system updates. That is expected on 15.x and later.

## Step 5: Upgrade

Run the command for your release group. `-y` answers "yes" to the question
automatically:

- **current**: `pkg upgrade -y; echo "exit=$?"`
- **EoL**: `env IGNORE_OSVERSION=yes pkg upgrade -y; echo "exit=$?"`

Expected: lines such as `[2/2] Upgrading nginx-lite from 1.30.4,3 to
1.30.5,3...`, possibly many of them, and last `exit=0`. If pkg updates itself
first, it continues with the rest in the same command.

| If you see | Do this |
|---|---|
| `exit=0` on the last line | go to step 6 |
| `exit=` followed by anything else | stop, and report the full output. On ZFS, the snapshot from step 3 is still there (see Undo) |

## Step 6: Check that nothing is left

Run the same command as in step 4 again (**current** or **EoL**).

| If you see | Do this |
|---|---|
| `Your packages are up to date.` and `exit=0` | go to step 7 |
| a list of packages to upgrade, or `New version of pkg detected` | run step 5 once more, then this step again. If a list is still shown, stop and report it |
| anything else | stop, and report the full output |

## Step 7: Restart if the kernel was upgraded

Run this line exactly as written. It compares when the kernel packages were
installed with when the machine last started:

    k=$(pkg query -g %t 'FreeBSD-kernel*' 2>/dev/null | sort -n | tail -1); b=$(sysctl -n kern.boottime | sed 's/^{ sec = \([0-9]*\),.*/\1/'); case "$b" in ''|*[!0-9]*) echo "CANNOT TELL" ;; *) if [ -z "$k" ]; then echo "NO KERNEL PACKAGE"; elif [ "$k" -gt "$b" ]; then echo "REBOOT NEEDED"; else echo "NO REBOOT NEEDED"; fi ;; esac

| If you see | Do this |
|---|---|
| `NO REBOOT NEEDED` | the task is finished |
| `NO KERNEL PACKAGE`, on 14.x | normal: on 14.x the kernel is not a package, so this skill never changes it. The task is finished |
| `NO KERNEL PACKAGE`, on 15.x or 16.0-CURRENT | unexpected. Stop, and report it |
| `CANNOT TELL` | stop, and report it |
| `REBOOT NEEDED` | run `shutdown -r +1; echo "exit=$?"`. Expected: `Shutdown at <date and time>.` and `exit=0`. The machine restarts one minute later, running the new kernel. Do not run any more commands. The task is finished; say in your final answer that the machine is restarting |

## Undo

On ZFS only, if the upgraded system has problems: make the snapshot from step 3
the one that starts next, then restart.

    bectl activate before-pkg-upgrade; echo "exit=$?"
    shutdown -r now

Expected: `Successfully activated boot environment before-pkg-upgrade` and
`exit=0`, then the machine restarts. After the restart, `bectl list` shows
`NR` (active now, and on reboot) next to `before-pkg-upgrade`, and
`freebsd-version -kru` shows the versions from before the upgrade. The upgraded
system is kept as the boot environment `default`.

On UFS there is no snapshot, so there is no Undo.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-09-24, snapshot 20260921 (a6deeaa2fb3b) | ZFS and UFS. 69 base packages to a newer snapshot; restart needed. `freebsd-version` still says `16.0-CURRENT` after the upgrade; `uname -v` shows the new build. |
| 15.1-RELEASE | verified | 2026-09-24 | ZFS and UFS. pkg updates itself first (2.7.5 to 2.8.4 on Latest), then 80 base packages to 15.1-p3; restart needed. |
| 15.0-RELEASE | verified | 2026-09-24 | ZFS and UFS. 150 base packages to 15.0-p13; restart needed. |
| 14.5-RELEASE | verified | 2026-09-24 | ZFS and UFS. Only added software (nginx-lite, pcre2); the kernel is not a package, so no restart. |
| 14.4-RELEASE | verified | 2026-09-24 | As 14.5. |
| 14.3-RELEASE (EoL) | verified | 2026-09-24 | As 14.5, with the **EoL** commands. |
| 14.2-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-09-24 | As 14.3. Without `IGNORE_OSVERSION`, `pkg upgrade -n` stops with `wrong OS version`, exit status 3. |

## Weak-model check

2026-09-24 (UTC): claude-haiku-4-5, given only this skill and a tool that runs
one command on the test machine, followed it on a freshly reset system of
every release above, twice per release: once with a ZFS root and once with a
UFS root, 18 runs in all. Before each run, nginx-lite was installed from the
Quarterly branch and the machine was switched to Latest (as
`ports/pkg-branch-latest` does), so a real upgrade was waiting; on 15.0, 15.1
and 16.0-CURRENT base-system updates were waiting too. A run counts only when
the model said DONE AND the independent check (`verify.sh`: nothing left to
upgrade, the upgraded kernel running if the kernel was upgraded, and on ZFS
the boot environment present) passed, after waiting for any restart the model
scheduled: all 18 did. A manual review of the command logs showed only the
skill's commands: the boot environment taken on every ZFS system and skipped on
every UFS system, the **EoL** commands on 14.0 to 14.3 only, step 7 printing
`NO KERNEL PACKAGE` on every 14.x system and `REBOOT NEEDED` on 15.0, 15.1
and 16.0-CURRENT, and a restart scheduled there and nowhere else.
`verify.sh` also checks that a package really was installed after the test
was set up, that on ZFS the boot environment is older than the upgrade, and on
15.x and later that a waiting kernel upgrade was really installed and that
`FreeBSD-base` is still enabled. The runs on 15.0, 15.1 and 16.0-CURRENT (both
file systems), 14.0 (ZFS) and 14.5 (UFS) used the final `setup.sh` and
`verify.sh`; the other 14.x runs used the version just before, whose checks are
the same on 14.x.

Undo (roll back to `before-pkg-upgrade`) was run by hand on ZFS systems of
15.0, 15.1 and 16.0-CURRENT, not by the weak model: after the restart,
`freebsd-version -kru` and `uname -v` showed the versions from before the
upgrade, and a package installed after the snapshot was gone.

## Not verified

- A failed upgrade (step 5 not ending in `exit=0`) was not provoked.
- Step 7 compares the kernel packages' install time with the time the machine
  started, so it assumes the clock was not changed in between. The test
  machines had no time server to step the clock; a clock change during the
  upgrade was not tried.

## Differences from the Handbook

- The Handbook's section is one command, `pkg upgrade`, and does not mention
  the base system. On 15.x and later `pkg upgrade` also upgrades the base
  system, kernel included (80 to 150 base packages in these tests), and the
  new kernel only runs after a restart. This skill adds the snapshot before
  and the restart after.
- On 14.0 to 14.3 `pkg upgrade` needs `IGNORE_OSVERSION=yes`; without it,
  it stops with `repository FreeBSD contains packages for wrong OS version`.

## Source

FreeBSD Handbook, "Upgrading Installed Packages",
https://docs.freebsd.org/en/books/handbook/ports/#pkgng-upgrading
