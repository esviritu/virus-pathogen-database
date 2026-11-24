"""Tests for scripts/validate.py.

Every test builds its tables in memory, so nothing is written to disk.

    python3 -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate  # noqa: E402  (imported after the path is set)


def table(*lines: str) -> list[str]:
    """Write a table the way it appears on disk: one string per line."""
    return [line + "\n" for line in lines]


class ParseTableTests(unittest.TestCase):
    def test_hash_header_is_read_and_comment_lines_are_skipped(self):
        header, rows, problems = validate.parse_table(table(
            "#accession\tstart\tend",
            "# a comment",
            "NC_001401.2\t0\t100",
        ), "mask.bed")
        self.assertEqual(header, ["accession", "start", "end"])
        self.assertEqual(rows, [(3, {"accession": "NC_001401.2", "start": "0", "end": "100"})])
        self.assertEqual(problems, [])

    def test_wrong_field_count_is_reported_with_its_line_number(self):
        _, rows, problems = validate.parse_table(table(
            "accession\treason\tissue",
            "NC_001401.2\tvector",
        ), "exclude.tsv")
        self.assertEqual(rows, [])
        self.assertEqual(len(problems), 1)
        self.assertIn("exclude.tsv:2", problems[0])


class SourceTests(unittest.TestCase):
    def rows(self, *data_rows):
        return [(line_number, row) for line_number, row in enumerate(data_rows, start=2)]

    def test_good_rows_pass_and_lengths_are_returned(self):
        problems, lengths = validate.check_sources(self.rows(
            {"Accession": "NC_001401.2", "Organism_Name": "AAV-2", "Length": "4679"},
            {"Accession": "MN908947.3", "Organism_Name": "SARS-CoV-2", "Length": "29903"},
        ), "accessions.tsv")
        self.assertEqual(problems, [])
        self.assertEqual(lengths, {"NC_001401.2": 4679, "MN908947.3": 29903})

    def test_unversioned_accession_is_rejected(self):
        problems, _ = validate.check_sources(self.rows(
            {"Accession": "NC_001401", "Organism_Name": "AAV-2", "Length": "4679"},
        ), "accessions.tsv")
        self.assertEqual(len(problems), 1)
        self.assertIn("version", problems[0])

    def test_duplicate_accession_is_rejected(self):
        row = {"Accession": "NC_001401.2", "Organism_Name": "AAV-2", "Length": "4679"}
        problems, _ = validate.check_sources(self.rows(row, row), "accessions.tsv")
        self.assertEqual(len(problems), 1)
        self.assertIn("duplicate", problems[0])

    def test_length_must_be_a_positive_whole_number(self):
        problems, _ = validate.check_sources(self.rows(
            {"Accession": "NC_001401.2", "Organism_Name": "AAV-2", "Length": "0"},
            {"Accession": "MN908947.3", "Organism_Name": "SARS-CoV-2", "Length": "about 30kb"},
        ), "accessions.tsv")
        self.assertEqual(len(problems), 2)


class ExcludeTests(unittest.TestCase):
    good_row = {"accession": "NC_001401.2", "reason": "vector contamination", "issue": "#3"}

    def test_good_row_passes_and_is_returned_as_excluded(self):
        problems, excluded = validate.check_exclude([(2, self.good_row)], "exclude.tsv", {"NC_001401.2"})
        self.assertEqual(problems, [])
        self.assertEqual(excluded, {"NC_001401.2"})

    def test_accession_not_in_sources_is_rejected(self):
        problems, _ = validate.check_exclude([(2, self.good_row)], "exclude.tsv", {"MN908947.3"})
        self.assertEqual(len(problems), 1)
        self.assertIn("not in sources", problems[0])

    def test_unknown_accessions_are_not_checked_before_sources_exist(self):
        problems, _ = validate.check_exclude([(2, self.good_row)], "exclude.tsv", None)
        self.assertEqual(problems, [])

    def test_reason_and_issue_are_required(self):
        row = {"accession": "NC_001401.2", "reason": "", "issue": "see slack"}
        problems, _ = validate.check_exclude([(2, row)], "exclude.tsv", None)
        self.assertEqual(len(problems), 2)

    def test_unversioned_accession_is_rejected_even_before_sources_exist(self):
        row = dict(self.good_row, accession="NC_001401")
        problems, _ = validate.check_exclude([(2, row)], "exclude.tsv", None)
        self.assertEqual(len(problems), 1)
        self.assertIn("version", problems[0])

    def test_full_issue_urls_are_accepted(self):
        row = dict(self.good_row, issue="https://github.com/esviritu/virus-pathogen-database/issues/3")
        problems, _ = validate.check_exclude([(2, row)], "exclude.tsv", None)
        self.assertEqual(problems, [])


class MaskTests(unittest.TestCase):
    lengths = {"NC_001401.2": 4679}

    def mask_row(self, start, end, accession="NC_001401.2", mask_type="vector"):
        return {"accession": accession, "start": start, "end": end, "type": mask_type,
                "reason": "cloning vector", "issue": "#3"}

    def test_mask_inside_the_genome_passes(self):
        problems = validate.check_mask([(2, self.mask_row("0", "4679"))], "mask.bed", self.lengths, set())
        self.assertEqual(problems, [])

    def test_start_must_come_before_end(self):
        problems = validate.check_mask([(2, self.mask_row("100", "100"))], "mask.bed", self.lengths, set())
        self.assertEqual(len(problems), 1)

    def test_mask_past_the_end_of_the_genome_is_rejected(self):
        problems = validate.check_mask([(2, self.mask_row("4000", "4680"))], "mask.bed", self.lengths, set())
        self.assertEqual(len(problems), 1)
        self.assertIn("4679", problems[0])

    def test_coordinates_must_be_whole_numbers(self):
        problems = validate.check_mask([(2, self.mask_row("-1", "ten"))], "mask.bed", self.lengths, set())
        self.assertEqual(len(problems), 1)

    def test_unversioned_accession_is_rejected_even_before_sources_exist(self):
        row = self.mask_row("0", "10", accession="NC_001401")
        problems = validate.check_mask([(2, row)], "mask.bed", None, set())
        self.assertEqual(len(problems), 1)
        self.assertIn("version", problems[0])

    def test_every_known_mask_type_passes(self):
        for mask_type in validate.MASK_TYPES:
            row = self.mask_row("0", "10", mask_type=mask_type)
            self.assertEqual(validate.check_mask([(2, row)], "mask.bed", self.lengths, set()), [])

    def test_unknown_mask_type_is_rejected_and_the_known_ones_are_listed(self):
        row = self.mask_row("0", "10", mask_type="contamination")
        problems = validate.check_mask([(2, row)], "mask.bed", self.lengths, set())
        self.assertEqual(len(problems), 1)
        self.assertIn("contamination", problems[0])
        self.assertIn("low_complexity", problems[0])

    def test_masking_an_excluded_accession_is_rejected(self):
        problems = validate.check_mask([(2, self.mask_row("0", "10"))], "mask.bed", self.lengths, {"NC_001401.2"})
        self.assertEqual(len(problems), 1)
        self.assertIn("excluded", problems[0])


class RepoTests(unittest.TestCase):
    def test_the_files_committed_in_this_repo_pass(self):
        self.assertEqual(validate.validate_repo(REPO_ROOT), [])


if __name__ == "__main__":
    unittest.main()
