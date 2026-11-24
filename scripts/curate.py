#!/usr/bin/env python3
"""Add one curation decision to VPD's tables, correctly formatted.

    python3 scripts/curate.py exclude --accession MN123456.1 \\
        --reason "whole record is cloning vector pUC19" --issue 4

    python3 scripts/curate.py mask --accession NC_001401.2 --first-base 1 --last-base 145 \\
        --type vector --reason "pUC19 backbone at 5' end" --issue 4

Give bases the way BLAST and GenBank show them: counted from 1, with the last base included.
The command converts them to BED for curation/mask.bed, so nobody does that by hand.

After adding the row it runs every check in validate.py. If any check fails, the row is taken
out again, the problems are printed and the exit code is 1. Uses the standard library only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import validate


def issue_reference(issue: str) -> str:
    """Write a bare issue number as '#4'. Anything else is left for the validator to judge."""
    return f"#{issue}" if issue.isdigit() else issue


def exclude_row(accession: str, reason: str, issue: str) -> list[str]:
    """Return the fields of one curation/exclude.tsv row."""
    return [accession, reason, issue_reference(issue)]


def mask_row(accession: str, first_base: int, last_base: int, mask_type: str, reason: str, issue: str) -> list[str]:
    """Return the fields of one curation/mask.bed row.

    BED counts from 0 and leaves the end out, so only the start moves: bases 1-145 counted
    the usual way are start 0, end 145.
    """
    bed_start = first_base - 1
    bed_end = last_base
    return [accession, str(bed_start), str(bed_end), mask_type, reason, issue_reference(issue)]


def text_with_row_added(table_text: str, row: list[str]) -> str:
    """Return the table text with the row as a new last line."""
    if table_text and not table_text.endswith("\n"):
        table_text += "\n"
    return table_text + "\t".join(row) + "\n"


def add_row_and_validate(root: Path, table_path: Path, row: list[str]) -> list[str]:
    """Add the row, run every repo check, and take the row out again if any check fails.

    Returns the problems found. An empty list means the row was added and is still there.
    """
    original_text = table_path.read_text()
    table_path.write_text(text_with_row_added(original_text, row))
    problems = validate.validate_repo(root)
    if problems:
        table_path.write_text(original_text)
    return problems


def parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=Path("."), help="repo checkout to change (default: .)")
    commands = parser.add_subparsers(dest="command", required=True)
    exclude_parser = commands.add_parser("exclude", help="leave a whole record out of the build")
    mask_parser = commands.add_parser("mask", help="hide part of a record, keeping the rest")
    for command_parser in (exclude_parser, mask_parser):
        command_parser.add_argument("--accession", required=True, help="with its version suffix, e.g. NC_001401.2")
        command_parser.add_argument("--reason", required=True,
                                    help="a short phrase a future reader understands without opening the issue")
        command_parser.add_argument("--issue", required=True,
                                    help="the issue number, e.g. 4, or a full GitHub issue or PR URL")
    mask_parser.add_argument("--first-base", type=int, required=True, help="first base to mask, counted from 1")
    mask_parser.add_argument("--last-base", type=int, required=True,
                             help="last base to mask, counted from 1 and included in the mask")
    mask_parser.add_argument("--type", required=True, choices=validate.MASK_TYPES, help="what the region is")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(argv)

    if arguments.command == "exclude":
        table_path = arguments.root / "curation" / "exclude.tsv"
        row = exclude_row(arguments.accession, arguments.reason, arguments.issue)
    else:
        if arguments.first_base < 1:
            print("first base must be 1 or more: bases are counted from 1, as BLAST and GenBank show them")
            return 1
        table_path = arguments.root / "curation" / "mask.bed"
        row = mask_row(arguments.accession, arguments.first_base, arguments.last_base,
                       arguments.type, arguments.reason, arguments.issue)

    problems = add_row_and_validate(arguments.root, table_path, row)
    if problems:
        for problem in problems:
            print(problem)
        print(f"nothing was added to {table_path}")
        return 1
    print(f"added to {table_path}:")
    print("\t".join(row))
    return 0


if __name__ == "__main__":
    sys.exit(main())
