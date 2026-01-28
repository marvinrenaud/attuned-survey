"""
Tests for agreement-based Jaccard scoring in compatibility algorithm.

These tests verify that mutual disinterest (both saying "no") counts as agreement,
not as 0% compatibility. Agreement is agreement - whether both say "yes" OR both say "no".
"""
import pytest
from src.compatibility.calculator import (
    calculate_activity_overlap,
    calculate_domain_similarity,
    calculate_power_complement,
)


class TestMutualDisinterestAsAgreement:
    """Tests for Bug 1: Mutual disinterest should count as agreement."""

    def test_mutual_disinterest_counts_as_agreement_standard_jaccard(self):
        """Both saying 'no' to anal should be agreement, not 0%."""
        # Both have 0.0 for anal activities (neither interested)
        activities_a = {
            'anal': {
                'anal_fingers_toys_receive': 0.0,
                'anal_fingers_toys_give': 0.0,
                'anal_sex_receive': 0.0,
                'anal_sex_give': 0.0,
            }
        }
        activities_b = {
            'anal': {
                'anal_fingers_toys_receive': 0.0,
                'anal_fingers_toys_give': 0.0,
                'anal_sex_receive': 0.0,
                'anal_sex_give': 0.0,
            }
        }
        power_switch = {'orientation': 'Switch', 'intensity': 0.5}

        overlap = calculate_activity_overlap(
            activities_a, activities_b, power_switch, power_switch
        )

        # Mutual disinterest should score high (agreement), not 0.5 (default)
        assert overlap >= 0.9, f"Mutual disinterest should be agreement, got {overlap}"

    def test_identical_preferences_high_overlap(self):
        """Identical preferences (mix of yes and no) should score very high."""
        # Both have identical preferences - some yes, some no
        activities = {
            'physical_touch': {
                'massage_receive': 1.0,
                'massage_give': 1.0,
                'hair_pulling_receive': 0.0,  # Both no
                'hair_pulling_give': 0.0,      # Both no
            },
            'anal': {
                'anal_fingers_toys_receive': 0.0,  # Both no
                'anal_fingers_toys_give': 0.0,      # Both no
            }
        }
        power_switch = {'orientation': 'Switch', 'intensity': 0.5}

        overlap = calculate_activity_overlap(
            activities, activities, power_switch, power_switch
        )

        # Identical preferences = 100% agreement
        assert overlap >= 0.95, f"Identical preferences should be ~100%, got {overlap}"

    def test_mismatch_reduces_score(self):
        """When one wants something the other doesn't, score should be lower."""
        activities_a = {
            'physical_touch': {
                'massage_receive': 1.0,
                'massage_give': 1.0,
                'spanking_receive': 1.0,  # A wants
                'spanking_give': 1.0,
            }
        }
        activities_b = {
            'physical_touch': {
                'massage_receive': 1.0,
                'massage_give': 1.0,
                'spanking_receive': 0.0,  # B doesn't want
                'spanking_give': 0.0,
            }
        }
        power_switch = {'orientation': 'Switch', 'intensity': 0.5}

        overlap = calculate_activity_overlap(
            activities_a, activities_b, power_switch, power_switch
        )

        # 2 agreements (massage), 2 mismatches (spanking) = 50%
        assert 0.4 <= overlap <= 0.6, f"Half match should be ~50%, got {overlap}"


class TestSamePoleDomainPenalty:
    """Tests for Bug 2: Same-pole domain similarity should be halved."""

    def test_same_pole_domain_similarity_penalty_top_top(self):
        """Top+Top domain similarity should be halved per TECHNICAL_NOTES.md."""
        domains = {
            'sensation': 70,
            'connection': 80,
            'power': 60,
            'exploration': 75,
            'verbal': 70
        }
        power_top = {'orientation': 'Top', 'intensity': 0.8}

        # Same domains for both = 100% raw similarity
        similarity = calculate_domain_similarity(domains, domains, power_top, power_top)

        # Same-pole should apply 0.5 penalty: 100% * 0.5 = 50%
        assert similarity <= 0.55, f"Same-pole Top+Top should be ~50%, got {similarity}"

    def test_same_pole_domain_similarity_penalty_bottom_bottom(self):
        """Bottom+Bottom domain similarity should also be halved."""
        domains = {
            'sensation': 60,
            'connection': 90,
            'power': 70,
            'exploration': 65,
            'verbal': 80
        }
        power_bottom = {'orientation': 'Bottom', 'intensity': 0.9}

        similarity = calculate_domain_similarity(
            domains, domains, power_bottom, power_bottom
        )

        # Same-pole should apply 0.5 penalty
        assert similarity <= 0.55, f"Same-pole Bottom+Bottom should be ~50%, got {similarity}"

    def test_complementary_pair_no_penalty(self):
        """Top+Bottom pairs should NOT have domain similarity penalty."""
        domains = {
            'sensation': 70,
            'connection': 80,
            'power': 60,
            'exploration': 75,
            'verbal': 70
        }
        power_top = {'orientation': 'Top', 'intensity': 0.8}
        power_bottom = {'orientation': 'Bottom', 'intensity': 0.8}

        similarity = calculate_domain_similarity(
            domains, domains, power_top, power_bottom
        )

        # Complementary pairs get no penalty - should be high
        assert similarity >= 0.90, f"Top+Bottom identical domains should be ~100%, got {similarity}"

    def test_switch_switch_no_penalty(self):
        """Switch+Switch pairs should NOT have domain similarity penalty."""
        domains = {
            'sensation': 70,
            'connection': 80,
            'power': 60,
            'exploration': 75,
            'verbal': 70
        }
        power_switch = {'orientation': 'Switch', 'intensity': 0.5}

        similarity = calculate_domain_similarity(
            domains, domains, power_switch, power_switch
        )

        # Switch pairs get no penalty
        assert similarity >= 0.90, f"Switch+Switch identical domains should be ~100%, got {similarity}"


class TestVersatilePowerComplement:
    """Tests for Bug 3: Versatile/Versatile should score higher than same-pole."""

    def test_versatile_versatile_higher_than_same_pole(self):
        """Versatile+Versatile should score higher than same-pole conflicts."""
        power_versatile = {'orientation': 'Versatile', 'intensity': 0.3}
        power_top = {'orientation': 'Top', 'intensity': 0.8}

        versatile_score = calculate_power_complement(power_versatile, power_versatile)
        same_pole_score = calculate_power_complement(power_top, power_top)

        # Versatile/Versatile should be higher than same-pole (0.50)
        assert versatile_score > same_pole_score, \
            f"Versatile/Versatile ({versatile_score}) should be > same-pole ({same_pole_score})"

    def test_versatile_versatile_minimum_score(self):
        """Versatile+Versatile should score at least 0.70."""
        power_versatile = {'orientation': 'Versatile', 'intensity': 0.3}

        score = calculate_power_complement(power_versatile, power_versatile)

        assert score >= 0.70, f"Versatile/Versatile should be >= 0.70, got {score}"

    def test_versatile_undefined_also_works(self):
        """Versatile/Undefined orientation should behave same as Versatile."""
        power_v1 = {'orientation': 'Versatile/Undefined', 'intensity': 0.2}
        power_v2 = {'orientation': 'Versatile', 'intensity': 0.3}

        # Both Versatile/Undefined
        score_both = calculate_power_complement(power_v1, power_v1)
        # Mixed Versatile types
        score_mixed = calculate_power_complement(power_v1, power_v2)

        assert score_both >= 0.70, f"Versatile/Undefined pair should be >= 0.70, got {score_both}"
        assert score_mixed >= 0.70, f"Mixed Versatile pair should be >= 0.70, got {score_mixed}"

    def test_versatile_with_defined_orientation(self):
        """Versatile + Top/Bottom should be moderate (between same-pole and Switch)."""
        power_versatile = {'orientation': 'Versatile', 'intensity': 0.3}
        power_top = {'orientation': 'Top', 'intensity': 0.8}
        power_bottom = {'orientation': 'Bottom', 'intensity': 0.8}

        score_with_top = calculate_power_complement(power_versatile, power_top)
        score_with_bottom = calculate_power_complement(power_versatile, power_bottom)
        same_pole_score = calculate_power_complement(power_top, power_top)

        # Versatile + defined should be higher than pure same-pole
        assert score_with_top > same_pole_score, \
            f"Versatile+Top ({score_with_top}) should be > same-pole ({same_pole_score})"
        assert score_with_bottom > same_pole_score, \
            f"Versatile+Bottom ({score_with_bottom}) should be > same-pole ({same_pole_score})"
