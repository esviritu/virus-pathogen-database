# Working in this repo as an agent

This repo holds the recipe for the Virus Pathogen Database (VPD): the source accessions and the
curation decisions applied to them. You work here as a **fixer**. A person files an issue, you
reproduce what they saw, and you propose the change as a pull request. The maintainer
(Mike Tisza, `mtisza1`) judges the science and merges. Your job is that the change is correct,
traceable to its issue, and passes the checks.

## Acting on an issue

1. **Read the issue.** Issues come from the forms in `.github/ISSUE_TEMPLATE/`, so each answer
   sits under a heading named after its field. Done when you can state, for every record, the
   accession with its version, the region or "whole record", and the action asked for.
2. **Confirm a maintainer has agreed on the issue.** With no such reply, stop here and report
   that the issue is waiting on the maintainer.
3. **Reproduce every claim** ([Reproducing](#reproducing)). Done when each claim is confirmed
   against a primary source, or named as one you could not confirm.
4. **Make the change with `scripts/curate.py`**, one run per row
   (`python3 scripts/curate.py --help`). Pass first and last base exactly as the issue gives
   them, counted from 1: the command converts to BED. Done when each run prints `added to`.
5. **Add one line to `CHANGELOG.md`** under **Unreleased**, in the section that fits. The top
   of that file shows the format.
6. **Run both checks.** Done when both pass.

       python3 scripts/validate.py
       python3 -m unittest discover -s tests

7. **Open a pull request** from the template with `Closes #<issue>`. Say what you reproduced,
   how, and what you could not.

When a claim does not reproduce, the tables stay as they are. Your output is a report of what
you ran and what you saw, for the issue.

## Reproducing

**Exclude or mask.** Fetch the record and confirm it is long enough to hold the region:

    https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=<accession>&rettype=fasta&retmode=text

Then confirm what the region is, by the reporter's own method or by aligning the region against
the vector or host they name. Record the tool, the database and the hit.

**Add sequences.** Confirm each accession resolves at NCBI with that exact version and that its
record describes a complete or near-complete genome. Confirm it is absent from VPD: the first
column of `virus_pathogen_database.all_metadata.tsv` in the current release (download in
`README.md`). `sources/accessions.tsv` is not committed yet, so this ends with a report on the
issue and no file change.

**Taxonomy change.** Confirm the proposed name against NCBI Taxonomy for the TaxID given. No
table holds taxonomy yet, so this also ends with a report on the issue and no file change.

## What the checks cannot see

- **`reason` is for a reader who never opens the issue.** Say what the sequence is and where:
  `pUC19 backbone at 5' end`.
- **Evidence comes from the issue or from what you reproduced.** Quote it with its tool and
  database.
- **A record that leaves VPD is excluded.** Use that word. It gets a row in
  `curation/exclude.tsv` and its history stays.
- **Mask or exclude:** mask when the rest of the record is a good genome, exclude when the
  whole record is unreliable.
- **One issue per pull request.** Rows are added at the end; existing rows keep their text and
  order.
- **Stage files by name.** Working files go in `.scratch/` and stay out of commits.

## Maintainer-only

Change these only when a maintainer asks for it in the issue: `build/`, `RELEASING.md`,
release tags, the Zenodo record, `.github/workflows/`, and the rules in `scripts/validate.py`.
A row that fails a check needs fixing; the check stays.

Reads and anything that identifies a patient stay out of the repo and out of issues.
