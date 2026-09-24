# FreeBSD Handbook skills

Step-by-step skills for everything in the
[FreeBSD Handbook](https://docs.freebsd.org/en/books/handbook/). Each skill
does exactly one task and is written so that the least capable reader, human
or model, gets it right.

Every skill is **tested before it is written**:

- Each step is run for real on a fresh FreeBSD system, on every release in the
  matrix below. The skill records what actually happened, not what the text
  says should happen.
- A small model then follows the finished skill on a fresh system, with no
  other context. If it fails, the skill is rewritten until it passes.
- Anything that could not be run, for example because it needs hardware such
  as a wireless card or a printer, is marked **not verified**. It is never
  presented as tested.

## Releases covered

Every FreeBSD release from 14.0 onward, plus the development branch:

| Release | Status |
|---|---|
| 16.0-CURRENT | development (results record the snapshot date) |
| 15.1-RELEASE | supported until 2027-03-31 |
| 15.0-RELEASE | supported until 2026-09-30 |
| 14.5-RELEASE | supported until 2027-06-30 |
| 14.4-RELEASE | supported until 2026-12-31 |
| 14.3, 14.2, 14.1, 14.0-RELEASE | end of life |

Information for a release is **never removed**. When a release reaches end of
life, its steps and results stay in every skill, marked EoL, so that someone
running it years from now still has what worked for them. New releases are
added as they are published.

## Layout

    skills/<chapter>/<task>/SKILL.md   one task per skill
    docs/TEMPLATE.md                   the format every skill follows
    COVERAGE.md                        progress, chapter by chapter
    tools/                             test machinery

## Using a skill

1. Find the chapter under `skills/`, the same names as the Handbook's chapters.
2. Open `SKILL.md` and follow the steps in order. Each step shows the exact
   command and the output you should see.
3. Check the "Release results" table first. It shows whether the skill was
   verified on your release.

## Status

This is a work in progress, done chapter by chapter. See
[COVERAGE.md](COVERAGE.md) for what is finished.

## Licence

The skills are derived from the FreeBSD Handbook, copyright The FreeBSD
Project, and are redistributed under its licence. Original material is
BSD-2-Clause. See [LICENSE](LICENSE). This project is not affiliated with or
endorsed by the FreeBSD Project.
