#!/usr/bin/env python3
"""Check VPD's source and curation tables before a human has to.

CI runs this on every pull request so the maintainer reviews only the science, not the
formatting. It uses the standard library only, so CI needs no environment.

    python3 scripts/validate.py              # check the checkout you are in
    python3 scripts/validate.py --root DIR   # check another checkout

Exits 0 when everything passes. Otherwise prints one line per problem, as
`file:line: what is wrong`, and exits 1.

What it checks:
    sources/accessions.tsv   required columns; versioned, unique accessions; positive lengths
    curation/exclude.tsv     versioned accessions that exist in sources; a reason and an issue
    curation/mask.bed        versioned accessions; coordinates are inside the genome; the type
                             is a known one; the record is not also excluded

Until sources/accessions.tsv is committed, the checks that need it are skipped.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from pathlib import Path

# NCBI accession with its version suffix, e.g. NC_001401.2 or MN908947.3. EsViritu needs the
# FASTA IDs to match the metadata exactly, version included, so an unversioned accession is a
# mistake. Every one of the 30,907 accessions in VPD v3.2.4 matches this pattern.
VERSIONED_ACCESSION = re.compile(r"^[A-Z]{1,6}_?[0-9]+\.[0-9]+$")

# Where a curation decision was discussed: "#12" or a full GitHub issue or pull request URL.
ISSUE_REFERENCE = re.compile(r"^(#[0-9]+|https://github\.com/\S+/(issues|pull)/[0-9]+)$")

# sources/ uses the column names esv_create_taxonomy reads; curation/ uses its own.
SOURCE_COLUMNS = ["Accession", "Organism_Name", "Length"]
EXCLUDE_COLUMNS = ["accession", "reason", "issue"]
MASK_COLUMNS = ["accession", "start", "end", "type", "reason", "issue"]

# What a masked region is. `type` sits in the fourth column, which BED tools read as the
# feature's name, so a genome browser labels each mask with it.
#   vector          cloning vector, adapter or other synthetic sequence
#   host            host genome or endogenous sequence, e.g. a match to the mouse genome
#   low_complexity  repeats and low-entropy sequence that recruit reads from anything
MASK_TYPES = ["vector", "host", "low_complexity"]

NumberedRow = tuple[int, dict[str, str]]


def parse_table(lines: Iterable[str], label: str) -> tuple[list[str], list[NumberedRow], list[str]]:
    """Split a tab-separated table into its header, its numbered rows and any parse problems.

    The first non-blank line is the header. A leading '#' on it is dropped: that is how
    mask.bed carries column names that BED tools will skip as a comment. Later lines starting
    with '#' are comments, and blank lines are ignored. Rows keep their line number in the
    file so problems can point at them.
    """
    header: list[str] = []
    rows: list[NumberedRow] = []
    problems: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        line = line.rstrip("\r\n")
        if not line.strip():
            continue
        if not header:
            header = line.lstrip("#").split("\t")
            continue
        if line.startswith("#"):
            continue
        values = line.split("\t")
        if len(values) != len(header):
            problems.append(f"{label}:{line_number}: expected {len(header)} tab-separated fields, "
                            f"found {len(values)}")
            continue
        rows.append((line_number, dict(zip(header, values))))
    return header, rows, problems


def check_header(header: list[str], required_columns: list[str], label: str) -> list[str]:
    """Report any required column the header is missing."""
    missing = [column for column in required_columns if column not in header]
    return [f"{label}: missing column(s): {', '.join(missing)}"] if missing else []


def check_accession(accession: str, where: str) -> list[str]:
    """Report an accession that lacks its version suffix.

    This is checked in every table, so a curation row is held to it even before
    sources/accessions.tsv exists to compare against.
    """
    if VERSIONED_ACCESSION.match(accession):
        return []
    return [f"{where}: accession '{accession}' needs its version suffix, e.g. NC_001401.2"]


def check_sources(rows: list[NumberedRow], label: str) -> tuple[list[str], dict[str, int]]:
    """Check the source accession table and return each accession's length.

    The lengths let the mask check confirm a region lies inside its genome.
    """
    problems: list[str] = []
    lengths: dict[str, int] = {}
    seen_accessions: set[str] = set()
    for line_number, row in rows:
        where = f"{label}:{line_number}"
        accession = row["Accession"]
        problems += check_accession(accession, where)
        if accession in seen_accessions:
            problems.append(f"{where}: duplicate accession '{accession}'")
        seen_accessions.add(accession)
        length = row["Length"]
        if length.isdigit() and int(length) > 0:
            lengths[accession] = int(length)
        else:
            problems.append(f"{where}: Length '{length}' must be a positive whole number")
    return problems, lengths


def check_reason_and_issue(row: dict[str, str], where: str) -> list[str]:
    """Every curation decision says why, and links to where it was discussed."""
    problems = []
    if not row["reason"].strip():
        problems.append(f"{where}: reason is empty")
    if not ISSUE_REFERENCE.match(row["issue"].strip()):
        problems.append(f"{where}: issue '{row['issue']}' should be '#<number>' or a GitHub issue/PR URL")
    return problems


def check_exclude(rows: list[NumberedRow], label: str,
                  known_accessions: set[str] | None) -> tuple[list[str], set[str]]:
    """Check the exclude list and return the accessions it removes.

    known_accessions is None until sources/accessions.tsv exists; the "is it in sources"
    check is skipped until then.
    """
    problems: list[str] = []
    excluded: set[str] = set()
    for line_number, row in rows:
        where = f"{label}:{line_number}"
        accession = row["accession"]
        problems += check_accession(accession, where)
        if accession in excluded:
            problems.append(f"{where}: '{accession}' is already excluded above")
        if known_accessions is not None and accession not in known_accessions:
            problems.append(f"{where}: '{accession}' is not in sources/accessions.tsv")
        problems += check_reason_and_issue(row, where)
        excluded.add(accession)
    return problems, excluded


def check_mask(rows: list[NumberedRow], label: str,
               lengths: dict[str, int] | None, excluded: set[str]) -> list[str]:
    """Check the mask regions.

    Coordinates are BED: 0-based, end-exclusive. Masking bases 1-100 of a genome, counted
    the usual 1-based way, is start 0, end 100.
    """
    problems: list[str] = []
    for line_number, row in rows:
        where = f"{label}:{line_number}"
        accession = row["accession"]
        problems += check_accession(accession, where)
        if accession in excluded:
            problems.append(f"{where}: '{accession}' is excluded, so masking it has no effect")
        start, end = row["start"], row["end"]
        if not (start.isdigit() and end.isdigit()):
            problems.append(f"{where}: start '{start}' and end '{end}' must be whole numbers >= 0")
        elif int(start) >= int(end):
            problems.append(f"{where}: start {start} must be less than end {end}")
        elif lengths is not None:
            if accession not in lengths:
                problems.append(f"{where}: '{accession}' is not in sources/accessions.tsv")
            elif int(end) > lengths[accession]:
                problems.append(f"{where}: end {end} is past the end of '{accession}' "
                                f"({lengths[accession]} bp)")
        if row["type"] not in MASK_TYPES:
            problems.append(f"{where}: type '{row['type']}' must be one of: {', '.join(MASK_TYPES)}")
        problems += check_reason_and_issue(row, where)
    return problems


def load_table(path: Path, required_columns: list[str]) -> tuple[list[NumberedRow] | None, list[str]]:
    """Read and parse one table. Rows are None when the header is unusable."""
    label = str(path)
    with path.open() as handle:
        header, rows, problems = parse_table(handle, label)
    header_problems = check_header(header, required_columns, label)
    if header_problems:
        return None, problems + header_problems
    return rows, problems


def validate_repo(root: Path) -> list[str]:
    """Run every check against a checkout and return all problems found."""
    problems: list[str] = []
    sources_path = root / "sources" / "accessions.tsv"
    exclude_path = root / "curation" / "exclude.tsv"
    mask_path = root / "curation" / "mask.bed"

    lengths: dict[str, int] | None = None
    if sources_path.exists():
        source_rows, source_problems = load_table(sources_path, SOURCE_COLUMNS)
        problems += source_problems
        if source_rows is not None:
            row_problems, lengths = check_sources(source_rows, str(sources_path))
            problems += row_problems
    else:
        print(f"note: {sources_path} is not committed yet; skipping the checks that need it")

    excluded: set[str] = set()
    for required_path in (exclude_path, mask_path):
        if not required_path.exists():
            problems.append(f"{required_path}: missing (commit it with just its header line)")
    if exclude_path.exists():
        exclude_rows, exclude_problems = load_table(exclude_path, EXCLUDE_COLUMNS)
        problems += exclude_problems
        if exclude_rows is not None:
            known_accessions = set(lengths) if lengths is not None else None
            row_problems, excluded = check_exclude(exclude_rows, str(exclude_path), known_accessions)
            problems += row_problems
    if mask_path.exists():
        mask_rows, mask_problems = load_table(mask_path, MASK_COLUMNS)
        problems += mask_problems
        if mask_rows is not None:
            problems += check_mask(mask_rows, str(mask_path), lengths, excluded)
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=Path("."), help="repo checkout to check (default: .)")
    arguments = parser.parse_args(argv)

    problems = validate_repo(arguments.root)
    for problem in problems:
        print(problem)
    print(f"{len(problems)} problem(s) found" if problems else "all checks passed")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
