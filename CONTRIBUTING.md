# Contributing to VPD

Thanks for helping improve VPD. There are two ways to help, and most people only need the first.

- **[Report it](#report-it).** Fill in a form. No git, no files. Someone else makes the change.
- **[Fix it yourself](#fix-it-yourself).** Make the change and open a pull request.

## Report it

1. **[Open an issue](https://github.com/esviritu/virus-pathogen-database/issues/new/choose)** and
   pick the form that fits.

   | Form | Use it when |
   |---|---|
   | Add sequences | a virus or genome is missing from VPD |
   | Exclude or mask | a record, or part of one, is contamination, vector, host sequence or otherwise unreliable |
   | Taxonomy change | a name or lineage is wrong, or has changed at NCBI or ICTV |
   | Question or idea | anything else, including "is this a database problem?" |

2. **Fill in what you can.** Plain language is fine. You do not need to know which file changes.
3. **A maintainer replies on the issue.** They, or someone working with them, make the change. That
   may be an AI agent, and the maintainer reviews whatever it proposes. You may get a follow-up
   question.

Problems with EsViritu itself, not the database, belong in the
[EsViritu repo](https://github.com/esviritu/EsViritu/issues).

### What makes a report easy to act on

Someone else has to see what you saw. The forms ask for this:

- **Add sequences:** the accession, why VPD needs it (a missing species, or a strain the current
  genome misses), and whether it is a complete or near-complete genome.
- **Exclude or mask:** where the region is, how you found it, and what it matches if you know
  (a BLAST hit to a vector, for example). Samples where it caused false positives help.
- **Taxonomy change:** the current name, the correct one, and the NCBI Taxonomy ID or ICTV source.

Please never attach reads or anything that identifies a patient.

### Only need it for your own project?

EsViritu can build a custom database from your own list of accessions, and combine it with VPD.
See [Making custom databases](https://github.com/esviritu/EsViritu/blob/main/docs/custom-database.md).
You can use it today without waiting for a VPD release.

### Proposing a bigger change

Ideas about how VPD is built, organised or released also go in a **Question or idea** issue.
Attach or link the document if there is one.

## Fix it yourself

1. **Start from an issue.** Open one, or pick one that exists, and wait for the maintainer's reply
   there before doing the work, so nobody's effort is wasted.
2. **Fork the repo and make a branch.**
3. **Make the change** with the command for it ([below](#which-change-goes-where)).
4. **Add a line to `CHANGELOG.md`** under **Unreleased**.
5. **Open a pull request** that links the issue. CI checks your rows the same way the build will.
6. **The maintainer reviews and merges.** Merged changes ship in the next release.

Small, single-purpose pull requests are much easier to review than large ones. Ten masks for one
contaminant is one pull request; masks for two unrelated contaminants are two.

### Which change goes where

| I want to... | How | Ends up in |
|---|---|---|
| Exclude a whole record | `scripts/curate.py exclude` | `curation/exclude.tsv` |
| Mask part of a record (vector, adapter, host insert) | `scripts/curate.py mask` | `curation/mask.bed` |
| Add a genome | the issue is as far as this goes for now | `sources/accessions.tsv`, not committed yet |
| Fix a name or lineage | the issue is as far as this goes for now; the maintainer will say where the fix belongs | |

**Exclude or mask?** Mask when the rest of the record is a good genome and only a region is
contaminated: the record keeps its taxonomy and still recruits reads elsewhere. Exclude when the
whole record is unreliable. An excluded record is left out of the build, and its row says why.

### Excluding a record

```bash
python3 scripts/curate.py exclude --accession MN123456.1 \
    --reason "whole record is cloning vector pUC19" --issue 4
```

This adds one row to `curation/exclude.tsv`:

```
accession	reason	issue
MN123456.1	whole record is cloning vector pUC19	#4
```

### Masking a region

Give the first and last base the way BLAST and GenBank show them: counted from 1, with the last
base included. The command converts them for you.

```bash
python3 scripts/curate.py mask --accession NC_001401.2 --first-base 1 --last-base 145 \
    --type vector --reason "pUC19 backbone at 5' end" --issue 4
```

This adds one row to `curation/mask.bed`:

```
#accession	start	end	type	reason	issue
NC_001401.2	0	145	vector	pUC19 backbone at 5' end	#4
```

The file is **BED: 0-based, end-exclusive**, so bases 1–145 are stored as `start 0, end 145`.
Masked bases become `N`, so reads no longer align there.

`--type` says what the region is:

| `type` | The region is |
|---|---|
| `vector` | a cloning vector, adapter or other synthetic sequence |
| `host` | host genome or endogenous sequence, such as a match to the mouse genome |
| `low_complexity` | repeats or low-entropy sequence that recruits reads from anything |

### Reason and issue

Every curation row needs both, and the command will not add a row without them. `--reason` is a
short phrase a future reader will understand without opening the issue. `--issue` is the issue
number, or a full GitHub issue or pull request URL.

### Editing the tables by hand

You can also edit a table directly. Fields are separated by tabs, new rows go at the end, and
existing rows stay as they are so the diff shows only your change. CI runs the same checks
either way.

### Adding a genome

`sources/accessions.tsv` is not committed yet, so an **Add sequences** issue is as far as this goes
for now. It will be the table
[`esv_create_taxonomy`](https://github.com/esviritu/EsViritu/blob/main/docs/custom-database.md)
reads: `Accession` (with its version suffix), `Organism_Name` and `Length` in bp, plus `Assembly`
so the segments of a segmented virus are grouped.

<!-- TODO (Mike): any other inclusion criteria, e.g. complete genomes only, host range. -->

### The changelog line

CI fails a pull request that changes `sources/` or `curation/` without touching `CHANGELOG.md`.
The top of that file shows the format. For a pull request that needs no entry, such as a typo
fix, a maintainer can add the `skip-changelog` label.

### Running the checks yourself

CI runs these on every pull request. Running them first saves a round trip. They need only
Python 3.

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests
```

Each problem is printed as `file:line: what is wrong`.

## AI agents

[AGENTS.md](AGENTS.md) has the rules for an agent working in this repo. A maintainer reviews
everything an agent proposes.

## Releases

Only the maintainer cuts releases. See [RELEASING.md](RELEASING.md).
