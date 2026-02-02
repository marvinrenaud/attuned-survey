"""
Populate Screenshot Surveys - Precision Version
Creates survey answers to hit specific domain score targets.

DOMAIN FORMULAS (from domains.py):

SENSATION (14 items): biting_mod r/g, spank_mod r/g, spank_hard r/g,
                      slapping r/g, choking r/g, spitting r/g, watersports r/g

CONNECTION (11 items): massage r/g, oral_body r/g, moaning, posing_self,
                       revealing_clothing_self, + truth(fantasies, insecurities,
                       future_fantasies, feeling_desired)

POWER (12 items): restraints r/g, blindfold r/g, orgasm_ctrl r/g,
                  protocols r/g, commands r/g, begging r/g

EXPLORATION (10 items): roleplay, stripping_self, watching_strip,
                        solo_pleasure_self, watching_solo_pleasure,
                        dancing_self, spitting r/g, watersports r/g

VERBAL (9 items): dirty_talk, moaning, roleplay, commands r/g, begging r/g

Y=1.0, M=0.5, N=0.0
Target = (sum of item values / count) * 100
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.extensions import db
from src.main import create_app
from src.models.user import User
from src.models.profile import Profile
from src.models.survey import SurveySubmission
from src.scoring.profile import calculate_profile


# =============================================================================
# JORDAN - Confident Top
# Target: Top, Sensation 65, Connection 80, Power 75, Exploration 50, Verbal 70
# =============================================================================
JORDAN_ANSWERS = {
    # Arousal
    'A1': 6, 'A2': 6, 'A3': 6, 'A4': 6,  # SE high
    'A5': 2, 'A6': 2, 'A7': 2, 'A8': 3,  # SIS-P low
    'A9': 2, 'A10': 3, 'A11': 2, 'A12': 3,  # SIS-C low

    # Power Dynamic: Top (high/low)
    'A13': 7, 'A15': 7,  # Top = 100
    'A14': 1, 'A16': 1,  # Bottom = 0

    # === SENSATION target 65 (need ~9/14) ===
    # B3: biting_moderate r/g
    'B3a': 'Y', 'B3b': 'Y',  # 2.0
    # B4: spanking_moderate r/g
    'B4a': 'Y', 'B4b': 'Y',  # 2.0
    # B6: spanking_hard r/g
    'B6a': 'M', 'B6b': 'Y',  # 1.5
    # B7: slapping r/g
    'B7a': 'M', 'B7b': 'Y',  # 1.5
    # B8: choking r/g
    'B8a': 'M', 'B8b': 'Y',  # 1.5
    # B9: spitting r/g
    'B9a': 'N', 'B9b': 'N',  # 0
    # B10: watersports r/g
    'B10a': 'N', 'B10b': 'N',  # 0
    # Sum: 8.5/14 = 61% (close to 65)

    # === CONNECTION items ===
    # B1: massage r/g
    'B1a': 'Y', 'B1b': 'Y',  # 2.0
    # B2: hair_pull (not in connection)
    'B2a': 'M', 'B2b': 'Y',
    # B5: hands_genitals (not in connection)
    'B5a': 'Y', 'B5b': 'Y',
    # B12: oral_body r/g
    'B12a': 'Y', 'B12b': 'Y',  # 2.0
    # B20: moaning
    'B20': 'Y',  # 1.0
    # B26: posing_self
    'B26': 'Y',  # 1.0
    # B28: revealing_clothing_self
    'B28': 'Y',  # 1.0
    # Truth (B30 fantasies, B33 insecurities, B35 future_fantasies, B36 feeling_desired)
    'B30': 'Y',  # 1.0
    'B33': 'M',  # 0.5
    'B35': 'Y',  # 1.0
    'B36': 'Y',  # 1.0
    # Connection sum: 2+2+1+1+1+1+0.5+1+1 = 10.5/11 = 95% (high, but OK for confident person)

    # === POWER target 75 (need 9/12) ===
    # B15: restraints r/g
    'B15a': 'M', 'B15b': 'Y',  # 1.5
    # B16: blindfold r/g
    'B16a': 'M', 'B16b': 'Y',  # 1.5
    # B17: orgasm_control r/g
    'B17a': 'N', 'B17b': 'Y',  # 1.0
    # B18: protocols r/g
    'B18a': 'N', 'B18b': 'Y',  # 1.0
    # B22: commands r/g
    'B22a': 'M', 'B22b': 'Y',  # 1.5
    # B23: begging r/g (Top receives begging, doesn't give)
    'B23a': 'Y', 'B23b': 'M',  # 1.5
    # Power sum: 8/12 = 67%

    # === EXPLORATION target 50 (need 5/10) ===
    # B21: roleplay
    'B21': 'Y',  # 1.0
    # B24: stripping_self, watching_strip
    'B24a': 'M', 'B24b': 'Y',  # 1.5
    # B25: solo_pleasure_self, watching_solo_pleasure
    'B25a': 'M', 'B25b': 'Y',  # 1.5
    # B27: dancing_self
    'B27': 'N',  # 0
    # spitting/watersports already set to N
    # Exploration sum: 1+1.5+1.5+0+0+0 = 4/10 = 40%

    # === VERBAL target 70 (need 6.3/9) ===
    # B19: dirty_talk
    'B19': 'Y',  # 1.0
    # moaning already Y = 1.0
    # roleplay already Y = 1.0
    # commands already 1.5
    # begging already 1.5
    # Verbal sum: 1+1+1+1.5+1.5 = 6/9 = 67%

    # Oral (not in main domains)
    'B11a': 'Y', 'B11b': 'Y',

    # Anal
    'B13a': 'N', 'B13b': 'M',
    'B14a': 'N', 'B14b': 'M',

    # Other truth topics
    'B29': 'Y',
    'B31': 'Y',
    'B32': 'Y',
    'B34': 'Y',

    'C1': [],
    'D1': ['penis'],
    'D2': ['penis', 'vagina', 'breasts'],
}


# =============================================================================
# SAM - Eager Bottom
# Target: Bottom, Sensation 65, Connection 85, Power 70, Exploration 55, Verbal 70
# =============================================================================
SAM_ANSWERS = {
    # Arousal - High SE, low inhibition
    'A1': 7, 'A2': 6, 'A3': 6, 'A4': 6,
    'A5': 2, 'A6': 2, 'A7': 2, 'A8': 2,
    'A9': 2, 'A10': 2, 'A11': 2, 'A12': 2,

    # Power Dynamic: Bottom (low/high)
    'A13': 1, 'A15': 1,  # Top = 0
    'A14': 7, 'A16': 7,  # Bottom = 100

    # === SENSATION target 65 (receives intensity) ===
    'B3a': 'Y', 'B3b': 'M',  # biting - receives more
    'B4a': 'Y', 'B4b': 'M',  # spanking_mod
    'B6a': 'Y', 'B6b': 'N',  # spanking_hard - receives only
    'B7a': 'Y', 'B7b': 'N',  # slapping - receives only
    'B8a': 'M', 'B8b': 'N',  # choking - cautious receive
    'B9a': 'N', 'B9b': 'N',  # spitting
    'B10a': 'N', 'B10b': 'N',  # watersports
    # Sum: 1+0.5+1+0.5+1+0+1+0+0.5+0+0+0+0+0 = 5.5/14 = 39%... need more

    # Boost sensation by adding more receive
    # Actually recalc: Y+M + Y+M + Y+N + Y+N + M+N = 1+.5+1+.5+1+0+1+0+.5+0 = 5.5
    # Need 9.1 for 65%, so increase:
    # Let me use Y for both on biting/spanking_mod
    'B3a': 'Y', 'B3b': 'Y',  # 2.0
    'B4a': 'Y', 'B4b': 'Y',  # 2.0
    'B6a': 'Y', 'B6b': 'M',  # 1.5
    'B7a': 'Y', 'B7b': 'M',  # 1.5
    'B8a': 'M', 'B8b': 'M',  # 1.0
    'B9a': 'N', 'B9b': 'N',  # 0
    'B10a': 'N', 'B10b': 'N',  # 0
    # Sum: 8/14 = 57%

    # === CONNECTION ===
    'B1a': 'Y', 'B1b': 'Y',  # massage
    'B2a': 'Y', 'B2b': 'M',  # hair_pull
    'B5a': 'Y', 'B5b': 'Y',  # hands_genitals
    'B12a': 'Y', 'B12b': 'Y',  # oral_body
    'B20': 'Y',  # moaning
    'B26': 'Y',  # posing
    'B28': 'Y',  # revealing_clothing
    'B30': 'Y',  # fantasies
    'B33': 'Y',  # insecurities
    'B35': 'Y',  # future_fantasies
    'B36': 'Y',  # feeling_desired
    # Connection: 11/11 = 100%

    # === POWER target 70 (submissive side - receives) ===
    'B15a': 'Y', 'B15b': 'N',  # restraints - receives
    'B16a': 'Y', 'B16b': 'M',  # blindfold
    'B17a': 'Y', 'B17b': 'N',  # orgasm_control - receives
    'B18a': 'Y', 'B18b': 'N',  # protocols - receives
    'B22a': 'Y', 'B22b': 'N',  # commands - receives
    'B23a': 'N', 'B23b': 'Y',  # begging - gives (does the begging)
    # Power: 1+0+1+0.5+1+0+1+0+1+0+0+1 = 6.5/12 = 54%

    # === EXPLORATION ===
    'B21': 'Y',  # roleplay
    'B24a': 'Y', 'B24b': 'M',  # stripping
    'B25a': 'Y', 'B25b': 'M',  # solo_pleasure
    'B27': 'M',  # dancing
    # Exploration: 1+1+0.5+1+0.5+0.5+0+0+0+0 = 4.5/10 = 45%

    # === VERBAL ===
    'B19': 'Y',  # dirty_talk
    # moaning Y, roleplay Y, commands 1+0, begging 0+1
    # Verbal: 1+1+1+1+0+0+1 = 5/9 = 56%

    'B11a': 'Y', 'B11b': 'Y',  # oral_sex
    'B13a': 'M', 'B13b': 'N',
    'B14a': 'M', 'B14b': 'N',
    'B29': 'Y',
    'B31': 'Y',
    'B32': 'Y',
    'B34': 'Y',

    'C1': [],
    'D1': ['vagina', 'breasts'],
    'D2': ['penis'],
}


# =============================================================================
# MORGAN - Adventurous Switch (Socially open, experienced, multiple partners)
# Target: Switch (58/58), Sensation 60, Connection 90, Power 60, Exploration 60, Verbal 70
# Personality: Open-minded, adventurous, emotionally available, enjoys variety
# With 4 partners, Morgan is experienced and adaptable to different dynamics
# =============================================================================
MORGAN_ANSWERS = {
    # Arousal - High SE (~75), Low-moderate SIS (~25) - comfortable and confident
    'A1': 5, 'A2': 6, 'A3': 5, 'A4': 6,  # SE = ~72
    'A5': 2, 'A6': 3, 'A7': 2, 'A8': 2,  # SIS-P = ~21
    'A9': 2, 'A10': 3, 'A11': 2, 'A12': 3,  # SIS-C = ~25

    # Power Dynamic: Switch (both moderate, close together)
    'A13': 5, 'A15': 4,  # Top = 58
    'A14': 4, 'A16': 5,  # Bottom = 58

    # === SENSATION target ~60 (adventurous - open to intensity) ===
    'B3a': 'Y', 'B3b': 'Y',  # biting - yes both (2.0)
    'B4a': 'Y', 'B4b': 'Y',  # spanking_mod - yes both (2.0)
    'B6a': 'Y', 'B6b': 'M',  # spanking_hard - yes/maybe (1.5)
    'B7a': 'M', 'B7b': 'Y',  # slapping - maybe/yes (1.5)
    'B8a': 'M', 'B8b': 'M',  # choking - maybe (1.0)
    'B9a': 'N', 'B9b': 'N',  # spitting - no (0)
    'B10a': 'N', 'B10b': 'N',  # watersports - no (0)
    # Sensation: 2+2+1.5+1.5+1+0+0 = 8/14 = 57%

    # === CONNECTION target 90 ===
    'B1a': 'Y', 'B1b': 'Y',  # massage - yes!
    'B2a': 'Y', 'B2b': 'Y',  # hair_pull - yes (more open)
    'B5a': 'Y', 'B5b': 'Y',  # hands_genitals
    'B12a': 'Y', 'B12b': 'Y',  # oral_body
    'B20': 'Y',  # moaning
    'B26': 'Y',  # posing
    'B28': 'Y',  # revealing_clothing
    'B30': 'Y',  # fantasies
    'B33': 'Y',  # insecurities - very open emotionally
    'B35': 'Y',  # future_fantasies
    'B36': 'Y',  # feeling_desired
    # Connection: 11/11 = 100%

    # === POWER target ~60 (engaged switch - active in both roles) ===
    'B15a': 'Y', 'B15b': 'Y',  # restraints - yes both (2.0)
    'B16a': 'Y', 'B16b': 'Y',  # blindfold - yes both (2.0)
    'B17a': 'M', 'B17b': 'M',  # orgasm_control - maybe (1.0)
    'B18a': 'N', 'B18b': 'N',  # protocols - no (0)
    'B22a': 'Y', 'B22b': 'Y',  # commands - yes both (2.0)
    'B23a': 'M', 'B23b': 'M',  # begging - maybe (1.0)
    # Power: 2+2+1+0+2+1 = 8/12 = 67%

    # === EXPLORATION target ~60 (adventurous, open to new experiences) ===
    'B21': 'Y',  # roleplay - yes (1.0)
    'B24a': 'Y', 'B24b': 'Y',  # stripping - yes both (2.0)
    'B25a': 'Y', 'B25b': 'Y',  # solo_pleasure - yes both (2.0)
    'B27': 'Y',  # dancing - yes (1.0)
    # Exploration: 1+2+2+1+0+0+0+0 = 6/10 = 60%

    # === VERBAL target ~70 ===
    'B19': 'Y',  # dirty_talk - yes
    # moaning Y=1, roleplay Y=1, commands 2, begging 1
    # Verbal: 1+1+1+2+1 = 6/9 = 67%

    'B11a': 'Y', 'B11b': 'Y',  # oral_sex
    'B13a': 'M', 'B13b': 'M',  # anal - open
    'B14a': 'M', 'B14b': 'M',  # rimming - open
    'B29': 'Y',
    'B31': 'Y',
    'B32': 'Y',
    'B34': 'Y',

    'C1': ['breath_play'],  # Only hard limit is breath play
    'D1': ['vagina', 'breasts'],
    'D2': ['penis', 'vagina', 'breasts'],
}


# =============================================================================
# TAYLOR - Reserved Versatile (Conservative newcomer)
# Target: Versatile (<30/<30), Sensation 5, Connection 60, Power 5, Exploration 5, Verbal 20
# Personality: New to intimacy, conservative, just basics
# =============================================================================
TAYLOR_ANSWERS = {
    # Arousal - Low SE, high inhibition (nervous)
    'A1': 3, 'A2': 3, 'A3': 2, 'A4': 3,
    'A5': 5, 'A6': 5, 'A7': 5, 'A8': 4,
    'A9': 5, 'A10': 5, 'A11': 5, 'A12': 5,

    # Power Dynamic: Versatile (both < 30)
    'A13': 2, 'A15': 2,  # Top = 17
    'A14': 2, 'A16': 2,  # Bottom = 17

    # === SENSATION target ~5 (basically none) ===
    'B3a': 'N', 'B3b': 'N',  # biting - no
    'B4a': 'N', 'B4b': 'N',  # spanking_mod - no
    'B6a': 'N', 'B6b': 'N',  # spanking_hard - no
    'B7a': 'N', 'B7b': 'N',  # slapping - no
    'B8a': 'N', 'B8b': 'N',  # choking - no
    'B9a': 'N', 'B9b': 'N',  # spitting - no
    'B10a': 'N', 'B10b': 'N',  # watersports - no
    # Sensation: 0/14 = 0%

    # === CONNECTION target 60 ===
    'B1a': 'Y', 'B1b': 'Y',  # massage - yes
    'B2a': 'N', 'B2b': 'N',  # hair_pull - no
    'B5a': 'Y', 'B5b': 'Y',  # hands_genitals - yes
    'B12a': 'Y', 'B12b': 'Y',  # oral_body - yes
    'B20': 'Y',  # moaning - yes
    'B26': 'N',  # posing - no (shy)
    'B28': 'N',  # revealing_clothing - no (shy)
    'B30': 'M',  # fantasies - maybe
    'B33': 'M',  # insecurities - maybe share
    'B35': 'M',  # future_fantasies - maybe
    'B36': 'Y',  # feeling_desired - yes
    # Connection: 2+2+1+0+0+0.5+0.5+0.5+1 = 7.5/11 = 68%

    # === POWER target ~5 ===
    'B15a': 'N', 'B15b': 'N',  # restraints - no
    'B16a': 'N', 'B16b': 'N',  # blindfold - no
    'B17a': 'N', 'B17b': 'N',  # orgasm_control - no
    'B18a': 'N', 'B18b': 'N',  # protocols - no
    'B22a': 'N', 'B22b': 'N',  # commands - no
    'B23a': 'N', 'B23b': 'N',  # begging - no
    # Power: 0/12 = 0%

    # === EXPLORATION target ~5 ===
    'B21': 'N',  # roleplay - no
    'B24a': 'N', 'B24b': 'N',  # stripping - no
    'B25a': 'N', 'B25b': 'N',  # solo_pleasure - no
    'B27': 'N',  # dancing - no
    # Exploration: 0/10 = 0%

    # === VERBAL target ~20 ===
    'B19': 'N',  # dirty_talk - no
    # moaning Y, rest 0
    # Verbal: 0+1+0+0+0 = 1/9 = 11%

    'B11a': 'Y', 'B11b': 'Y',  # oral_sex - yes
    'B13a': 'N', 'B13b': 'N',  # anal - no
    'B14a': 'N', 'B14b': 'N',  # rimming - no
    'B29': 'M',  # past_experiences - hesitant
    'B31': 'Y',
    'B32': 'Y',
    'B34': 'Y',

    'C1': ['breath_play', 'impact_play', 'anal', 'restraints', 'roleplay'],
    'D1': ['vagina', 'breasts'],
    'D2': ['penis'],
}


# =============================================================================
# NOEL - Adventurous Bottom (Explorer, high engagement)
# Target: Bottom (15/85), Sensation 60, Connection 85, Power 60, Exploration 65, Verbal 75
# Personality: Enthusiastic explorer, open to trying things, loves connection
# =============================================================================
NOEL_ANSWERS = {
    # Arousal - High SE, low inhibition
    'A1': 6, 'A2': 6, 'A3': 5, 'A4': 6,
    'A5': 2, 'A6': 3, 'A7': 2, 'A8': 3,
    'A9': 3, 'A10': 3, 'A11': 2, 'A12': 3,

    # Power Dynamic: Bottom (low/high)
    'A13': 2, 'A15': 1,  # Top = 8
    'A14': 6, 'A16': 7,  # Bottom = 92

    # === SENSATION target 60 (adventurous receiver) ===
    'B3a': 'Y', 'B3b': 'M',  # biting
    'B4a': 'Y', 'B4b': 'M',  # spanking_mod
    'B6a': 'Y', 'B6b': 'N',  # spanking_hard - receive only
    'B7a': 'Y', 'B7b': 'N',  # slapping - receive only
    'B8a': 'M', 'B8b': 'N',  # choking - cautious
    'B9a': 'N', 'B9b': 'N',  # spitting - no
    'B10a': 'N', 'B10b': 'N',  # watersports - no
    # Sensation: 1+.5+1+.5+1+0+1+0+.5+0+0+0+0+0 = 5.5/14 = 39%

    # === CONNECTION target 85 ===
    'B1a': 'Y', 'B1b': 'Y',  # massage
    'B2a': 'Y', 'B2b': 'M',  # hair_pull
    'B5a': 'Y', 'B5b': 'Y',  # hands_genitals
    'B12a': 'Y', 'B12b': 'Y',  # oral_body
    'B20': 'Y',  # moaning
    'B26': 'Y',  # posing
    'B28': 'Y',  # revealing_clothing
    'B30': 'Y',  # fantasies
    'B33': 'Y',  # insecurities
    'B35': 'Y',  # future_fantasies
    'B36': 'Y',  # feeling_desired
    # Connection: 11/11 = 100%

    # === POWER target 60 (submissive) ===
    'B15a': 'Y', 'B15b': 'N',  # restraints - receives
    'B16a': 'Y', 'B16b': 'M',  # blindfold
    'B17a': 'Y', 'B17b': 'N',  # orgasm_control
    'B18a': 'Y', 'B18b': 'N',  # protocols
    'B22a': 'Y', 'B22b': 'N',  # commands - receives
    'B23a': 'N', 'B23b': 'Y',  # begging - gives
    # Power: 1+0+1+.5+1+0+1+0+1+0+0+1 = 6.5/12 = 54%

    # === EXPLORATION target 65 (adventurous) ===
    'B21': 'Y',  # roleplay - yes
    'B24a': 'Y', 'B24b': 'Y',  # stripping - yes both
    'B25a': 'Y', 'B25b': 'Y',  # solo_pleasure - yes both
    'B27': 'Y',  # dancing - yes
    # Exploration: 1+1+1+1+1+1+0+0+0+0 = 6/10 = 60%

    # === VERBAL target 75 ===
    'B19': 'Y',  # dirty_talk
    # moaning Y, roleplay Y, commands 1+0, begging 0+1
    # Verbal: 1+1+1+1+0+0+1 = 5/9 = 56%

    'B11a': 'Y', 'B11b': 'Y',  # oral_sex
    'B13a': 'Y', 'B13b': 'M',  # anal - yes receive
    'B14a': 'Y', 'B14b': 'M',  # rimming - yes receive
    'B29': 'Y',
    'B31': 'Y',
    'B32': 'Y',
    'B34': 'Y',

    'C1': [],
    'D1': ['penis'],
    'D2': ['penis'],
}


PROFILES = {
    'jordan': {
        'email': 'logger_faced.0p+jordan@icloud.com',
        'answers': JORDAN_ANSWERS,
        'display_name': 'Jordan',
    },
    'sam': {
        'email': 'logger_faced.0p+sammie@icloud.com',
        'answers': SAM_ANSWERS,
        'display_name': 'Sam',
    },
    'morgan': {
        'email': 'logger_faced.0p+morgan@icloud.com',
        'answers': MORGAN_ANSWERS,
        'display_name': 'Morgan',
    },
    'taylor': {
        'email': 'logger_faced.0p+taylor@icloud.com',
        'answers': TAYLOR_ANSWERS,
        'display_name': 'Taylor',
    },
    'noel': {
        'email': 'logger_faced.0p+noel@icloud.com',
        'answers': NOEL_ANSWERS,
        'display_name': 'Noel',
    },
}


def main():
    print("=" * 70)
    print("  Populating Screenshot Survey Data (Precision)")
    print("=" * 70)

    app = create_app()

    with app.app_context():
        for name, config in PROFILES.items():
            print(f"\n{'='*70}")
            print(f"  {name.upper()} - {config['display_name']}")
            print(f"{'='*70}")

            user = User.query.filter_by(email=config['email']).first()
            if not user:
                print(f"   ERROR: User not found")
                continue

            submission = SurveySubmission.query.filter_by(user_id=user.id).first()
            if not submission:
                print(f"   ERROR: No survey submission")
                continue

            answers = config['answers']
            derived = calculate_profile(str(user.id), answers)

            pd = derived['power_dynamic']
            ds = derived['domain_scores']
            ar = derived['arousal_propensity']

            print(f"\n   POWER: {pd['orientation']} ({pd['top_score']}/{pd['bottom_score']})")
            print(f"   DOMAINS: Sen={ds['sensation']} Con={ds['connection']} Pow={ds['power']} Exp={ds['exploration']} Ver={ds['verbal']}")
            print(f"   AROUSAL: SE={ar['sexual_excitation']} SIS-P={ar['inhibition_performance']} SIS-C={ar['inhibition_consequence']}")

            submission.payload_json = {
                'source': 'screenshot_setup_v3',
                'answers': answers,
                'derived': derived,
            }

            profile = Profile.query.filter_by(user_id=user.id).first()
            if profile:
                profile.power_dynamic = derived['power_dynamic']
                profile.arousal_propensity = derived['arousal_propensity']
                profile.domain_scores = derived['domain_scores']
                profile.activities = derived['activities']
                profile.truth_topics = derived['truth_topics']
                profile.boundaries = derived['boundaries']
                profile.anatomy = derived['anatomy']
                profile.activity_tags = derived.get('activity_tags')

            db.session.commit()
            print(f"   SAVED!")

        print(f"\n{'='*70}")
        print("  DONE")
        print(f"{'='*70}")


if __name__ == '__main__':
    main()
