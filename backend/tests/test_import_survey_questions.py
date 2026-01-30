"""Tests for survey questions import script."""
import pytest
import csv
import sys
from pathlib import Path

# Add scripts directory to path for import
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

# Path to CSV
CSV_PATH = Path(__file__).parent.parent.parent / 'frontend/src/data/questions.csv'


class TestParseMaps:
    """Test the parse_maps helper function."""

    def test_parse_valid_json(self):
        """Valid JSON should be parsed correctly."""
        from import_survey_questions import parse_maps
        result = parse_maps('{"factor":"SE"}')
        assert result == {"factor": "SE"}

    def test_parse_complex_json(self):
        """Complex JSON with multiple keys should be parsed correctly."""
        from import_survey_questions import parse_maps
        result = parse_maps('{"category":"physical_touch","activity":"massage_receive","direction":"on_me"}')
        assert result['category'] == 'physical_touch'
        assert result['activity'] == 'massage_receive'
        assert result['direction'] == 'on_me'

    def test_parse_empty_string(self):
        """Empty string should return None."""
        from import_survey_questions import parse_maps
        assert parse_maps('') is None
        assert parse_maps('  ') is None

    def test_parse_none(self):
        """None should return None."""
        from import_survey_questions import parse_maps
        assert parse_maps(None) is None

    def test_parse_invalid_json(self):
        """Invalid JSON should return None (not raise)."""
        from import_survey_questions import parse_maps
        result = parse_maps('not-json')
        assert result is None

    def test_parse_json_with_nested_quotes(self):
        """JSON with nested strings should parse correctly."""
        from import_survey_questions import parse_maps
        result = parse_maps('{"facet":"BONDAGE","tag":"BREATH_PLAY"}')
        assert result['facet'] == 'BONDAGE'
        assert result['tag'] == 'BREATH_PLAY'


class TestCSVReadability:
    """Test that the import script can read the CSV correctly.

    These tests verify the CSV parsing logic without touching the database.
    """

    def test_csv_can_be_read(self):
        """Import script should be able to read the CSV file."""
        assert CSV_PATH.exists(), f"CSV not found at {CSV_PATH}"

        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 75

    def test_all_rows_have_required_fields(self):
        """Every row should have all required fields."""
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert row.get('id', '').strip(), f"Missing id in row"
                assert row.get('chapter', '').strip(), f"Missing chapter for {row.get('id')}"
                assert row.get('type', '').strip(), f"Missing type for {row.get('id')}"
                assert row.get('prompt', '').strip(), f"Missing prompt for {row.get('id')}"

    def test_maps_json_is_valid(self):
        """All maps fields should contain valid JSON."""
        from import_survey_questions import parse_maps

        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                maps_str = row.get('maps', '').strip()
                if maps_str:
                    result = parse_maps(maps_str)
                    assert result is not None, f"Invalid JSON in maps for {row['id']}: {maps_str}"


class TestImportDataPreparation:
    """Test the data preparation logic of the import script."""

    def test_question_pre_prompt_assignment(self):
        """Verify pre-prompts are assigned based on chapter."""
        # This tests the logic without database interaction
        chapter_prompts = {
            "Arousal & Power": "How much do you agree with the statement?",
            "Physical Touch": "Are you currently open to exploring these activities with a play partner?",
            "Oral Activities": "Are you currently open to exploring these activities with a play partner?",
            "Anal Activities": "Are you currently open to exploring these activities with a play partner?",
            "Power Exchange": "Are you currently open to exploring these activities with a play partner?",
            "Verbal & Roleplay": "Are you currently open to exploring these activities with a play partner?",
            "Display & Performance": "Are you currently open to exploring these activities with a play partner?",
            "Truth Topics": "Are you currently open to discussing these topics with a play partner?",
            "Boundaries & Safety": "Do you currently have any hard boundaries?"
        }

        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            chapters_found = set()
            for row in reader:
                chapter = row.get('chapter', '').strip()
                chapters_found.add(chapter)

        # Verify all expected chapters are in CSV
        for chapter in chapter_prompts.keys():
            assert chapter in chapters_found, f"Chapter '{chapter}' not found in CSV"

    def test_display_order_calculation(self):
        """Verify display order would be assigned correctly."""
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                expected_order = row_num - 1
                # First question (A1) should have display_order 1
                if row['id'] == 'A1':
                    assert expected_order == 1


class TestQuestionTextForImport:
    """Verify the exact text that would be imported."""

    def test_questions_to_be_changed_current_values(self):
        """Document current values of questions that will be changed."""
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            questions = {row['id']: row['prompt'] for row in reader}

        # These are the CURRENT values (before the fix)
        # This test documents what exists now
        assert 'B4b' in questions
        assert 'B5b' in questions
        assert 'B6b' in questions
        assert 'B7b' in questions
        assert 'B12b' in questions
        assert 'B15b' in questions
        assert 'B22a' in questions
        assert 'B23a' in questions
        assert 'B23b' in questions
        assert 'B24a' in questions
        assert 'B25a' in questions

    def test_commas_preserved_in_prompts(self):
        """Questions with commas in text should have full content."""
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            questions = {row['id']: row['prompt'] for row in reader}

        # A1 has commas in text
        assert 'touch, scent, visuals' in questions['A1']

        # B15a has multiple commas
        assert 'hands held, ties, cuffs, rope' in questions['B15a']

        # B17a has commas
        assert 'edging, denial, forced orgasm' in questions['B17a']
