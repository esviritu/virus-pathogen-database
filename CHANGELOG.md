# Changelog

All notable changes to VPD. Every pull request that touches `sources/` or `curation/` adds a line
under **Unreleased**; CI checks for it. At release time the maintainer renames that heading to the
new version.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning is described
in [RELEASING.md](RELEASING.md).

Each entry says what changed, how many records it touches, and links the issue or PR:

```
- Masked vector sequence in 12 records ([#4](https://github.com/esviritu/virus-pathogen-database/issues/4))
```

## [Unreleased]

### Added

### Excluded

### Masked

### Taxonomy

### Build

- Repository created: CI validates `sources/` and `curation/` on every pull request.
- `scripts/curate.py` adds exclude and mask rows, converting 1-based coordinates to BED.

## [3.2.4]

Baseline: the last release built before this repo existed. 30,907 accessions.
[Zenodo](https://doi.org/10.5281/zenodo.17716199).

<!-- TODO (Mike): earlier versions, if you want them recorded here. Even one line each helps. -->
