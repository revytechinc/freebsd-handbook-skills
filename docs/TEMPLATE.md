# Skill template

Every skill in `skills/` follows this template exactly. It is written for the
least capable model that might read it: nothing is left to inference, every
command is complete, and every step says what success looks like.

Copy everything from the `---` line down into
`skills/<chapter>/<task>/SKILL.md` and fill it in.

## Rules for writing a skill

1. **One task per skill.** "Install a package" and "remove a package" are two
   skills. If a step says "then, if you also want X", X is its own skill.
2. **Every command is complete and copy-pasteable.** No `<placeholders>` inside a
   command, unless the Inputs table defines the placeholder and says exactly
   what to substitute. Inputs are pasted into root commands, so the skill
   states the characters each input may contain and says to stop if it
   contains anything else. An Undo removes only what the skill created, never
   a whole user-supplied path.
3. **Every command is followed by what to expect.** Give the exact output, or
   the one line that must appear, and what to do if it does not.
4. **No "edit the file".** Every file change is made by a command (`sysrc`,
   `printf ... >>`, `sed -i ''`) and checked by a command.
5. **Decisions are tables, not prose.** "If the output contains A, go to step 5.
   If it contains B, go to step 7. Otherwise stop and report."
6. **Version differences are a lookup.** Step 1 always identifies the release,
   and any step that differs by release has a table keyed on that value. Never
   write "on newer versions".
7. **Nothing in a skill is untested.** Each step was run on every release marked
   `verified` in the Release results table. Anything that could not be run is
   listed under "Not verified", with the reason.
8. **Information is never deleted.** When a release reaches end of life, its row
   and its release-specific steps stay and are marked `(EoL <date>)`.
9. **No real infrastructure, no personal data.** Addresses come only from the
   documentation ranges, which are never routed on the internet: IPv4
   `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24` (RFC 5737); IPv6
   `2001:db8::/32` (RFC 3849) for simple examples, and `3fff::/20` (RFC 9637)
   when an example needs large or several prefixes. MAC addresses come from
   `00:00:5e:00:53:00`-`ff` (RFC 7042). Names use `example.org`. No real
   people's names, e-mail addresses, hostnames or public addresses.
   `tools/check-public.py` checks this: run it before every commit, and a
   GitHub Actions job runs it again on every push and pull request.
10. **Plain words.** Short sentences. Define every term the first time it is
    used. Do not assume the reader knows FreeBSD.

---

```markdown
---
name: <chapter>-<task>              # kebab-case, unique across the repo
description: <one sentence: what this does and when to use it>
handbook: <chapter>/#<anchor>       # the Handbook section this comes from
handbook_commit: <freebsd-doc commit the skill was written against>
---

# <Task title>

## What this does

<Two or three sentences. What the reader will have when finished.>

## Before you start

- You need: <root / a user in wheel / network access / a spare disk ...>
- This changes: <files, services, packages it touches>
- Time: <rough time>
- Risk: <none / reversible / DESTRUCTIVE: erases data on DISK>

## Inputs

| Name | Meaning | Example |
|---|---|---|
| `PKG` | name of the package to install | `nginx` |

## Step 1: Identify the release

Run:

    freebsd-version -u

Expected: one line like `15.1-RELEASE`, `14.4-RELEASE-p3` or `16.0-CURRENT`.
Write down the part before the first `-` plus the word after it, e.g.
`15.1-RELEASE`. Steps below that differ by release use this value.

## Step 2: <verb> <object>

Run:

    <command>

Expected output (exactly, or containing this line):

    <output>

| If you see | Do this |
|---|---|
| the expected output | go to step 3 |
| `<specific error>` | <specific fix>, then repeat step 2 |
| anything else | stop, and report the full output |

## Step N: Verify

Run:

    <command that proves the task worked>

Expected:

    <output>

If this does not match, the task did not succeed. Do not continue: go to
"Undo".

## Undo

<Exact commands that return the system to how it was before step 2.>

## Release results

| Release | Result | Tested (UTC) | Notes |
|---|---|---|---|
| 16.0-CURRENT | not verified | | |
| 15.1-RELEASE | not verified | | |
| 15.0-RELEASE | not verified | | |
| 14.5-RELEASE | not verified | | |
| 14.4-RELEASE | not verified | | |
| 14.3-RELEASE (EoL) | not verified | | |
| 14.2-RELEASE (EoL) | not verified | | |
| 14.1-RELEASE (EoL) | not verified | | |
| 14.0-RELEASE (EoL) | not verified | | |

Every row starts as `not verified`: a row only changes after a real test run,
so an unedited row can never claim a pass. For 16.0-CURRENT, the Tested column
also records the snapshot's build date.

Result is one of: `verified` (every step was run and the Verify step passed),
`verified (no-op)` (the end state already existed on that release before the
run; confirm from the command log that the skill detected this and made no
changes),
`differs` (it works, with the release-specific steps noted),
`fails` (does not work on that release; the Notes say why),
`not verified` (could not be run; the Notes say why).

## Weak-model check

<date>: claude-haiku-4-5 followed this skill with no other context on
<releases>: <pass / fail and what was changed>.

## Not verified

<Anything in the Handbook section that could not be run, and why: for example,
"needs a physical wireless card". If everything was run, write "Nothing.">

## Source

FreeBSD Handbook, "<section title>",
https://docs.freebsd.org/en/books/handbook/<chapter>/#<anchor>
```
