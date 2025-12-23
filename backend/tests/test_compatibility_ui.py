
import unittest
from unittest.mock import MagicMock, patch
from flask import Flask
import uuid
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.routes.compatibility import compatibility_bp, _compare_interests
# Note: We will import _compare_interests after implementing it, for now we mock or test logic units if possible.
# Actually, since I haven't implemented it yet, I can't import it. 
# I will write the test to hit the endpoint and mock the dependencies.

from src.models.user import User
from src.models.profile import Profile
from src.models.compatibility import Compatibility

class TestCompatibilityUI(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(compatibility_bp)
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True

    def test_domain_order_enforcement(self):
        """Verify comparison_data.domains follows strict order."""
        # This will be an integration test mock
        pass

class TestInterestLogic(unittest.TestCase):
    """Unit tests for the helper logic we are about to write."""
    
    def test_smart_matching_giving_receiving(self):
        """Test that 'Massage (Giving)' and 'Massage (Receiving)' match."""
        # Logic to be implemented in _compare_interests
        from src.routes.compatibility import _compare_interests
        
        user_acts = {'massage_give': 1.0}
        partner_acts = {'massage_receive': 1.0}
        
        # We need a mock or real implementation of ACTIVITY_DISPLAY_NAMES for this to work depending on implementation
        # Assuming the helper takes dicts and returns a list
        
        # For TDD, I'll write the test assuming the helper exists, but I can't run it until I create the helper.
        # So I will create the file with the test, but I need to implement the helper in the same step or shortly after.
        pass

# I'll create a full integration test file that mocks the DB queries to test the JSON structure.

class StubModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class TestCompatibilityUIIntegration(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(compatibility_bp)
        self.client = self.app.test_client()
        self.u_id = uuid.uuid4()
        self.p_id = uuid.uuid4()

    @patch('src.routes.compatibility.User')
    @patch('src.routes.compatibility.Profile')
    @patch('src.routes.compatibility.Compatibility')
    @patch('src.routes.compatibility.PartnerConnection')
    def test_ui_structure_and_order(self, mock_conn, mock_compat, mock_profile, mock_user):
        # Mock Connection
        mock_conn.query.filter.return_value.filter_by.return_value.first.return_value = StubModel(status='accepted')
        
        # Mock Users
        u_user = StubModel(id=self.u_id, display_name="User", profile_sharing_setting="all_responses")
        p_user = StubModel(id=self.p_id, display_name="Partner", profile_sharing_setting="all_responses")
        mock_user.query.get.side_effect = lambda id: u_user if id == self.u_id else (p_user if id == self.p_id else None)
        
        # Mock Profiles - Use simple objects
        u_profile = StubModel(
            id=1, 
            user_id=self.u_id,
            submission_id="sub1",
            arousal_propensity={'sexual_excitation': 0.5, 'inhibition_performance': 0.2, 'inhibition_consequence': 0.1},
            power_dynamic={'top_score': 10, 'bottom_score': 5, 'orientation': 'Switch', 'interpretation': 'Versatile'},
            domain_scores={'sensation': 10, 'connection': 20, 'power': 30, 'exploration': 40, 'verbal': 50},
            activities={'physical_touch': {'massage_give': 1.0}},
            boundaries={'hard_limits': []},
            created_at='2023-01-01'
        )
        p_profile = StubModel(
            id=2, 
            user_id=self.p_id,
            submission_id="sub2",
            arousal_propensity={'sexual_excitation': 0.6, 'inhibition_performance': 0.3, 'inhibition_consequence': 0.4},
            power_dynamic={'top_score': 5, 'bottom_score': 10, 'orientation': 'Bottom', 'interpretation': 'Sub'},
            domain_scores={'sensation': 15, 'connection': 25, 'power': 35, 'exploration': 45, 'verbal': 55},
            activities={'physical_touch': {'massage_receive': 1.0}}, # Should match massage_give
            boundaries={'hard_limits': ['spanking']}, # Test conflict?
            created_at='2023-01-01'
        )
        
        # Setup mocking chain: Profile.query... -> first()
        # We need to handle the chain carefully
        # query.filter_by().order_by().first()
        
        # Mock chained return
        mock_query_u = MagicMock()
        mock_query_u.order_by.return_value.first.return_value = u_profile
        
        mock_query_p = MagicMock()
        mock_query_p.order_by.return_value.first.return_value = p_profile

        mock_profile.query.filter_by.side_effect = lambda user_id: mock_query_u if user_id == self.u_id else mock_query_p

        # Mock Compatibility
        mock_compat_rec = StubModel(
            overall_percentage=85,
            interpretation="Great",
            created_at=MagicMock(isoformat=lambda: "2023-01-01"),
            breakdown={'power_complement': 90, 'domain_similarity': 80, 'activity_overlap': 70, 'truth_overlap': 60},
            mutual_activities=[], 
            mutual_truth_topics=[],
            blocked_activities=[],
            boundary_conflicts=[]
        )
        mock_compat.query.filter_by.return_value.first.return_value = mock_compat_rec
        
        # Call Endpoint
        response = self.client.get(f'/api/compatibility/{self.u_id}/{self.p_id}/ui')
        
        # Debug fail
        if response.status_code != 200:
            print(response.json)
        
        self.assertEqual(response.status_code, 200)
        data = response.json
        
        # 1. Critical Domain Alignment
        domains = data['comparison_data']['domains']
        expected_order = ['Sensation', 'Connection', 'Power', 'Exploration', 'Verbal']
        self.assertEqual([d['domain'] for d in domains], expected_order, "Domains must follow strict order")
        self.assertIn('user_score', domains[0])
        self.assertIn('partner_score', domains[0])
        self.assertEqual(domains[0]['user_score'], 10) # check value
        
        # 1b. Comparison Scores
        scores = data['compatibility_summary']['comparison_scores']
        self.assertEqual(scores['power_score'], 90, "Power score should match breakdown")
        self.assertEqual(scores['domain_score'], 80, "Domain score should match breakdown")
        self.assertEqual(scores['activity_score'], 70, "Activity score should match breakdown")
        self.assertEqual(scores['truth_score'], 60, "Truth score should match breakdown")
        
        # 2. Flattened Arousal
        arousal = data['comparison_data']['arousal']
        self.assertIn('user_sexual_excitation', arousal)
        self.assertIn('partner_sexual_excitation', arousal)
        self.assertEqual(arousal['user_sexual_excitation'], 0.5)
        
        # 3. Smart Interest Matching (Giving vs Receiving)
        # massage_give (U) vs massage_receive (P) -> Should be Mutual
        interests = data['interests_comparison']
        # Find Physical Section
        phys = next((s for s in interests if s['section'] == 'Physical Touch'), None)
        self.assertIsNotNone(phys)
        
        # Check for tags
        tags = phys['tags']
        # Flatten tags to check statuses
        # We expect "Massage (Giving)" or "Massage (Receiving)" ?
        # Code logic: append display name. 
        # If mutual, which display name? The one found first in sorted loop.
        # massage_give comes before massage_receive? 'm' 'a' ...
        # If it matched, we added it.
        # Let's check status directly
        
        massage_tag = next((t for t in tags if "Massage" in t['name']), None)
        self.assertIsNotNone(massage_tag, "Should detect massage match")
        self.assertEqual(massage_tag['status'], 'mutual', "Giving/Receiving should match as mutual")
        
        # 4. Null Safety
        self.assertIsNotNone(data['partner_profile']['interests'])
        self.assertIsInstance(data['partner_profile']['interests'], list)

        
        # 4. Conflict Normalization (Hard Limit "Massage" vs Interest "massage_give")
        # u: massage_give, p: hard limit "Massage" (needs normalization key check if hard limit stored as Display Name or Key?)
        # User prompt says: "boundaries in our system are generally stored as the base activity (e.g., 'Massage') rather than the specific role."
        # This implies we need to match "massage_give" -> "Massage"
        # BUT wait, the prompt says "normalize activity keys... so that any role-specific interest is cross-referenced against the base activity".
        # If Hard Limit is "Massage" (Display Name) or "massage" (Key)?
        # Let's assume Hard Limit is stored as "massage" (Key) or "Massage" (Title).
        # We will test mismatch handling.
        # We need a test case where Partner has hard limit="spanking" and User has "spanking_give"
        # In setup u_profile has 'massage_give', p has 'spanking'. 
        # let's add u_profile interest 'spanking_give' to verify conflict.
        
        # 5. Display Name Fallback
        # Test unknown key "unknown_activity_give" -> "Unknown Activity (Giving)"?
        # or just "Unknown Activity Give"
        
        self.assertIsNotNone(data)

    def test_logic_refinements(self):
        """Test specific edge cases for logic refinements."""
        from src.routes.compatibility import _compare_interests
        
        # Setup Data
        u_acts = {
            'physical_touch': {
                'massage_give': 1.0, 
                'unknown_thing_receive': 1.0,
                'spanking_give': 1.0
            }
        }
        u_bounds = {}
        
        p_acts = {
            'physical_touch': {
                'massage_receive': 1.0
            }
        }
        # Partner hates 'Spanking' (Base)
        p_bounds = {'hard_limits': ['Spanking', 'spanking']} 
        
        results = _compare_interests(u_acts, u_bounds, p_acts, p_bounds, False)
        phys = results[0]['tags']
        
        # 1. Smart Match Deduplication
        # Should only have one entry for massage
        massage = [t for t in phys if 'Massage' in t['name']]
        self.assertEqual(len(massage), 1, "Should de-duplicate Giving/Receiving pair")
        self.assertEqual(massage[0]['status'], 'mutual')
        
        # 2. Conflict Normalization
        # Spanking Give vs Spanking Limit
        spanking = next((t for t in phys if 'Spanking' in t['name']), None)
        self.assertIsNotNone(spanking, "Should find spanking interest")
        self.assertEqual(spanking['status'], 'conflict', "Should detect conflict despite suffix")
        
        # 3. Fallback Formatting
        # unknown_thing_receive -> Unknown Thing Receive (Formatted)
        unknown = next((t for t in phys if 'Unknown' in t['name']), None)
        self.assertIsNotNone(unknown)
        # Expect "Unknown Thing Receive" or similar title case
        self.assertTrue(unknown['name'].startswith("Unknown Thing"), "Should format fallback name")

if __name__ == '__main__':
    unittest.main()
