"""Tests for survey questions CSV parsing and structure."""
import pytest
import csv
from pathlib import Path

# Path to CSV relative to backend root
CSV_PATH = Path(__file__).parent.parent.parent / 'frontend/src/data/questions.csv'


class TestCSVStructure:
    """Verify CSV file structure and parsing."""

    def test_csv_file_exists(self):
        """CSV file should exist at expected location."""
        assert CSV_PATH.exists(), f"CSV not found at {CSV_PATH}"

    def test_csv_has_required_columns(self):
        """CSV should have all required columns."""
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            required = {'id', 'chapter', 'type', 'prompt', 'options', 'maps'}
            assert required.issubset(set(reader.fieldnames)), \
                f"Missing columns: {required - set(reader.fieldnames)}"

    def test_csv_question_count(self):
        """CSV should have expected number of questions."""
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        # 75 questions total (A1-A16, B section pairs and singles, C1)
        assert len(rows) == 75, f"Expected 75 questions, got {len(rows)}"

    def test_all_questions_have_ids(self):
        """Every question should have a non-empty ID."""
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=2):
                assert row['id'].strip(), f"Row {i} has empty ID"

    def test_all_questions_have_prompts(self):
        """Every question should have a non-empty prompt."""
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert row['prompt'].strip(), f"Question {row['id']} has empty prompt"

    def test_all_questions_have_chapters(self):
        """Every question should have a non-empty chapter."""
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert row['chapter'].strip(), f"Question {row['id']} has empty chapter"


class TestCSVCommaHandling:
    """Verify questions with commas are parsed correctly."""

    @pytest.fixture
    def questions(self):
        """Load all questions from CSV."""
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return {row['id']: row for row in reader}

    def test_a1_commas_parsed_correctly(self, questions):
        """A1 has commas in 'touch, scent, visuals' - should be fully preserved."""
        prompt = questions['A1']['prompt']
        assert 'touch, scent, visuals' in prompt, \
            f"A1 comma content not preserved: {prompt}"

    def test_b15a_commas_parsed_correctly(self, questions):
        """B15a has commas in 'hands held, ties, cuffs, rope' - should be fully preserved."""
        prompt = questions['B15a']['prompt']
        assert 'hands held, ties, cuffs, rope' in prompt, \
            f"B15a comma content not preserved: {prompt}"

    def test_b17a_commas_parsed_correctly(self, questions):
        """B17a has commas in 'edging, denial, forced orgasm' - should be fully preserved."""
        prompt = questions['B17a']['prompt']
        assert 'edging, denial, forced orgasm' in prompt, \
            f"B17a comma content not preserved: {prompt}"

    def test_parentheticals_preserved(self, questions):
        """Parenthetical content should be fully preserved."""
        # Check some questions with parentheticals
        assert '(on me)' in questions['B3a']['prompt'], "B3a parenthetical missing"
        assert '(I do)' in questions['B3b']['prompt'], "B3b parenthetical missing"
        assert '(receiving)' in questions['B1a']['prompt'].lower(), "B1a parenthetical missing"
        assert '(giving)' in questions['B1b']['prompt'].lower(), "B1b parenthetical missing"


class TestQuestionIDPatterns:
    """Verify question ID patterns are consistent."""

    @pytest.fixture
    def questions(self):
        """Load all questions from CSV."""
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return {row['id']: row for row in reader}

    def test_section_a_questions_exist(self, questions):
        """Section A should have questions A1-A16."""
        for i in range(1, 17):
            qid = f'A{i}'
            assert qid in questions, f"Missing question {qid}"

    def test_paired_questions_have_both_variants(self, questions):
        """Questions with a/b variants should have both."""
        paired_questions = [
            'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10',
            'B11', 'B12', 'B13', 'B14', 'B15', 'B16', 'B17', 'B18',
            'B22', 'B23', 'B24', 'B25'
        ]
        for base in paired_questions:
            assert f'{base}a' in questions, f"Missing {base}a"
            assert f'{base}b' in questions, f"Missing {base}b"

    def test_non_paired_questions_exist(self, questions):
        """Non-paired B section questions should exist."""
        non_paired = ['B19', 'B20', 'B21', 'B26', 'B27', 'B28',
                      'B29', 'B30', 'B31', 'B32', 'B33', 'B34', 'B35', 'B36']
        for qid in non_paired:
            assert qid in questions, f"Missing question {qid}"

    def test_boundary_question_exists(self, questions):
        """C1 boundary question should exist."""
        assert 'C1' in questions, "Missing C1 boundary question"
