---
name: x11-xorg-driver-select
description: Choose the X.org graphics driver (intel, radeon, nvidia, scfb or vesa) with a small file in /usr/local/etc/X11/xorg.conf.d, after making sure the driver is installed and no other file already chooses one.
handbook: x11/#x-config-gpu
handbook_commit: bdf18a0458
---

# Choose the X.org graphics driver in a file

## What this does

X.org normally finds a graphics driver by itself. When it picks the wrong
one, or several drivers conflict, a file in
`/usr/local/etc/X11/xorg.conf.d/` can name the driver to use. This skill
installs the driver if needed and writes that file, named as in the
Handbook (`20-intel.conf`, `20-vesa.conf` and so on), with one `Device`
section. X.org reads it the next time it starts.

| `DRIVER` | Use it for | Package with the driver |
|---|---|---|
| `intel` | Intel graphics (with skill `x11/drm-kmod-install`) | `xf86-video-intel` |
| `radeon` | older AMD graphics (with `x11/drm-kmod-install`) | `xf86-video-ati` |
| `nvidia` | NVIDIA graphics | comes with the skill `x11/nvidia-driver-install` |
| `scfb` | no supported driver, machine started with UEFI | `xf86-video-scfb` |
| `vesa` | no supported driver, machine started with BIOS | `xf86-video-vesa` |

`sysctl machdep.bootmethod` says `UEFI` or `BIOS`.

## Before you start

- You need: a root shell, network access to `pkg.FreeBSD.org`, pkg, and the
  X server installed (skill `x11/xorg-install`).
- This changes: may install the driver package, and creates one file in
  `/usr/local/etc/X11/xorg.conf.d/`.
- Time: under a minute.
- Risk: low: a wrong driver only stops X from starting; Undo removes the
  file.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `DRIVER` | the X.org driver to use | `intel` |

`DRIVER` must be exactly one of `intel`, `radeon`, `nvidia`, `scfb`, `vesa`.
If it is not, stop, report it, run no command, and end with FAILED.
Everywhere below, replace `DRIVER` with this value, and `PACKAGE` with the
package for it from the table above.

## Step 1: Identify the release

Run:

    freebsd-version -u

| The line is | Do this |
|---|---|
| `14.0-RELEASE` to `14.5-RELEASE`, `15.0-RELEASE`, `15.1-RELEASE` or `16.0-CURRENT`, possibly followed by `-p` and a number (14.0 to 14.3 are end of life as of 2026-09-24) | go to step 2 |
| anything else | stop, report the line, and end with FAILED: this skill was not tested there |

## Step 2: Check the X server is installed

Run:

    pkg -N >/dev/null 2>&1; echo "pkg=$?"; pkg -N >/dev/null 2>&1 && { pkg info -e xorg-server; echo "xserver=$?"; }

| If you see | Do this |
|---|---|
| `pkg=0`, then `xserver=0` | go to step 3 |
| `pkg=0`, then `xserver=1` | the X server is not installed. Stop, report it, and end with FAILED (install it first with `x11/xorg-install`) |
| anything else | stop, report the output, and end with FAILED |

## Step 3: Make sure the driver is installed

A driver is a file named after it in `/usr/local/lib/xorg/modules/drivers/`.
Run:

    ls /usr/local/lib/xorg/modules/drivers/DRIVER_drv.so; echo "exit=$?"

| If you see | Do this |
|---|---|
| `/usr/local/lib/xorg/modules/drivers/DRIVER_drv.so`, then `exit=0` | installed: go to step 4 |
| `No such file or directory` and `exit=1`, and `DRIVER` is `nvidia` | stop, report it, and end with FAILED: install the NVIDIA driver with `x11/nvidia-driver-install` first |
| `No such file or directory` and `exit=1` (any other `DRIVER`) | run the next command |
| anything else | stop, report the output, and end with FAILED |

Only in that case, install the package (`-y` answers pkg's question):

    pkg install -y PACKAGE > /root/xorg-driver-select.log 2>&1; echo "exit=$?"; ls /usr/local/lib/xorg/modules/drivers/DRIVER_drv.so

| If you see | Do this |
|---|---|
| `exit=0`, then `/usr/local/lib/xorg/modules/drivers/DRIVER_drv.so` | go to step 4 |
| anything else | run `grep -m3 -E 'No address record|Network is unreachable|timed out|Could not connect|No packages available' /root/xorg-driver-select.log`, report it with the output, and end with FAILED |

## Step 4: Check no other file chooses a graphics device

Two things can make the new file useless or conflicting:

- If `/etc/X11/xorg.conf.d/` holds any `.conf` file, X.org uses that folder
  **instead of** `/usr/local/etc/X11/xorg.conf.d/`, and a file written there
  would be ignored.
- A file `xorg.conf` (in `/usr/local/etc/X11/` or `/etc/X11/`, or one of
  the other names X.org looks for, such as `xorg.conf-4` or
  `xorg.conf.` and the host name) is read together with the folder; two
  files that each name a graphics driver make X.org load both.

This prints `SHADOWED` and the files if `/etc/X11/xorg.conf.d/` holds
`.conf` files, then every file X.org reads that already has a `Device`
section, or `NONE`. Any `Device` section counts, with or without a `Driver`
line: without a `Screen` section, X.org uses the first `Device` section it
reads. (`Driver` lines in other sections, such as for a keyboard, or an
`OutputClass` section that applies only to matching hardware, do not count.)

    s=$(ls /etc/X11/xorg.conf.d/*.conf 2>/dev/null); [ -n "$s" ] && echo "SHADOWED $s"; f=$(for x in /etc/X11/xorg.conf* /usr/local/etc/X11/xorg.conf* /etc/xorg.conf* /usr/local/lib/X11/xorg.conf* /usr/local/etc/X11/xorg.conf.d/*.conf /etc/X11/xorg.conf.d/*.conf /usr/local/share/X11/xorg.conf.d/*.conf; do [ -f "$x" ] && echo "$x"; done | xargs awk 'tolower($1)=="section" && tolower($2)=="\"device\""{print FILENAME}' | sort -u); echo "${f:-NONE}"

| If you see | Do this |
|---|---|
| a line starting `SHADOWED` | X.org reads `/etc/X11/xorg.conf.d/` instead. Do not change anything else. If step 3 installed the package, remove it again (Undo). Stop, report it, and end with FAILED |
| `NONE` (and no `SHADOWED`) | go to step 5 |
| exactly `/usr/local/etc/X11/xorg.conf.d/20-DRIVER.conf` | the file may be there already: go to step 5, which checks it |
| any other file name | another file already has a `Device` section. Do not change it. If step 3 installed the package, remove it again (Undo). Stop, report the file names, and end with FAILED |

## Step 5: Write the file

This writes the file only if nothing of that name exists yet (`written`;
it is written to a temporary file first and then moved into place, so a
failed write leaves nothing behind), says `already` if it exists with
exactly this content, and `different` (writing nothing) if it exists with
other content or is a link. Run:

    d=/usr/local/etc/X11/xorg.conf.d; f=$d/20-DRIVER.conf; c=$(printf 'Section "Device"\n\tIdentifier "Card0"\n\tDriver     "DRIVER"\nEndSection'); if [ -L "$f" ]; then echo different; elif [ ! -e "$f" ]; then mkdir -p "$d" && printf '%s\n' "$c" > "$f.new" && mv "$f.new" "$f" && echo written || rm -f "$f.new"; elif [ "$(cat "$f")" = "$c" ]; then echo already; else echo different; fi; cat "$f"

Expected:

    written
    Section "Device"
    	Identifier "Card0"
    	Driver     "DRIVER"
    EndSection

(with `DRIVER` filled in; `already` instead of `written` if the file was
there).

| If you see | Do this |
|---|---|
| `written` or `already`, then the four lines above with `DRIVER` | done: end with DONE |
| `different`, then other lines | `20-DRIVER.conf` exists with other content. Do not change it. Stop, report it, and end with FAILED |
| anything else | stop, report the output, and end with FAILED |

Report that X.org will use the driver `DRIVER` the next time it starts. Note
whether step 5 said `written` and whether step 3 installed the package
(Undo needs to know).

## Undo

Only if step 5 said `written`, remove the file:

    rm /usr/local/etc/X11/xorg.conf.d/20-DRIVER.conf; echo "exit=$?"

Only if step 3 installed the package, remove it:

    pkg delete -y PACKAGE; echo "exit=$?"

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | verified | 2026-10-07, snapshot 20260921 (a6deeaa2fb3b) |  |
| 15.1-RELEASE | verified | 2026-10-07 | Also tried by hand. |
| 15.0-RELEASE | verified | 2026-10-07 |  |
| 14.5-RELEASE | verified | 2026-10-07 |  |
| 14.4-RELEASE | verified | 2026-10-07 |  |
| 14.3-RELEASE (EoL) | verified | 2026-10-07 |  |
| 14.2-RELEASE (EoL) | verified | 2026-10-07 |  |
| 14.1-RELEASE (EoL) | verified | 2026-10-07 |  |
| 14.0-RELEASE (EoL) | verified | 2026-10-07 |  |

## Weak-model check

2026-10-07 (UTC): claude-haiku-4-5, given only this skill, the input
`DRIVER=vesa` (not the skill's example), and a tool that runs one command on
the test machine, followed it on a freshly reset system of every release
above (pkg and the X server installed beforehand, the VESA driver not). A
run counts only when the model said DONE AND the independent check
(`verify.sh`: `vesa_drv.so` is installed, `20-vesa.conf` holds exactly the
`Device` section, no other file X.org reads has a `Device` section, and the
X server, started once, read `/usr/local/etc/X11/xorg.conf.d` and loaded no
video driver but `vesa`) passed: all 9 did. (Step 4 and the check were then
widened to count every `Device` section, not only those naming a driver;
the final `verify.sh`, run again on each of the 9 systems the model had set
up, passed.)

## Not verified

- Tried by hand on 15.1 (2026-10-06), on a machine without a screen:
  without a file, the X server tried the drivers `modesetting`, `scfb` and
  `vesa` in turn; with `20-vesa.conf` it loaded only `vesa`. In both cases it
  then stopped with `xf86OpenConsole: No console driver found` (the test
  machines have only a serial console). So the file was read and obeyed;
  showing a picture was not tried.
- Tried by hand on 15.1: with a `.conf` file in `/etc/X11/xorg.conf.d/`,
  X.org said `Using config directory: "/etc/X11/xorg.conf.d"` and ignored
  `/usr/local/etc/X11/xorg.conf.d/` (an empty `/etc/X11/xorg.conf.d/` did
  not); with `/usr/local/etc/X11/xorg.conf` naming `scfb` beside
  `20-vesa.conf`, it read both and loaded both drivers.
- `OutputClass` sections are not counted as choosing a driver: they apply
  only to the hardware they match, and the X server package's own
  `/usr/local/share/X11/xorg.conf.d/10-quirks.conf` has one (`Driver
  "modesetting"` for Apple hardware) on every machine. One installed by an
  NVIDIA driver package could still pick `nvidia` for an NVIDIA card next to
  the file this skill writes; that was not tried.
- The `xorg` package (skill `x11/xorg-install`) already brings the `vesa`
  and `scfb` drivers (through `xorg-drivers`); `intel`, `radeon` and
  `nvidia` come from their own packages.
- The drivers `intel`, `radeon`, `nvidia` and `scfb`, several graphics
  processors with `BusID`, PRIME (`DRI_PRIME=1`) and `nvidia-xconfig` were
  not tried.

## Differences from the Handbook

- The Handbook shows each file's contents. The skill also checks that the
  driver is installed and that no other file already names a driver, and
  never overwrites an existing file.

## Source

FreeBSD Handbook, "X.org Configuration Files" and "Graphics Configuration",
https://docs.freebsd.org/en/books/handbook/x11/#x-config-gpu
