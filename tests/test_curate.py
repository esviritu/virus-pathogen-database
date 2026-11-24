"""Tests for scripts/curate.py.

Each test runs the command against a throwaway checkout: a folder holding just the two
curation tables. The folder is created next to this file and removed when the test ends, so
nothing is written to the system temp folder.

    python3 -m unittest discover -s tests -v
"""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import curate  # noqa: E402  (imported after the path is set)

EXCLUDE_HEADER = "accession\treason\tissue\n"
MASK_HEADER = "#accession\tstart\tend\ttype\treason\tissue\n"


class CurateTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(temporary_directory.cleanup)
        self.checkout = Path(temporary_directory.name)
        (self.checkout / "curation").mkdir()
        self.exclude_path = self.checkout / "curation" / "exclude.tsv"
        self.mask_path = self.checkout / "curation" / "mask.bed"
        self.exclude_path.write_text(EXCLUDE_HEADER)
        self.mask_path.write_text(MASK_HEADER)

    def run_curate(self, *arguments: str) -> int:
        """Run the command against the throwaway checkout and return its exit code."""
        with contextlib.redirect_stdout(io.StringIO()):
            return curate.main(["--root", str(self.checkout), *arguments])

    def mask(self, first_base: str, last_base: str, accession: str = "NC_001401.2",
             reason: str = "pUC19 backbone at 5' end", issue: str = "4") -> int:
        return self.run_curate("mask", "--accession", accession, "--first-base", first_base,
                               "--last-base", last_base, "--type", "vector", "--reason", reason, "--issue", issue)

    def test_mask_converts_first_and_last_base_to_bed_coordinates(self):
        exit_code = self.mask("1", "145")
        self.assertEqual(exit_code, 0)
        self.assertEqual(self.mask_path.read_text(),
                         MASK_HEADER + "NC_001401.2\t0\t145\tvector\tpUC19 backbone at 5' end\t#4\n")

    def test_masking_a_single_base_gives_a_one_base_bed_interval(self):
        self.mask("10", "10")
        self.assertEqual(self.mask_path.read_text().splitlines()[1].split("\t")[1:3], ["9", "10"])

    def test_exclude_adds_a_row_with_the_reason_and_issue(self):
        exit_code = self.run_curate("exclude", "--accession", "MN123456.1",
                                    "--reason", "whole record is cloning vector pUC19", "--issue", "4")
        self.assertEqual(exit_code, 0)
        self.assertEqual(self.exclude_path.read_text(),
                         EXCLUDE_HEADER + "MN123456.1\twhole record is cloning vector pUC19\t#4\n")

    def test_issue_url_is_kept_as_given(self):
        issue_url = "https://github.com/esviritu/virus-pathogen-database/issues/4"
        self.mask("1", "145", issue=issue_url)
        self.assertEqual(self.mask_path.read_text().splitlines()[1].split("\t")[-1], issue_url)

    def test_row_goes_on_its_own_line_when_the_table_has_no_final_newline(self):
        self.mask_path.write_text(MASK_HEADER.rstrip("\n"))
        self.mask("1", "145")
        self.assertEqual(len(self.mask_path.read_text().splitlines()), 2)

    def test_first_base_must_be_one_or_more(self):
        exit_code = self.mask("0", "145")
        self.assertEqual(exit_code, 1)
        self.assertEqual(self.mask_path.read_text(), MASK_HEADER)

    def test_last_base_before_first_base_is_refused_and_nothing_is_written(self):
        exit_code = self.mask("145", "1")
        self.assertEqual(exit_code, 1)
        self.assertEqual(self.mask_path.read_text(), MASK_HEADER)

    def test_reason_containing_a_tab_is_refused_and_nothing_is_written(self):
        exit_code = self.mask("1", "145", reason="vector\tbackbone")
        self.assertEqual(exit_code, 1)
        self.assertEqual(self.mask_path.read_text(), MASK_HEADER)

    def test_masking_an_excluded_record_is_refused_and_nothing_is_written(self):
        self.run_curate("exclude", "--accession", "NC_001401.2", "--reason", "whole record is vector", "--issue", "4")
        exit_code = self.mask("1", "145")
        self.assertEqual(exit_code, 1)
        self.assertEqual(self.mask_path.read_text(), MASK_HEADER)


if __name__ == "__main__":
    unittest.main()
