---
name: bsdinstall-install-manual
description: Install FreeBSD with the installer (bsdinstall) at the machine's console, partitioning the first disk by hand in the partition editor (GPT; boot, swap and a UFS root), a fixed network address, a root password and one administrator account.
handbook: bsdinstall/#bsdinstall-part-manual
handbook_commit: bdf18a0458
---

# Install FreeBSD with manual partitioning

## What this does

Walks through the FreeBSD installer, screen by screen, at the console of a
machine that has just started from an installation image (skill
`bsdinstall/media-write-usb`). It installs FreeBSD on the **first disk, erasing it**, with a partition
table made by hand in the installer's partition editor: GPT, a 512 KB boot
partition, 2 GB of swap and a UFS root file system on the rest. It also sets
a fixed network address, a root password and one user who may become root.
At the end the machine restarts into the installed system.

This skill is done at the console, not in a shell. The tool for it types keys
and shows the screen (80 columns by 25 lines). On the screen, the item or
button that is currently selected is shown between `«` and `»`, such as
`[«  OK  »]`. Keys are written like this: `<Enter>`, `<Space>`, `<Up>`,
`<Down>`, `<Left>`, `<Right>`, `<Backspace>`; other text is typed as it is.
Sending no keys (an empty string) waits until the screen stops changing (up
to 2 minutes) and shows it again.

## Before you start

- You need: the machine started from a FreeBSD 15.1 `disc1` or `memstick`
  image, showing its console; network access (the installer downloads the
  debug and 32-bit parts from the Internet).
- This changes: **erases the machine's first disk** and installs FreeBSD
  on it.
- Time: about 10 minutes.
- Risk: high for any data on that disk; there is no Undo.
- The machine must start in BIOS (legacy) mode: the layout has a
  `freebsd-boot` partition and no `efi` partition, so a machine that starts
  with UEFI would not start the installed system.

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `HOSTNAME` | the machine's name | `web1` |
| `IPADDR` | its IPv4 address | `192.0.2.20` |
| `NETMASK` | the network mask | `255.255.255.0` |
| `ROUTER` | the default router | `192.0.2.1` |
| `DNS` | the name server | `192.0.2.1` |
| `ROOTPW` | the password for root | (a strong password) |
| `USERNAME` | the login name of the administrator account | `jru` |
| `FULLNAME` | that person's full name | `J. Random User` |
| `USERPW` | that account's password | (a strong password) |

Check them first: `HOSTNAME` is 1 to 63 letters, digits and `-`; the four
addresses are each four numbers from 0 to 255 separated by dots; `USERNAME`
is 1 to 16 characters, starting with a lower-case letter, then only
lower-case letters, digits and `_`; `FULLNAME` has only letters, digits,
spaces and `.` `-`; the passwords are 8 to 64 characters and contain no `~`,
no `<`, no `>` and no spaces. If any does not, stop and report it, type nothing, and end with FAILED.

## Step 1: Wait for the installer

Send no keys (an empty string) and read the screen. Repeat until the last
line is `Console type [vt100]:` (the machine may still be starting: this can
take a minute or two).

| If you see | Do this |
|---|---|
| `Console type [vt100]:` on the last line | go to step 2 |
| a `login:` prompt, or anything that is not the installer after 5 tries (each try waits up to 2 minutes) | stop, report the screen, and end with FAILED: the machine did not start the installer |

## Step 2: Terminal type and Welcome

Send `vt100<Enter>`. The screen shows **Welcome** with the buttons
`[  Install  ]`, `[   Shell   ]` and `[Live System]`, with `Install`
selected. Send `<Enter>`.

## Step 3: Hostname

The screen shows **Set Hostname** with an empty field. Send `HOSTNAME`
(the hostname filled in, with no `<Enter>`). Read the screen:

| The field shows | Do this |
|---|---|
| exactly the hostname | send `<Enter>` |
| nothing | send no keys (an empty string) once and read the screen again; if the field is still empty, send `HOSTNAME` once more, and read the screen again |
| anything else (part of the name, or the name twice) | send `<Backspace>` once for every character shown, then `HOSTNAME`, and read the screen again |

After 3 tries without exactly the hostname, stop, report the screen, and
end with FAILED.

## Step 4: Installation type

The screen shows **Select Installation Type** with the buttons
`[   Distribution Sets   ]` and `[Packages (Tech Preview)]`. Select
`Distribution Sets`: if `Packages (Tech Preview)` is between `«` and `»`,
send `<Left>`. When `«   Distribution Sets   »` is selected, send `<Enter>`.

## Step 5: Components

The screen shows **Distribution Select**, a list with `kernel-dbg` and
`lib32` ticked (`[X]`). Keep it as it is: send `<Enter>`.

The next screen says **Network Installation** (some files are not on the
image and will be downloaded). Send `<Enter>`.

## Step 6: Network

1. **Network Configuration**, a list of network interfaces (such as
   `vtnet0` or `em0`) with the buttons `[ Auto ]`, `[Manual]`, `[Cancel]`.
   Select `[Manual]` with `<Right>`, then send `<Enter>`.
2. **Would you like to configure IPv4 for this interface?** Send `<Enter>`
   (Yes).
3. **Would you like to use DHCP to configure this interface?** Select
   `[  No  ]` with `<Right>`, then send `<Enter>`.
4. **Static Network Interface Configuration**, a form with `IP Address`,
   `Subnet Mask` and `Default Router`. The cursor is in `IP Address`. Send
   `IPADDR<Down>NETMASK<Down>ROUTER` (values filled in), check the three
   fields on the screen show exactly them, then send `<Enter>`. If a field
   shows anything else, stop, report the screen, and end with FAILED.
5. **Would you like to configure IPv6 for this interface?** Select
   `[  No  ]` with `<Right>`, then send `<Enter>`.
6. **Resolver Configuration**, a form with `Search`, `IPv4 DNS #1` and
   `IPv4 DNS #2`. The cursor is in `Search`. Send `<Down>DNS` (value filled
   in), check `IPv4 DNS #1` shows exactly it, then send `<Enter>`. If it shows
   anything else, stop, report the screen, and end with FAILED.

## Step 7: Disk (by hand, in the partition editor)

In this step the same few keys come back often. **"Go to Create"** means:
send `<Left>` and read the screen, again and again (at most 6 times), until
the button `[«Create»]` at the bottom is selected (between `«` and `»`); it
is the first button on the left. **"Clear the field"** means: send `<Right>` twenty times
and then `<Backspace>` twenty times, in one call (the text in the field is
then gone; the cursor starts at the beginning of a filled-in field, so
`<Backspace>` alone does nothing).

1. **Partitioning**, a list starting with `Auto (ZFS)`. Send `<Down><Down>`
   so `«Manual»` is selected, then `<Enter>`.
2. **Partition Editor**, a list with the disk (such as `vtbd0` or `ada0`)
   selected and, at the bottom, the buttons `[Create] [Delete] [Modify]
   [Revert] [ Auto ] [Finish]`. Go to Create, then send `<Enter>`.
3. **Partition Scheme**, a list with `APM`, `BSD`, `GPT`, `MBR`. Send `<Up>`
   or `<Down>` until `«GPT»` is selected, then `<Enter>`. A message says *The
   partition table has been successfully created*. Send `<Enter>` (OK). The
   selection is now back on `[«Finish»]`: do **not** send `<Enter>` yet.
4. The boot partition. Go to Create, then send `<Enter>`. **Add Partition**,
   a form with `Type:`, `Size:`, `Mountpoint:` and `Label:`; the cursor is in
   `Type:`. Clear the field, then send `freebsd-boot`. Send `<Down>`, clear
   the field, then send `512K`. Read the screen: `Type:` shows `freebsd-boot`
   (the start may be scrolled off, such as `eebsd-boot`) and `Size:` shows
   `512K`. Send `<Enter>`. The list shows a new line with `512 KB` and
   `freebsd-boot`.
5. The swap partition. Go to Create, then send `<Enter>`. Clear the field,
   then send `freebsd-swap`. Send `<Down>`, clear the field, then send `2G`.
   Read the screen: `Size:` shows `2G`. Send `<Enter>`. The list shows a new
   line with `2.0 GB`, `freebsd-swap` and `none`.
6. The root partition. Go to Create, then send `<Enter>`. The form already
   shows `Type: freebsd-ufs` and the rest of the disk as the size; keep
   them. Send `<Down><Down>` (to `Mountpoint:`), clear the field, then send
   `/`. Read the screen: `Mountpoint:` shows exactly `/`. Send `<Enter>`.
7. The list must now show three lines under the disk: `512 KB freebsd-boot`,
   `2.0 GB freebsd-swap none`, and a line with `freebsd-ufs` and `/`. If it
   does not, stop, report the screen, and end with FAILED (nothing has been
   written to the disk yet).

If at any point in this step a message box with an error appears (such as
an unknown partition type), or a field shows something other than what the
step says, stop, report the screen, and end with FAILED.
8. `[«Finish»]` is selected. Send `<Enter>`. **Confirmation**: *Your changes
   will now be written to disk*, with `[   Commit    ]` selected. Send
   `<Enter>`. The disk is erased now.

## Step 8: Download and install

1. **Mirror Selection**, a list of download sites with the first,
   `http://download.freebsd.org` (Main Site), selected. Send `<Enter>`.
2. The installer downloads, checks and unpacks the files (**Fetching
   Distribution**, **Archive Extraction**, with progress bars). Send no keys
   (an empty string) again and again until the screen shows **Set root
   password**. This takes a few minutes; after 20 tries without it, stop,
   report the screen, and end with FAILED. If a screen says **Error** or
   **failed**, stop, report the screen, and end with FAILED.

## Step 9: Root password

Wait until the screen shows **Set root password**, a form with `Password`
and `Repeat password` (send no keys, as in step 8). Then send
`ROOTPW<Down>ROOTPW<Enter>` (the password filled in, both times).

| Next, if you see | Do this |
|---|---|
| **Time Zone Selector** | go to step 10 |
| a message that the passwords do not match, or **Set root password** again | send `<Enter>` if there is a message with `OK`, then, at the form, send `ROOTPW<Down>ROOTPW<Enter>` again. After 3 tries, stop, report the screen, and end with FAILED |
| anything else | stop, report the screen, and end with FAILED |

## Step 10: Time zone and clock

1. **Time Zone Selector** with `0  UTC` selected. Send `<Enter>`.
2. **Does the timezone abbreviation `UTC' look reasonable?** Send `<Enter>`
   (Yes).
3. **Time & Date** with a calendar and the buttons `[Set Date]` and
   `[  Skip  ]`, `Skip` selected. Send `<Enter>`.
4. **Time & Date** with the time and `[Set Time]` and `[  Skip  ]`, `Skip`
   selected. Send `<Enter>`.

## Step 11: Services and hardening

1. **System Configuration**: services to start at boot, with `sshd` and
   `dumpdev` ticked. Keep it: send `<Enter>`.
2. **System Hardening**: a list of options, none ticked. Keep it: send
   `<Enter>`.

## Step 12: Administrator account

1. **Would you like to add users to the installed system now?** Send
   `<Enter>` (Yes).
2. The screen changes to text questions, one after another, each on the last
   line. Answer them in this order, sending each answer with `<Enter>` and
   reading the screen after each one:

| The question ends with | Send |
|---|---|
| `Username:` | `USERNAME<Enter>` |
| `Full name:` | `FULLNAME<Enter>` |
| `Uid (Leave empty for default):` | `<Enter>` |
| `Login group [USERNAME]:` | `<Enter>` |
| `Invite USERNAME into other groups? []:` | `wheel<Enter>` |
| `Login class [default]:` | `<Enter>` |
| `Shell (sh csh tcsh nologin) [sh]:` | `<Enter>` |
| `Home directory [/home/USERNAME]:` | `<Enter>` |
| `Home directory permissions (Leave empty for default):` | `<Enter>` |
| `Use password-based authentication? [yes]:` | `<Enter>` |
| `Use an empty password? (yes/no) [no]:` | `<Enter>` |
| `Use a random password? (yes/no) [no]:` | `<Enter>` |
| `Enter password:` | `USERPW<Enter>` |
| `Enter password again:` | `USERPW<Enter>` |
| `Lock out the account after creation? [no]:` | `<Enter>` |
| `OK? (yes/no) [yes]:` | first check the summary above it shows `USERNAME`, `FULLNAME` and `Groups` with `wheel`; then `yes<Enter>`. If it does not, stop, report the screen, and end with FAILED |
| `Add another user? (yes/no) [no]:` | `no<Enter>` |

If a question on the screen is not the one expected, or `adduser` reports an
error, stop, report the screen, and end with FAILED.

## Step 13: Finish and restart

1. **Final Configuration**, a list starting with `Finish`, which is
   selected. Send `<Enter>`.
2. **Manual Configuration**: *would you like to open a shell ...?* `[  No  ]`
   is selected. Send `<Enter>`.
3. **Complete**: *Installation of FreeBSD complete!* `[  Reboot   ]` is
   selected. Send `<Enter>`.
4. Send no keys (an empty string) again and again (at most 10 times; if it
   does not appear, stop, report the screen, and end with FAILED) until a line
   `FreeBSD/amd64 (HOSTNAME) (...)` and `login:` appear: the installed system
   has started. Do not log in.

Report that FreeBSD was installed, with the hostname and address.

## Undo

None: the disk was erased. To start over, start the machine from the
installation image again.

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 15.1-RELEASE | verified | 2026-09-28 | `disc1` image, in a bhyve VM (BIOS boot) with a serial console and one 20 GB virtio disk (`vtbd0`). Also done by hand, screen by screen: the layout came out as below. |

Done by hand, `gpart show vtbd0` afterwards:

    =>      40  41942960  vtbd0  GPT  (20G)
            40       216         - free -  (108K)
           256      1024      1  freebsd-boot  (512K)
          1280   4194304      2  freebsd-swap  (2.0G)
       4195584  37747416      3  freebsd-ufs  (18G)

## Weak-model check

2026-09-28 (UTC): claude-haiku-4-5, given only this skill, the test inputs
(not the skill's examples), and a tool that types keys at the machine's
serial console and returns the screen, followed it on a freshly reset VM
started from the 15.1 `disc1` image. A run counts only when the model said
DONE, the console log shows the installer's first question, its
*Installation of FreeBSD complete!* screen and then the installed system's
login prompt as the last screen, with nothing typed after that prompt
appeared, AND the independent check (`verify.sh`, typed into the installed
system's console after logging in as root with the given password: release
15.1, the hostname in the running system and in `rc.conf`, a GPT disk with
`vtbd0p1` a 512K `freebsd-boot`, `vtbd0p2` a 2G `freebsd-swap` listed as
swap in `/etc/fstab`, `vtbd0p3` `freebsd-ufs` mounted as the root, the fixed
address, router and name server, `sshd` and crash dumps enabled, the time
zone UTC, the debug and 32-bit parts installed, the account in `wheel` with
its full name and the given password, and a password hash for root) passed.

## Not verified

- Only 15.1-RELEASE, from `disc1`, at a serial console, on one virtual disk.
  On a serial console the installer does not show the keyboard map screen
  the Handbook describes first.
- In this VM the partition scheme list started on `MBR`; the skill always
  picks GPT, as the Handbook recommends.
- Recovering from a hostname field that shows part of the name, and from
  root passwords that do not match, has not been tested.
- Tried by hand: in the partition editor, the selection returns to
  `[Finish]` after the *partition table has been successfully created*
  message, so an `<Enter>` there would go straight to *Commit*. `<Esc>` did
  not close the **Add Partition** form. In a filled-in field of that form the
  cursor starts at the beginning, so text typed there goes in front of what
  is shown.
- A machine that starts with UEFI (it needs an `efi` partition) was not
  tried.
- Other layouts (several file systems such as a separate `/var`, labels,
  ZFS by hand), MBR, DHCP, IPv6, wireless, other time zones, and packages
  instead of distribution sets are not part of this skill.

## Differences from the Handbook

- The Handbook describes the partition editor and suggests layouts with
  several file systems. The skill makes the simplest complete layout (boot,
  swap, one UFS root), with the keys to press, as the screens appear in
  15.1.
- 15.1 asks whether to install with distribution sets or packages (a
  technology preview); the skill picks distribution sets, which the
  Handbook describes.

## Source

FreeBSD Handbook, "Manual Partitioning",
https://docs.freebsd.org/en/books/handbook/bsdinstall/#bsdinstall-part-manual
