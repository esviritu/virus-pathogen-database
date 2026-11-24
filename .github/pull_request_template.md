Closes #

## What this changes

<!-- One or two sentences. How many records, and in which file. -->

## What was checked

<!-- How the claim in the issue was reproduced: tool, database, hit. Say so if part of it could not be. -->

## Checklist

- [ ] The linked issue has the evidence and a maintainer has replied on it
- [ ] Rows were added with `scripts/curate.py`, or hand-written masks use BED coordinates (0-based start, end-exclusive)
- [ ] Every new curation row has a `reason` and an `issue`
- [ ] A line was added to `CHANGELOG.md` under **Unreleased**
- [ ] `python3 scripts/validate.py` passes locally
