---
name: x11-drm-kmod-install
description: Install the kernel graphics driver for Intel or AMD graphics (the drm-kmod package) and have it loaded at every boot, but only when the driver was built for the running kernel.
handbook: x11/#x-configuration-intel
handbook_commit: bdf18a0458
---

# Install the Intel or AMD graphics driver (drm-kmod)

## What this does

Installs the package `drm-kmod`, which brings the kernel modules that drive
Intel and AMD graphics processors, and adds the right module to `kld_list`
in `/etc/rc.conf`, so the system loads it at every boot. X.org (skill
`x11/xorg-install`) needs this driver to use the graphics hardware.

A kernel module must be built for the kernel it is loaded into; loading one
built for another FreeBSD version can crash the system (a "panic"). The
packages for the end-of-life releases 14.0 to 14.3 are built for 14.4. So
this skill first checks that the installed driver matches the running
kernel, and only then enables it. If it does not match, the driver stays
installed but not enabled, and it has to be built from the ports tree on
that machine instead.

## Before you start

- You need: a root shell, network access to `pkg.FreeBSD.org`, and pkg itself
  installed (skill `ports/pkg-bootstrap`).
- Find out which module your graphics processor needs (the `MODULE` input):
  run `pciconf -lv | grep -B3 display` and read the `vendor =` line:
  `Intel Corporation` needs `i915kms`; `Advanced Micro Devices, Inc. [AMD/ATI]`
  needs `amdgpu` (Radeon HD 7000 series and later) or `radeonkms` (older
  Radeon). No line, or another vendor: this skill does not apply.
- This changes: installs about 190 packages (the drivers and the firmware for
  many graphics processors) under `/usr/local` and `/boot/modules`, and
  changes `kld_list` in `/etc/rc.conf`.
- Time: under a minute with a fast connection.
- Risk: medium: a driver that does not suit the hardware can make the screen
  go blank at boot. See Undo.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `MODULE` | the kernel module for the graphics processor | `amdgpu` |

`MODULE` must be exactly one of `i915kms`, `amdgpu`, `radeonkms`. If it is
not, stop, report it, run no command, and end with FAILED. Everywhere below,
replace `MODULE` with this value.

## Step 1: Identify the release

The driver is loaded at the next boot, into the kernel installed on disk. If
that is not the kernel running now (an upgrade is waiting for a restart), the
check in step 3 would compare against the wrong kernel. The command prints
the installed release, then `SAME-KERNEL` if the running kernel's own
version line (with its build number and source revision) is found in the
kernel file it was started from, or `DIFFERENT-KERNEL` if not. Run:

    freebsd-version -u; v=$(sysctl -n kern.version | head -1); f=$(sysctl -n kern.bootfile); if [ -z "$v" ]; then echo NO-VERSION; elif [ ! -r "$f" ]; then echo "NO-KERNEL-FILE $f"; elif grep -q -F -- "$v" "$f"; then echo SAME-KERNEL; else echo DIFFERENT-KERNEL; fi

| If you see | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24), then `SAME-KERNEL` | go to step 2 |
| `DIFFERENT-KERNEL` | the kernel on disk is not the one running (a new kernel is waiting for a restart). Stop, report it, and end with FAILED: restart the machine first, then run this skill |
| `NO-VERSION` or `NO-KERNEL-FILE` | the check could not be made. Stop, report the output, and end with FAILED |
| anything else | stop, report the output, and end with FAILED: this skill was not tested there |

## Step 2: Install drm-kmod

First check whether a graphics driver package is already installed: either
`drm-kmod` itself or one of the packages holding the modules (`drm-` and a
number and `-kmod`, such as `drm-61-kmod`, which can also be built on this
machine from the ports tree). If one is, do not run `pkg install`: it might
replace a driver built for this kernel with a package built for another.
Run:

    if l=$(pkg query '%n'); then echo "$l" | grep -E '^drm(-kmod|-[0-9]+-kmod)$'; echo "found=$?"; else echo PKG-ERROR; fi

| If you see | Do this |
|---|---|
| one or more package names, then `found=0` | already installed: do not install, go to step 3 (Undo will not remove it) |
| only `found=1` | not installed: run the next command |
| `PKG-ERROR` | pkg could not list the installed packages. Stop, report the output, and end with FAILED |
| anything else | stop, report the output, and end with FAILED |

Only after `found=1`, run exactly this (`-y` answers pkg's question; without
it pkg installs nothing). The full output goes to `/root/drm-kmod-install.log`:

    pkg install -y drm-kmod > /root/drm-kmod-install.log 2>&1; echo "exit=$?"; pkg info -e drm-kmod; echo "installed=$?"

| If you see | Do this |
|---|---|
| `exit=0`, then `installed=0` | go to step 3 |
| anything else | run `grep -m3 -E 'No address record|Network is unreachable|timed out|Could not connect|No packages available' /root/drm-kmod-install.log`, report it with the output, and end with FAILED |

## Step 3: Check the driver was built for this kernel

`drm-kmod` itself only points to a package named `drm-` and a number and
`-kmod` (such as `drm-66-kmod`), which holds the modules. That package's
version ends with the FreeBSD version it was built for (the last number
before any `_`). This command compares that with the kernel and prints
`MATCH`, `MISMATCH`, or `UNKNOWN` when it cannot read a FreeBSD version
(seven digits). Run:

    p=$(pkg query '%n' | grep -E '^drm-[0-9]+-kmod$' | head -1); b=$(pkg query '%v' "$p" | sed -e 's/[_,].*//' -e 's/.*\.//'); k=$(uname -K); echo "package=$p built=$b kernel=$k"; case "$b" in [0-9][0-9][0-9][0-9][0-9][0-9][0-9]) case "$k" in [0-9][0-9][0-9][0-9][0-9][0-9][0-9]) [ "$b" = "$k" ] && echo MATCH || echo MISMATCH ;; *) echo UNKNOWN ;; esac ;; *) echo UNKNOWN ;; esac

Expected, such as:

    package=drm-66-kmod built=1501000 kernel=1501000
    MATCH

| If you see | Do this |
|---|---|
| a `package=drm-` line with numbers after `built=` and `kernel=`, then `MATCH` | go to step 4 |
| a `package=drm-` line with numbers after `built=` and `kernel=`, then `MISMATCH` | do **not** enable the driver; skip step 4 and go to step 3a |
| `UNKNOWN`, or anything else (such as `package=` with nothing after it) | stop, report the output, and end with FAILED |

## Step 3a: Only after MISMATCH: make sure it is not enabled already

The driver may have been set to load earlier (by hand, or before an
upgrade). The system reads that in two ways: `kld_list`, from `/etc/rc.conf`
and from `/etc/rc.conf.d/kld` (read here the way the system reads it at
boot), and a line `MODULE_load="YES"` in `/boot/loader.conf`,
`/boot/loader.conf.local` or a file in `/boot/loader.conf.d/`. This prints
`LISTED-KLD` if MODULE is in `kld_list` (in any form: `MODULE`, `MODULE.ko`
or a path ending in either), `LISTED-LOADER` and the file if a loader file
loads it, or `NOT-LISTED` if neither. Run:

    l=$(sh -c '. /etc/rc.subr && load_rc_config kld && echo "kld_list=$kld_list"') || l=ERROR; r=NOT-LISTED; case "$l" in kld_list=*) ;; *) r=ERROR ;; esac; for m in ${l#kld_list=}; do m=${m##*/}; m=${m%.ko}; [ "$m" = MODULE ] && r=LISTED-KLD; done; f=$(grep -lsiE '^[[:space:]]*MODULE_load[[:space:]]*=[[:space:]]*"?yes' /boot/loader.conf /boot/loader.conf.local /boot/loader.conf.d/*.conf); [ -n "$f" ] && r="$r LISTED-LOADER $f"; echo "$r"

| If you see | Do this |
|---|---|
| exactly `NOT-LISTED` | report: the driver is installed but was built for another kernel (the number after `built=` in step 3), so it is not enabled; to use it, build `graphics/drm-kmod` from the ports tree on this machine (skill `ports/port-install`). This is the correct result, not a failure: end with DONE |
| `NOT-LISTED` together with `LISTED-LOADER`, or `LISTED-KLD` | the driver is already set to load at boot, but it was built for another kernel: loading it can crash the system. Do not change anything yourself. Stop, report this as a warning, and end with FAILED. Say where it is set: for `LISTED-KLD`, in `kld_list` (removed with `sysrc kld_list-=MODULE`, or in `/etc/rc.conf.d/kld`); for `LISTED-LOADER`, the line `MODULE_load="YES"` in the file named after it |
| anything else | stop, report the output, and end with FAILED |

## Step 4: Load the driver at every boot

First check the module file belongs to the package checked in step 3, then
add it: `+=` adds MODULE to the modules already in `kld_list` (it removes
none, and adds nothing if MODULE is already there). Run:

    p=$(pkg query '%n' | grep -E '^drm-[0-9]+-kmod$' | head -1); o=$(pkg which -q /boot/modules/MODULE.ko); echo "owner=$o"; case "$o" in "$p"-[0-9]*) sysrc kld_list+=MODULE; echo "sysrc=$?"; sh -c '. /etc/rc.subr && load_rc_config kld && echo "at boot: $kld_list"' ;; *) echo NOT-FROM-PACKAGE ;; esac

Expected: `owner=` and the package from step 3 with its version (such as
`owner=drm-66-kmod-6.6.25.1501000_8`), then a line `kld_list:` with the old
value, `->`, and the new value, which contains `MODULE`, then `sysrc=0`,
then `at boot:` and the list the system will really use at boot (a
`kld_list` in `/etc/rc.conf.d/kld` would replace the one in `/etc/rc.conf`).
Note whether the old value (before `->`) already contained `MODULE` (Undo
needs to know).

| If you see | Do this |
|---|---|
| `owner=drm-`..., a `kld_list:` line whose new value (after `->`) contains `MODULE`, `sysrc=0`, and an `at boot:` line that contains `MODULE` | done: end with DONE |
| as above, but the `at boot:` line does not contain `MODULE` | `/etc/rc.conf.d/kld` sets its own `kld_list`, so the change to `/etc/rc.conf` has no effect. If the old value (before `->`) did not contain `MODULE`, take the change back with `sysrc kld_list-=MODULE`. Then stop, report it, and end with FAILED |
| `NOT-FROM-PACKAGE` | the module file is missing or does not come from the checked package; nothing was changed. Stop, report the output, and end with FAILED |
| anything else | stop, report the output, and end with FAILED |

Report that the driver is installed and enabled. It is loaded at the next
boot; to load it now instead, run `kldload MODULE` (only on the machine with
that graphics hardware).

## Undo

Only if step 4 added the module (the old value before `->` did not contain
`MODULE`), take it out of `kld_list` again:

    sysrc kld_list-=MODULE; echo "exit=$?"

Only if step 2 showed `found=1` (no driver package was installed before, and
this skill installed it), remove the package and what it brought:

    pkg delete -y drm-kmod; echo "exit=$?"
    pkg autoremove -n; echo "exit=$?"

`pkg autoremove -n` only lists what it would remove; it ends with `exit=1`
when there is something to remove, and `Nothing to do.` with `exit=0` when
there is not (as seen in the skill `ports/pkg-autoremove`). If every package it
lists is also in the `New packages to be INSTALLED:` list in
`/root/drm-kmod-install.log`, run `pkg autoremove -y; echo "exit=$?"`. If any
is not, do not: it was not installed by this skill; stop and report the list.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-10-06, snapshot 20260921 (a6deeaa2fb3b) | `drm-612-kmod`. On 2026-09-28 it was built for 1600026 (the snapshot's kernel): enabled. On 2026-10-06 the repository had a build for 1600027, newer than the snapshot: correctly not enabled. |
| 15.1-RELEASE | verified | 2026-10-06 | `drm-66-kmod` built for 1501000: enabled. |
| 15.0-RELEASE | verified | 2026-10-06 | `drm-66-kmod` built for 1500068: enabled. |
| 14.5-RELEASE | verified | 2026-10-06 | `drm-61-kmod` built for 1405000 (from `FreeBSD-kmods`): enabled. |
| 14.4-RELEASE | verified | 2026-10-06 | `drm-61-kmod` built for 1404000: enabled. |
| 14.3-RELEASE (EoL) | verified | 2026-10-06 | Built for 14.4: correctly not enabled. |
| 14.2-RELEASE (EoL) | verified | 2026-10-06 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-10-06 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-10-06 | As 14.3. |

## Weak-model check

2026-10-06 (UTC): claude-haiku-4-5, given only this skill, the input
`MODULE=i915kms` (not the skill's example), and a tool that runs one command
on the test machine, followed it on a freshly reset system of every release
above (pkg installed beforehand). A run counts only when the model said DONE
AND the independent check (`verify.sh`: a `drm-NN-kmod` package is
installed; when its build version equals `uname -K`, `i915kms` is in
`kld_list` as the system reads it at boot and `/boot/modules/i915kms.ko`
exists; otherwise `i915kms` is set to load neither in `kld_list` nor in a
loader file) passed: all 9 did. The final `verify.sh` was then run again on
each of the 9 systems the model had set up: all passed.

## Not verified

- Loading the driver (`kldload`, or a boot with `kld_list` set) was not
  tried: the test machines have no graphics processor. The skill stops at the
  package, the module file and `rc.conf`.
- Tried by hand (2026-09-28): the package holding the modules, and the
  FreeBSD version it was built for, per release: 14.0 to 14.4 get
  `drm-61-kmod` built for 14.4 (1404000); 14.5 gets `drm-61-kmod` built for
  14.5 from the `FreeBSD-kmods` repository; 15.0 `drm-66-kmod` built for
  1500068; 15.1 `drm-66-kmod` built for 1501000; 16.0-CURRENT (snapshot
  20260921) `drm-612-kmod` built for 1600026. Each matched `uname -K` except
  on 14.0 to 14.3. The package prints: "Please note that this package was
  built for FreeBSD ... If this is not your current running version, please
  rebuild it from ports to prevent panics when loading the module."
- `sysrc kld_list+=` was run twice: the second time left the value
  unchanged; with `kld_list="linux"` it gave `linux i915kms`.
- Building `graphics/drm-kmod` from the ports tree (the path for a
  `MISMATCH`) and Undo were not tried.
- NVIDIA drivers are a separate procedure (`nvidia-drm-kmod`), not part of
  this skill.

## Differences from the Handbook

- The Handbook installs `drm-kmod` and adds the module to `kld_list`. The
  skill also checks the driver was built for the running kernel first, as the
  package's own message asks, and does not enable it otherwise.
- The Handbook names the module per vendor in separate sections (Intel, AMD);
  the skill takes it as an input.

## Source

FreeBSD Handbook, "Graphics Drivers", "Intel(R) Graphics" and "AMD(R)
Graphics", https://docs.freebsd.org/en/books/handbook/x11/#x-configuration-intel
