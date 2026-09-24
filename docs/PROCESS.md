# How the skills are made and tested

This describes the method, so that anyone can judge what "verified" means here,
and so the work can be continued the same way.

## 1. Read the Handbook section

Skills come from the FreeBSD Handbook source (AsciiDoc) at a recorded commit.
Each skill names that commit in `handbook_commit` and links to the section.

## 2. Run every step before writing it

Test systems are contained: they sit on an isolated network whose only way
out is a gateway that allows the FreeBSD package and update servers and
nothing else. Nothing leaves them except requests to those FreeBSD servers
(which include the normal pkg and update client details, such as the
release's ABI); nothing is ever submitted upstream. A service that a skill
needs to talk to (a mail server, a second host) is created on that network for
the test and deleted as soon as it is no longer needed.

Each procedure is carried out on a fresh FreeBSD system of each release in the
matrix:

- **Jails** for most userland work: packages, services, users, configuration.
- **Virtual machines** (bhyve) for anything that touches the kernel, the boot
  loader, disks, filesystems, firewalls or system updates. There are two VMs
  per release: one with a UFS root and one with a ZFS root, so skills that
  depend on the root file system (for example, taking a boot environment
  before an upgrade) are tested both ways. VMs are reset to a clean snapshot
  between skills, and every test machine gets a checkpoint snapshot before
  work on each Handbook section starts.
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

Each skill directory holds, next to `SKILL.md`, the files the test uses:

| File | Purpose |
|---|---|
| `report-only` | Optional, empty. Marks a skill that only reports something and changes nothing. It has `answer.sh` instead of `verify.sh`: the true answer is computed before the model runs, must be unchanged afterwards (so the model did not alter what it reports on), and must be in the model's final message. |
| `verify.sh` | (Not used by a `report-only` skill.) Run on the test system after the model finishes. Exit 0 means the task's end state exists. It is also run before the model starts, and must fail on a fresh system; when the end state already existed, the harness reports `VERIFIED-NO-OP` (exit status 3), and the skill's table says `verified (no-op)`, not `verified`. |
| `setup.sh` | Optional. Puts the fresh system into the state the skill assumes (for example, pkg installed, or no network). The model never does this part. |
| `test-inputs.txt` | Optional. The values of the skill's inputs, given to the model the way a person asking for the task would give them. |
| `reboots` | Optional, empty. The skill may end by scheduling a restart (`shutdown -r +1`); the harness then waits for the machine to come back before running `verify.sh`. |
| `answer.sh` | Required for skills that report something rather than change something (a search, a query). Such a skill always ends by writing a `RESULT:` line; `answer.sh` computes the true `RESULT:` line on the test system without the model, and the model's final message must contain exactly that line. The test inputs must differ from the skill's own examples, so the answer cannot be copied from the text. |

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
