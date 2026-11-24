# Virus Pathogen Database (VPD)

The reference database [EsViritu](https://github.com/esviritu/EsViritu) maps reads against: curated
human, animal and plant virus genomes with NCBI-derived taxonomy.

This repo holds the **recipe** for VPD: the source accession list, the curation decisions applied
to it and their history, and the build that turns them into a release. The built database is
published on Zenodo.

## Download a release

Current release: **v3.2.4** · [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17716199.svg)](https://doi.org/10.5281/zenodo.17716199)

```bash
mkdir esviritu_DB && cd esviritu_DB
wget https://zenodo.org/records/17716199/files/esviritu_db_v3.2.4.tar.gz
md5sum esviritu_db_v3.2.4.tar.gz   # 24d85c1ec3cbffff12e921d2f39c91b2
tar -xvf esviritu_db_v3.2.4.tar.gz && rm esviritu_db_v3.2.4.tar.gz
```

EsViritu 1.0.0 and later need VPD 3.1.0 or later. [CHANGELOG.md](CHANGELOG.md) lists what changed
in each release.

## What a release contains

| File | Contents |
|---|---|
| `virus_pathogen_database.fna` | Genome sequences, one record per accession |
| `virus_pathogen_database.mmi` | minimap2 index of the above, built with `-x sr` |
| `virus_pathogen_database.all_metadata.tsv` | One row per accession: taxonomy, length, assembly |
| `MANIFEST.yaml` *(from the next release)* | What the release was built from: see [RELEASING.md](RELEASING.md) |

## Repo layout

```
sources/accessions.tsv   the accessions VPD is built from (the table esv_create_taxonomy reads)
curation/exclude.tsv     accessions excluded from the build, each with a reason and an issue
curation/mask.bed        regions hard-masked to N, each with a type, a reason and an issue
build/                   the build: sources + curation -> a release    (being ported, see below)
scripts/curate.py        adds one curation row, correctly formatted
scripts/validate.py      the checks CI runs on every pull request
```

Every curation row links to the issue where it was discussed, so `git blame curation/mask.bed`
tells you why any region is masked.

## Proposing a change

[Open an issue](https://github.com/esviritu/virus-pathogen-database/issues/new/choose). You do not
need git: fill in a form and a maintainer takes it from there.

- **Add sequences**: a virus or genome VPD is missing
- **Exclude or mask**: contamination, vectors, misannotated or low-quality records
- **Taxonomy change**: a name or lineage that is wrong or has changed at NCBI
- **Question or idea**: anything else

[CONTRIBUTING.md](CONTRIBUTING.md) covers both reporting a problem and making the change yourself.
[AGENTS.md](AGENTS.md) has the rules for AI agents working in this repo.

## Building

> **TODO:** `build/` is being ported from the current release process. The first milestone is a
> build that reproduces v3.2.4 exactly. Until then, releases are built by the maintainer.

## Maintainers

Mike Tisza ([@mtisza1](https://github.com/mtisza1)) maintains VPD and signs off on every release.
Curation is open to the community through issues and pull requests.

## Citation

If you use VPD, please cite EsViritu:

> Michael J. Tisza, Shelby R. Simar, Jackie K. Zorz, Sara J. Javornik Cregeen, Anthony W. Maresso.
> **EsViritu is a sensitive and specific profiler for viral pathogen detection and genome recovery
> in metagenomes.** <https://doi.org/10.64898/2026.09.29.755457>
