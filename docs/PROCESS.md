# How the skills are made and tested

This describes the method, so that anyone can judge what "verified" means here,
and so the work can be continued the same way.

## 1. Read the Handbook section

Skills come from the FreeBSD Handbook source (AsciiDoc) at a recorded commit.
Each skill names that commit in `handbook_commit` and links to the section.

## 2. Run every step before writing it

Each procedure is carried out on a fresh FreeBSD system of each release in the
matrix:

- **Jails** for most userland work: packages, services, users, configuration.
- **Virtual machines** (bhyve) for anything that touches the kernel, the boot
  loader, disks, filesystems, firewalls or system updates. VMs are reset to a
  clean snapshot between skills.
- **Two or more VMs on a private network** for networking between machines.

The skill is then written from what actually happened: the real commands, the
real output, and every error met on the way and how it was fixed. Where the
Handbook's text and reality disagree, the skill follows reality and says so.

Anything that cannot be run, for example because it needs a physical wireless
card, a printer, a serial line or a display, is listed in the skill under "Not
verified", with the reason. It is never marked `verified`.

## 3. A small model follows the finished skill

Each finished skill is given to a small model, currently claude-haiku-4-5,
with nothing else: no other instructions, no memory, no project files. The
model works on a fresh system of the release under test.

The model gets exactly one tool, which runs a shell command on the test system
(`tools/harness/target_mcp.py`). It has no tools that act on the machine
running the test. The harness separates "the command could not reach the test
system" from "the command ran and failed", so an infrastructure problem is
never recorded as a failure of the skill.

After the model finishes, the skill's own Verify step is run independently.
The model's opinion of its success is not taken as the result. If the model
fails, the skill is rewritten, typically by removing an ambiguity or adding an
expected-output check, and the run is repeated from a fresh system.

## 4. Record results per release

Each skill has a "Release results" table with one row per release. Rows start
as `not verified` and change only after a real run. A release that reaches end
of life keeps its row and its release-specific steps, marked EoL. Nothing is
deleted, so the information stays useful to anyone still running that release.

16.0-CURRENT changes continuously, so its results record the snapshot build
date they were tested against.

## 5. What is not published

Raw test logs are kept privately. They contain details of the test
infrastructure, such as addresses and interface names, that do not belong in a
public repository. Each skill includes the outputs that matter for following
it.

## Release sources

| Releases | Source |
|---|---|
| Supported releases | https://download.freebsd.org/releases/ |
| End-of-life releases (14.0–14.3) | https://ftp-archive.freebsd.org/pub/FreeBSD-Archive/old-releases/ (checked against each release's `MANIFEST` checksums) |
| 16.0-CURRENT | https://download.freebsd.org/snapshots/ |
