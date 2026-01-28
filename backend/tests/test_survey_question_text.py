"""Regression tests for survey question text content.

These tests verify specific question prompts match expected values.
They lock in the expected text after phrasing standardization changes.

IMPORTANT: These tests expect the UPDATED text after the phrasing fixes.
They will FAIL before the CSV is updated, and PASS after.
"""
import pytest
import csv
from pathlib import Path

CSV_PATH = Path(__file__).parent.parent.parent / 'frontend/src/data/questions.csv'


@pytest.fixture
def questions():
    """Load all questions from CSV."""
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return {row['id']: row['prompt'] for row in reader}


class TestPhrasingConsistencyFixes:
    """Tests for the phrasing consistency fixes.

    These tests verify the question text AFTER the planned changes:
    - B4b, B6b, B7b: "I deliver" -> "I do"
    - B5b: "on partner's genitals" -> "on genitals"
    - B12b: Add examples (chest, neck, ears, inner thighs, etc.)
    - B15b: Add examples (hands held, ties, cuffs, rope)
    - B22a: "Receiving/following" -> "Following"
    - B23a: Simplified format
    - B23b: Simplified format
    - B24a: "(me performing)" -> "(I perform)"
    - B25a: "(me)" -> "(I perform)"
    """

    def test_b4b_uses_i_do(self, questions):
        """B4b should use '(I do)' not '(I deliver)'."""
        assert questions['B4b'] == 'Spanking - moderate (I do).'

    def test_b5b_simplified(self, questions):
        """B5b should say 'on genitals' not 'on partner's genitals'."""
        assert questions['B5b'] == 'Using hands/fingers on genitals (I do).'

    def test_b6b_uses_i_do(self, questions):
        """B6b should use '(I do)' not '(I deliver)'."""
        assert questions['B6b'] == 'Spanking - hard (I do).'

    def test_b7b_uses_i_do(self, questions):
        """B7b should use '(I do)' not '(I deliver)'."""
        assert questions['B7b'] == 'Slapping (face or body) (I do).'

    def test_b12b_has_examples(self, questions):
        """B12b should include body part examples like B12a."""
        expected = 'Oral stimulation on other body parts - chest, neck, ears, inner thighs, etc. (I do).'
        assert questions['B12b'] == expected

    def test_b15b_has_examples(self, questions):
        """B15b should include restraint examples like B15a."""
        expected = 'Restraining partner (hands held, ties, cuffs, rope) (I do).'
        assert questions['B15b'] == expected

    def test_b22a_simplified(self, questions):
        """B22a should say 'Following' not 'Receiving/following'."""
        expected = 'Following commands during intimate play (I follow).'
        assert questions['B22a'] == expected

    def test_b23a_simplified_format(self, questions):
        """B23a should have simplified parenthetical format."""
        expected = 'Begging or pleading (me doing the begging).'
        assert questions['B23a'] == expected

    def test_b23b_simplified_format(self, questions):
        """B23b should have simplified parenthetical format."""
        expected = 'Begging or pleading (hearing my partner beg).'
        assert questions['B23b'] == expected

    def test_b24a_uses_i_perform(self, questions):
        """B24a should use '(I perform)' not '(me performing)'."""
        expected = 'Stripping or undressing slowly (I perform).'
        assert questions['B24a'] == expected

    def test_b25a_uses_i_perform(self, questions):
        """B25a should use '(I perform)' not '(me)'."""
        expected = 'Being watched during solo pleasure (I perform).'
        assert questions['B25a'] == expected


class TestUnchangedQuestions:
    """Verify questions that should NOT change remain correct."""

    def test_b1a_unchanged(self, questions):
        """B1a should remain as-is (receiving pattern is fine)."""
        assert questions['B1a'] == 'Massage (receiving).'

    def test_b1b_unchanged(self, questions):
        """B1b should remain as-is (giving pattern is fine)."""
        assert questions['B1b'] == 'Massage (giving).'

    def test_b3a_unchanged(self, questions):
        """B3a should remain as-is (on me pattern is fine)."""
        assert questions['B3a'] == 'Biting or scratching - moderate (on me).'

    def test_b3b_unchanged(self, questions):
        """B3b should remain as-is (I do pattern is fine)."""
        assert questions['B3b'] == 'Biting or scratching - moderate (I do).'

    def test_b16b_already_correct(self, questions):
        """B16b should already say '(I do)'."""
        assert questions['B16b'] == 'Blindfolding or sensory deprivation (I do).'

    def test_b17b_acceptable_as_is(self, questions):
        """B17b uses '(I control)' which is acceptable for this activity."""
        assert questions['B17b'] == 'Orgasm control - edging, denial, forced orgasm (I control).'

    def test_b11a_unchanged(self, questions):
        """B11a should remain as-is (receiving pattern is fine)."""
        assert questions['B11a'] == 'Oral sex on genitals (receiving).'

    def test_b11b_unchanged(self, questions):
        """B11b should remain as-is (giving pattern is fine)."""
        assert questions['B11b'] == 'Oral sex on genitals (giving).'
