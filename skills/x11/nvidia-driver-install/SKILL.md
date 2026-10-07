---
name: x11-nvidia-driver-install
description: Install the current NVIDIA graphics driver (nvidia-drm-kmod) and have it loaded at every boot with kernel modesetting, but only when its kernel modules were built for the running kernel and belong to the same driver version.
handbook: x11/#x-configuration-nvidia
handbook_commit: bdf18a0458
---

# Install the NVIDIA graphics driver

## What this does

Installs the package `nvidia-drm-kmod`, the current NVIDIA driver, which
brings two packages of kernel modules: `nvidia-kmod` (the modules `nvidia`
and `nvidia-modeset`) and a package named `nvidia-drm-` and a number and
`-kmod` (the module `nvidia-drm`). Then it adds `nvidia-drm` to `kld_list`
in `/etc/rc.conf`, so the system loads it at every boot, and turns on kernel
modesetting (`hw.nvidiadrm.modeset=1` in `/boot/loader.conf`), which
`nvidia-drm` needs.

Two things are checked first, because the packages do not always fit:

- each module package must be built for the running kernel (the packages
  for 14.0 to 14.3, and for 15.1, are built for another release), and
- both must be the same driver version: `nvidia-drm` refuses to start
  beside an `nvidia-modeset` of another version (seen on 14.4, where the
  two packages come from different repositories).

If either does not hold, the driver stays installed but is not enabled.

## Before you start

- You need: a root shell, network access to `pkg.FreeBSD.org`, pkg itself
  installed (skill `ports/pkg-bootstrap`), and an NVIDIA graphics processor
  that the current driver supports: run `pciconf -lv | grep -B3 display`;
  the `vendor =` line says `NVIDIA Corporation`. Older NVIDIA hardware needs
  an older driver (`nvidia-driver-470`, `-390`, `-340`, `-304`), which this
  skill does not cover.
- This changes: installs about 200 packages (the driver, X.org and their
  libraries), changes `kld_list` in `/etc/rc.conf` and adds a line to
  `/boot/loader.conf`.
- Time: about two minutes with a fast connection.
- Risk: medium: a driver that does not suit the hardware can make the
  screen go blank at boot. See Undo.

## Step 1: Identify the release

The driver is loaded at the next boot, into the kernel installed on disk. If
that is not the kernel running now (an upgrade is waiting for a restart), the
check in step 3 would compare against the wrong kernel. The command prints
the release of the installed userland, then `SAME-KERNEL` if the running kernel's own
version line (with its build number and source revision) is found in the
kernel file it was started from, or `DIFFERENT-KERNEL` if not. Run:

    freebsd-version -u; v=$(sysctl -n kern.version | head -1); f=$(sysctl -n kern.bootfile); if [ -z "$v" ]; then echo NO-VERSION; elif [ ! -r "$f" ]; then echo "NO-KERNEL-FILE $f"; elif grep -q -F -- "$v" "$f"; then echo SAME-KERNEL; else echo DIFFERENT-KERNEL; fi

| If you see | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24), then `SAME-KERNEL` | go to step 2 |
| `DIFFERENT-KERNEL` | the kernel on disk is not the one running (a new kernel is waiting for a restart). Stop, report it, and end with FAILED: restart the machine first, then run this skill |
| `NO-VERSION` or `NO-KERNEL-FILE` | the check could not be made. Stop, report the output, and end with FAILED |
| anything else | stop, report the output, and end with FAILED: this skill was not tested there |

## Step 2: Install nvidia-drm-kmod

First check whether an NVIDIA driver package is already installed. If one
is, do not run `pkg install`: it might replace a driver built for this
kernel (from the ports tree) with a package built for another. Run:

    if l=$(pkg query '%n'); then echo "$l" | grep -E '^nvidia-(drm-kmod|kmod|drm-[0-9]+-kmod|driver.*)$'; echo "found=$?"; else echo PKG-ERROR; fi

| If you see | Do this |
|---|---|
| one or more package names, then `found=0` | already installed: do not install, go to step 3 (Undo will not remove it) |
| only `found=1` | not installed: run the next command |
| `PKG-ERROR`, or anything else | stop, report the output, and end with FAILED |

Only after `found=1`, run exactly this (`-y` answers pkg's question; without
it pkg installs nothing). The full output goes to
`/root/nvidia-driver-install.log`:

    pkg install -y nvidia-drm-kmod > /root/nvidia-driver-install.log 2>&1; echo "exit=$?"; pkg info -e nvidia-drm-kmod; echo "installed=$?"

| If you see | Do this |
|---|---|
| `exit=0`, then `installed=0` | go to step 3 |
| anything else | run `grep -m3 -E 'No address record|Network is unreachable|timed out|Could not connect|No packages available' /root/nvidia-driver-install.log`, report it with the output, and end with FAILED |

## Step 3: Check the modules were built for this kernel and fit together

Each module package's version ends with the FreeBSD version it was built
for (the last number before any `_`); the part before it is the NVIDIA
driver version. This command prints one line per package, a line
`driver versions differ:` if they do, and then `MATCH` (both built for this
kernel, same driver version), `MISMATCH`, or `UNKNOWN` when it cannot read
them. Run:

    k=$(uname -K); r=MATCH; case "$k" in [0-9][0-9][0-9][0-9][0-9][0-9][0-9]) ;; *) r=UNKNOWN ;; esac; d0=; n=0; for p in nvidia-kmod $(pkg query '%n' | grep -E '^nvidia-drm-[0-9]+-kmod$'); do v=$(pkg query '%v' "$p") || { r=UNKNOWN; continue; }; b=$(echo "$v" | sed -e 's/[_,].*//' -e 's/.*\.//'); d=$(echo "$v" | sed -e 's/[_,].*//' -e 's/\.[^.]*$//'); echo "package=$p driver=$d built=$b kernel=$k"; n=$((n+1)); case "$b" in [0-9][0-9][0-9][0-9][0-9][0-9][0-9]) ;; *) r=UNKNOWN ;; esac; [ "$b" = "$k" ] || [ "$r" = UNKNOWN ] || r=MISMATCH; [ -z "$d0" ] && d0=$d; [ "$d" = "$d0" ] || { [ "$r" = UNKNOWN ] || r=MISMATCH; echo "driver versions differ: $d0 and $d"; }; done; [ "$n" -ge 2 ] || r=UNKNOWN; echo "$r"

Expected, such as:

    package=nvidia-kmod driver=595.84 built=1500068 kernel=1500068
    package=nvidia-drm-66-kmod driver=595.84 built=1500068 kernel=1500068
    MATCH

| If the last line is | Do this |
|---|---|
| `MATCH` | go to step 4 |
| `MISMATCH` | do **not** enable the driver; skip step 4 and go to step 3a |
| `UNKNOWN`, or anything else | stop, report the output, and end with FAILED |

## Step 3a: Only after MISMATCH: make sure it is not enabled already

The driver may have been set to load earlier (by hand, or before an
upgrade): in `kld_list` (from `/etc/rc.conf` and `/etc/rc.conf.d/kld`, read
here the way the system reads it at boot), or with a line
`nvidia-drm_load="YES"` or `nvidia_drm_load="YES"` in `/boot/loader.conf`,
`/boot/loader.conf.local` or a file in `/boot/loader.conf.d/`. This prints
`LISTED-KLD` if `nvidia-drm` is in `kld_list` (as `nvidia-drm`,
`nvidia-drm.ko` or a path ending in either), `LISTED-LOADER` and the file if
a loader file loads it, or `NOT-LISTED` if neither. Run:

    l=$(sh -c '. /etc/rc.subr && load_rc_config kld && echo "kld_list=$kld_list"') || l=ERROR; r=NOT-LISTED; case "$l" in kld_list=*) ;; *) r=ERROR ;; esac; for m in ${l#kld_list=}; do m=${m##*/}; m=${m%.ko}; [ "$m" = nvidia-drm ] && r=LISTED-KLD; done; f=$(grep -lsiE '^[[:space:]]*nvidia[-_]drm_load[[:space:]]*=[[:space:]]*"?yes"?[[:space:]]*(#.*)?$' /boot/loader.conf /boot/loader.conf.local /boot/loader.conf.d/*.conf); [ -n "$f" ] && r="$r LISTED-LOADER $f"; echo "$r"

| If you see | Do this |
|---|---|
| exactly `NOT-LISTED` | report: the driver is installed, but its modules were built for another kernel or for different driver versions (the lines from step 3), so it is not enabled; to use it, build `graphics/nvidia-drm-kmod` from the ports tree on this machine (skill `ports/port-install`). This is the correct result, not a failure: end with DONE |
| `NOT-LISTED` together with `LISTED-LOADER`, or `LISTED-KLD` | the driver is already set to load at boot although its modules do not fit this kernel. Do not change anything yourself. Stop, report this as a warning, and end with FAILED. Say where it is set: for `LISTED-KLD`, in `kld_list` (removed with `sysrc kld_list-=nvidia-drm`, or in `/etc/rc.conf.d/kld`); for `LISTED-LOADER`, the `_load="YES"` line in the file named after it |
| anything else | stop, report the output, and end with FAILED |

## Step 4: Load the driver at every boot, with modesetting

The command first repeats the check of step 3 and does nothing but print
`NOT-MATCH` unless it still says MATCH. Then it checks the module file
belongs to the package checked in step 3. Then
turn on modesetting. The loader reads `/boot/loader.conf`, then
`/boot/loader.conf.local` and the files in `/boot/loader.conf.d/`; the
command looks at all of them. It adds the line `hw.nvidiadrm.modeset="1"` to
`/boot/loader.conf` if none of them sets it (`loader=added`), leaves it if
every line there sets `1` (`loader=already`), and otherwise changes nothing
and prints `loader=other` and the lines it found (also when the line could
not be written). (`sysrc` cannot
set a name with dots, so the line is added directly.) Only then it adds
`nvidia-drm` to `kld_list` (`+=` adds it to the modules already there,
removes none, and adds nothing if it is already there). Run:

    k=$(uname -K); r=MATCH; case "$k" in [0-9][0-9][0-9][0-9][0-9][0-9][0-9]) ;; *) r=UNKNOWN ;; esac; d0=; n=0; for q in nvidia-kmod $(pkg query '%n' | grep -E '^nvidia-drm-[0-9]+-kmod$'); do v=$(pkg query '%v' "$q") || r=UNKNOWN; b=$(echo "$v" | sed -e 's/[_,].*//' -e 's/.*\.//'); d=$(echo "$v" | sed -e 's/[_,].*//' -e 's/\.[^.]*$//'); n=$((n+1)); [ "$b" = "$k" ] || r=NO; [ -z "$d0" ] && d0=$d; [ "$d" = "$d0" ] || r=NO; done; [ "$n" -ge 2 ] || r=NO; if [ "$r" != MATCH ]; then echo NOT-MATCH; else p=$(pkg query '%n' | grep -E '^nvidia-drm-[0-9]+-kmod$' | head -1); o=$(pkg which -q /boot/modules/nvidia-drm.ko); echo "owner=$o"; case "$o" in "$p"-[0-9]*) m=$(grep -hE '^[[:space:]]*hw\.nvidiadrm\.modeset[[:space:]]*=' /boot/loader.conf /boot/loader.conf.local /boot/loader.conf.d/*.conf 2>/dev/null); st=other; if [ -z "$m" ]; then f=/boot/loader.conf; { [ ! -s "$f" ] || [ -z "$(tail -c1 "$f")" ] || echo; echo 'hw.nvidiadrm.modeset="1"'; } >> "$f" && st=added; elif ! echo "$m" | grep -qvE '=[[:space:]]*"?1"?[[:space:]]*(#.*)?$'; then st=already; fi; echo "loader=$st"; [ "$st" = other ] && echo "$m"; case "$st" in added|already) sysrc kld_list+=nvidia-drm; echo "sysrc=$?"; sh -c '. /etc/rc.subr && load_rc_config kld && echo "at boot: $kld_list"' ;; esac ;; *) echo NOT-FROM-PACKAGE ;; esac; fi

Expected: `owner=` and the package from step 3 with its version (such as
`owner=nvidia-drm-66-kmod-595.84.1500068_1`); `loader=added` or
`loader=already`; a line `kld_list:` with the old value, `->`, and the new
value, which contains `nvidia-drm`; `sysrc=0`; then `at boot:` and the list
the system will really use at boot. Note whether it said `loader=added`, and
whether the old value of `kld_list` (before `->`) already contained
`nvidia-drm` (Undo needs both).

| If you see | Do this |
|---|---|
| `owner=nvidia-drm-`..., `loader=added` or `loader=already`, the `kld_list:` line whose new value contains `nvidia-drm`, `sysrc=0`, and an `at boot:` line that contains `nvidia-drm` | done: end with DONE |
| `loader=other` (with or without lines after it) | a loader file already sets `hw.nvidiadrm.modeset` to another value, or `/boot/loader.conf` could not be written; nothing was changed. Stop, report the output, and end with FAILED |
| as above, but the `at boot:` line does not contain `nvidia-drm` | `/etc/rc.conf.d/kld` sets its own `kld_list`, so the change to `/etc/rc.conf` has no effect. If the old value did not contain `nvidia-drm`, take it back with `sysrc kld_list-=nvidia-drm`; if it said `loader=added`, also remove that line (the `sed` command in Undo). Then stop, report it, and end with FAILED |
| `NOT-FROM-PACKAGE` | the module file is missing or does not come from the checked package; nothing was changed. Stop, report the output, and end with FAILED |
| `NOT-MATCH` | step 3 said MATCH, but the check now fails (the packages changed, or pkg could not be read); nothing was changed. Stop, report the output, and end with FAILED |
| anything else | stop, report the output, and end with FAILED. If the output said `loader=added`, that line stays in `/boot/loader.conf`: say so (Undo removes it) |

Report that the driver is installed and enabled. It is loaded at the next
boot.

## Undo

Only if step 4 added `nvidia-drm` (the old value of `kld_list` did not
contain it), take it out again:

    sysrc kld_list-=nvidia-drm; echo "exit=$?"

Only if step 4 said `loader=added`, remove the line it added:

    sed -i '' '/^hw\.nvidiadrm\.modeset="1"$/d' /boot/loader.conf; echo "exit=$?"

Only if step 2 showed `found=1` (no NVIDIA package was installed before, and
this skill installed it), remove the package and what it brought:

    pkg delete -y nvidia-drm-kmod; echo "exit=$?"
    pkg autoremove -n; echo "exit=$?"

`pkg autoremove -n` only lists what it would remove; it ends with `exit=1`
when there is something to remove, and `Nothing to do.` with `exit=0` when
there is not (as seen in the skill `ports/pkg-autoremove`). If every package
it lists is also in the `New packages to be INSTALLED:` list in
`/root/nvidia-driver-install.log`, run `pkg autoremove -y; echo "exit=$?"`.
If any is not, do not: it was not installed by this skill; stop and report
the list.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-10-06, snapshot 20260921 (a6deeaa2fb3b) | Modules built for 1600027, newer than the snapshot kernel (1600026): correctly not enabled. |
| 15.1-RELEASE | verified | 2026-10-06 | Modules built for 15.0 (1500068): correctly not enabled. |
| 15.0-RELEASE | verified | 2026-10-06 | Both built for 1500068, driver 595.84: enabled with modesetting. |
| 14.5-RELEASE | verified | 2026-10-06 | `nvidia-kmod` 595.104.02 (built for 14.5) but `nvidia-drm-61-kmod` 595.84 (built for 14.4): correctly not enabled. |
| 14.4-RELEASE | verified | 2026-10-06 | Both built for 14.4, but driver versions 595.104.02 and 595.84: correctly not enabled. |
| 14.3-RELEASE (EoL) | verified | 2026-10-06 | Built for 14.4: correctly not enabled. |
| 14.2-RELEASE (EoL) | verified | 2026-10-06 | As 14.3. |
| 14.1-RELEASE (EoL) | verified | 2026-10-06 | As 14.3. |
| 14.0-RELEASE (EoL) | verified | 2026-10-06 | As 14.3. |

## Weak-model check

2026-10-06 (UTC): claude-haiku-4-5, given only this skill and a tool that
runs one command on the test machine, followed it on a freshly reset system
of every release above (pkg installed beforehand). A run counts only when
the model said DONE AND the independent check (`verify.sh`: `nvidia-drm-kmod`
is installed; when `nvidia-kmod` and the `nvidia-drm-NN-kmod` package are
both built for `uname -K` and carry the same driver version, `nvidia-drm` is
in `kld_list` as the system reads it at boot, its module file belongs to
that package, and every loader line setting `hw.nvidiadrm.modeset` says 1;
otherwise `nvidia-drm` is set to load nowhere) passed: all 9 did.

## Not verified

- The test machines have no graphics processor, so the driver was never used
  to drive a screen.
- Tried by hand (2026-10-06), loading the modules with `kldload nvidia` and
  `kldload nvidia-drm` on machines without a GPU: on 15.0 (modules built for
  15.0, driver 595.84) both loaded; on 14.4 (`nvidia-kmod` 595.104.02 from
  `FreeBSD-kmods`, `nvidia-drm-61-kmod` 595.84 from `FreeBSD`) both loaded,
  but the kernel log said `[nvidia-drm] Version mismatch:
  nvidia-modeset.ko(595.104.02) nvidia-drm.ko(595.84)`, so `nvidia-drm` does
  not work there; on 15.1 the modules built for 15.0 loaded without an error
  message. So the "same kernel" rule is stricter than needed on 15.1; it is
  kept because nothing guarantees a module built for another release works,
  and the `drm-kmod` package itself warns about panics.
- Packages per release (2026-10-06): 14.0 to 14.3 get both module packages
  built for 14.4; 14.4 and 14.5 get `nvidia-kmod` 595.104.02 built for the
  release from `FreeBSD-kmods` but `nvidia-drm-61-kmod` 595.84 built for 14.4
  from `FreeBSD`; 15.0 gets both built for 15.0 (driver 595.84); 15.1 gets
  the 15.0 builds; 16.0-CURRENT gets builds for 1600027, newer than the
  snapshot kernel (1600026).
- `fwget`, which the Handbook mentions for firmware, said
  `No firmware packages to install.` on 14.0 and 15.1 (no devices that need
  any); it is not part of this skill.
- The older drivers (`nvidia-driver-470` and older, `nvidia-modeset` or
  `nvidia` in `kld_list`), building from the ports tree, and Undo were not
  tried.

## Differences from the Handbook

- The Handbook installs `nvidia-drm-kmod`, adds `nvidia-drm` to `kld_list`,
  and sets `hw.nvidiadrm.modeset="1"` for subsequent boots. The skill does
  the same, but only after checking that the modules were built for this
  kernel and are the same driver version, and adds the modesetting line to
  `/boot/loader.conf` only if no such line is there (`sysrc` cannot set a
  name with dots: it answers `name contains characters not allowed in
  shell`).

## Source

FreeBSD Handbook, "NVIDIA(R) Graphics",
https://docs.freebsd.org/en/books/handbook/x11/#x-configuration-nvidia
