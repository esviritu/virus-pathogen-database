# Releasing VPD

The maintainer cuts every release. This is the checklist, kept short on purpose.

> **Proposal, for Mike to confirm or change.** The versioning and manifest below are a starting
> point, not a decision.

## Versioning

VPD uses `MAJOR.MINOR.PATCH`:

| Bump | When | Example |
|---|---|---|
| MAJOR | the file contract changes, so EsViritu has to change too | a new metadata column EsViritu reads |
| MINOR | records are added or excluded | new genomes, exclusions |
| PATCH | records are kept but edited | masks, taxonomy fixes |

## Checklist

1. `CHANGELOG.md`: rename **Unreleased** to the new version and date, and start a fresh
   **Unreleased** above it.
2. Build. <!-- TODO: the command, once build/ is ported. -->
3. Write `MANIFEST.yaml` into the release folder (below).
4. Spot-check: run EsViritu on one known-positive sample against the new build.
5. Tag the commit: `git tag v3.3.0 && git push origin v3.3.0`.
6. Upload the tarball as a new version of the
   [Zenodo record](https://doi.org/10.5281/zenodo.17716199) so the concept DOI keeps resolving
   to the latest.
7. Update the version, URL and md5 in `README.md`, and in EsViritu's install docs.

## `MANIFEST.yaml`

Records what a release was built from, so a result can be traced to its inputs.

```yaml
# Example values. The build should write this file, not a person.
vpd_version: 3.3.0
git_commit: <full SHA of the tagged commit>
built: 2026-12-01
records: 30907
taxonomy:
  # NCBI keeps dated snapshots in pub/taxonomy/taxdump_archive/. Building from one of those
  # rather than the live taxdump makes a release reproducible, and an NCBI rename traceable.
  taxdump: taxdmp_2026-11-01.zip
  taxdump_md5: <md5>
  accession2taxid: nucl_gb.accession2taxid.gz
  accession2taxid_downloaded: 2026-11-15
  accession2taxid_md5: <md5>
tools:
  esviritu: 1.3.5      # for esv_create_taxonomy
  minimap2: 2.28
  seqkit: 2.8.2
```
