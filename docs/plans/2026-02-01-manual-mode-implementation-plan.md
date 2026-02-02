# Manual Mode Paired Cards - Implementation Plan

**Date:** February 1, 2026
**Branch:** `feature/manual-mode-paired-cards`
**Status:** APPROVED - Ready for Implementation

---

## Executive Summary

Implement paired cards for manual mode gameplay. When `selection_mode: "MANUAL"`, each queue item contains both `truth_card` and `dare_card` fields. Frontend picks which to display based on user selection. Backend tracks only the selected card and charges one credit per turn.

**Estimated Effort:** Backend changes + comprehensive testing

---

## Agreed Design

### Queue Structure

**RANDOM mode (unchanged):**
```json
{
  "selection_mode": "RANDOM",
  "queue": [
    {
      "step": 1,
      "status": "SHOW_CARD",
      "card_id": "123",
      "card": { "card_id": "123", "type": "TRUTH", "display_text": "...", "primary_player": "Marcus" },
      "truth_card": null,
      "dare_card": null,
      "primary_player_idx": 0,
      "progress": { ... }
    }
  ]
}
```

**MANUAL mode (new):**
```json
{
  "selection_mode": "MANUAL",
  "queue": [
    {
      "step": 1,
      "status": "SHOW_CARD",
      "card_id": null,
      "card": null,
      "truth_card": { "card_id": "123", "type": "TRUTH", "display_text": "...", "primary_player": "Marcus" },
      "dare_card": { "card_id": "456", "type": "DARE", "display_text": "...", "primary_player": "Marcus" },
      "primary_player_idx": 0,
      "progress": { ... }
    }
  ]
}
```

### API Contract

**NextTurn Request:**
```json
POST /api/game/{session_id}/next
{
  "action": "NEXT",
  "selected_type": "TRUTH"  // REQUIRED in MANUAL mode
}
```

**Behavior:**
- RANDOM mode: `selected_type` ignored, consumes `card`
- MANUAL mode: `selected_type` required, consumes matching card (`truth_card` or `dare_card`)

### Billing Rules

| Event | Activity Logged | Credit Charged |
|-------|-----------------|----------------|
| Pair generated | Neither | 0 |
| User selects TRUTH | `truth_card` | 1 |
| User selects DARE | `dare_card` | 1 |
| Unselected card | Not logged | 0 |

---

## Implementation Phases

### Phase 0: Setup & Baseline Testing

**Branch Creation:**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/manual-mode-paired-cards
```

**Capture Baseline Test Results:**
```bash
cd backend
python -m pytest tests/test_gameplay_*.py -v --tb=short > ../docs/plans/baseline_gameplay_tests.txt 2>&1
python -m pytest tests/test_gameplay_limits.py -v
```

**Create Baseline Snapshot Test:**

Create `backend/tests/test_manual_mode_baseline.py` to capture current RANDOM mode behavior before changes.

---

### Phase 1: Core Data Structure Changes

**File:** `backend/src/routes/gameplay.py`

#### 1.1 Add Helper Function for Card Generation

```python
def _generate_single_card(
    session: Session,
    target_step: int,
    activity_type: str,  # "truth" or "dare"
    primary_player: dict,
    secondary_player: dict,
    intensity_min: int,
    intensity_max: int,
    rating: str,
    exclude_ids: set
) -> Optional[Dict[str, Any]]:
    """Generate a single card of specified type. Returns None if no activity found."""
    # Extract card generation logic from _generate_turn_data
    # ... existing activity selection, scoring, text resolution ...

    return {
        "card_id": str(activity.activity_id),
        "type": activity_type.upper(),
        "display_text": resolved_text,
        "primary_player": primary_player.get('name', 'Player'),
        "secondary_players": [secondary_player.get('name', 'Partner')],
        "intensity_rating": activity.intensity
    }
```

#### 1.2 Modify `_generate_turn_data()` for Dual-Card Support

```python
def _generate_turn_data(
    session: Session,
    step_offset: int = 0,
    selected_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate data for a single turn.

    In MANUAL mode: generates both truth_card and dare_card
    In RANDOM mode: generates single card (existing behavior)
    """
    settings = session.game_settings or {}
    is_manual = settings.get("selection_mode", "RANDOM").upper() == "MANUAL"
    include_dare = settings.get("include_dare", True)

    # ... existing setup (players, step calculation, profiles, exclusions) ...

    if is_manual:
        # Generate BOTH cards
        truth_card = _generate_single_card(
            session, target_step, "truth",
            primary_player, secondary_player,
            intensity_min, intensity_max, rating, exclude_ids
        )

        dare_card = None
        if include_dare:
            # Use different exclude set to allow different activity
            dare_exclude = exclude_ids.copy()
            if truth_card:
                dare_exclude.add(int(truth_card["card_id"]))
            dare_card = _generate_single_card(
                session, target_step, "dare",
                primary_player, secondary_player,
                intensity_min, intensity_max, rating, dare_exclude
            )

        return {
            "status": "SHOW_CARD",
            "primary_player_idx": primary_idx,
            "step": target_step,
            "card_id": None,  # No single card in MANUAL mode
            "card": None,
            "truth_card": truth_card,
            "dare_card": dare_card,
            "progress": {
                "current_step": effective_step,
                "total_steps": 25,
                "intensity_phase": get_phase_name(effective_step)
            }
        }
    else:
        # RANDOM mode: existing single-card behavior
        activity_type = selected_type if selected_type else random.choice(["truth", "dare"])
        if activity_type.lower() == "dare" and not include_dare:
            activity_type = "truth"

        card = _generate_single_card(
            session, target_step, activity_type,
            primary_player, secondary_player,
            intensity_min, intensity_max, rating, exclude_ids
        )

        return {
            "status": "SHOW_CARD",
            "primary_player_idx": primary_idx,
            "step": target_step,
            "card_id": card["card_id"] if card else "fallback",
            "card": card,
            "truth_card": None,
            "dare_card": None,
            "progress": { ... }
        }
```

---

### Phase 2: NextTurn Endpoint Changes

**File:** `backend/src/routes/gameplay.py`

#### 2.1 Modify `next_turn()` to Handle Selection

```python
@gameplay_bp.route("/<session_id>/next", methods=["POST"])
@token_required
@limiter.limit("300 per hour")
def next_turn(current_user_id, session_id):
    """
    Advance to next turn.

    In MANUAL mode:
    - Requires selected_type in request body
    - Tracks only the selected card (truth_card or dare_card)
    - Charges 1 credit for the selected card
    """
    try:
        # ... existing session fetch and validation ...

        data = request.get_json() or {}
        selected_type = data.get("selected_type")  # NEW: Read selection

        settings = session.game_settings or {}
        is_manual = settings.get("selection_mode", "RANDOM").upper() == "MANUAL"

        state = session.current_turn_state or {}
        queue = state.get("queue", [])

        # Determine owner
        owner_id = str(current_user_id) if current_user_id else None
        anonymous_session_id = data.get("anonymous_session_id")

        if not owner_id and not anonymous_session_id:
            return jsonify({'error': 'Unauthorized', 'message': 'Identity required for billing'}), 401

        # 1. Consume the current turn
        if queue:
            consumed_item = queue.pop(0)

            if is_manual:
                # MANUAL MODE: Validate and extract selected card
                if not selected_type:
                    return jsonify({
                        'error': 'Bad Request',
                        'message': 'selected_type required in MANUAL mode'
                    }), 400

                selected_type = selected_type.upper()

                if selected_type == "TRUTH":
                    selected_card = consumed_item.get("truth_card")
                elif selected_type == "DARE":
                    selected_card = consumed_item.get("dare_card")
                else:
                    return jsonify({
                        'error': 'Bad Request',
                        'message': 'selected_type must be TRUTH or DARE'
                    }), 400

                if selected_card is None:
                    return jsonify({
                        'error': 'Bad Request',
                        'message': f'{selected_type} not available for this turn'
                    }), 400

                card_data = selected_card
            else:
                # RANDOM MODE: Use existing card field
                card_data = consumed_item.get('card', {})

            # Log activity history (only for real cards)
            if card_data and card_data.get('type') != 'LIMIT_REACHED':
                _record_activity_history(
                    card_data=card_data,
                    consumed_item=consumed_item,
                    owner_id=owner_id,
                    anonymous_session_id=anonymous_session_id,
                    session=session,
                    players=players
                )

            # Charge credit (only for real cards, only for free users)
            if owner_id and card_data and card_data.get('type') != 'LIMIT_REACHED':
                _increment_activity_count(owner_id)

        # 2. Update state and replenish queue
        state["queue"] = queue
        session.current_turn_state = state
        flag_modified(session, "current_turn_state")

        queue = _fill_queue(session, target_size=3, owner_id=owner_id, anonymous_session_id=anonymous_session_id)

        # 3. Enforce activity limit
        limit_status, queue = _enforce_activity_limit(
            queue=queue,
            user_id=owner_id,
            anonymous_session_id=anonymous_session_id,
            charge_credit=False
        )

        # 4. Update session and commit
        state["queue"] = queue
        session.current_turn_state = state
        flag_modified(session, "current_turn_state")
        db.session.commit()

        # 5. Response
        return jsonify({
            "session_id": session.session_id,
            "selection_mode": settings.get("selection_mode", "RANDOM").upper(),
            "limit_status": limit_status,
            "queue": queue,
            "current_turn": queue[0] if queue else {}
        })

    except Exception as e:
        # ... existing error handling ...
```

#### 2.2 Extract Activity History Recording

```python
def _record_activity_history(
    card_data: Dict,
    consumed_item: Dict,
    owner_id: Optional[str],
    anonymous_session_id: Optional[str],
    session: Session,
    players: List[Dict]
) -> None:
    """Record played activity to history for repetition prevention."""
    from ..models.activity_history import UserActivityHistory

    cid_str = card_data.get('card_id')
    activity_id = int(cid_str) if cid_str and cid_str.isdigit() else None

    turn_primary_idx = consumed_item.get('primary_player_idx')
    turn_primary_id = None
    if turn_primary_idx is not None and 0 <= turn_primary_idx < len(players):
        turn_primary_id = str(players[turn_primary_idx].get('id'))

    history = UserActivityHistory(
        user_id=owner_id,
        anonymous_session_id=anonymous_session_id,
        session_id=session.session_id,
        activity_id=activity_id,
        activity_type=card_data.get('type', 'TRUTH').lower(),
        primary_player_id=turn_primary_id,
        was_skipped=False,
        presented_at=datetime.utcnow()
    )
    db.session.add(history)
```

---

### Phase 3: Response Format Updates

#### 3.1 Update `start_game()` Response

Add `selection_mode` to response:

```python
return jsonify({
    "session_id": session.session_id,
    "selection_mode": settings.get("selection_mode", "RANDOM").upper(),  # NEW
    "limit_status": limit_status,
    "queue": queue,
    "current_turn": queue[0] if queue else {}
}), 200
```

#### 3.2 Update Limit Card Generation for MANUAL Mode

```python
def _generate_limit_card() -> Dict[str, Any]:
    """Generate a barrier card for activity limit."""
    card_data = {
        "card_id": f"limit-barrier-{uuid.uuid4().hex[:8]}",
        "type": "LIMIT_REACHED",
        "display_text": "Activity limit reached. Tap to unlock unlimited turns.",
        "primary_player": "",
        "secondary_players": [],
        "intensity_rating": 1
    }

    return {
        "status": "SHOW_CARD",
        "primary_player_idx": 0,
        "step": 999,
        "card_id": card_data["card_id"],
        "card": card_data,
        "truth_card": card_data,  # Same limit card for both
        "dare_card": card_data,
        "progress": {
            "current_step": 999,
            "total_steps": 25,
            "intensity_phase": "Limit"
        }
    }
```

---

### Phase 4: Comprehensive Testing

#### 4.1 Create Manual Mode Test File

**File:** `backend/tests/test_gameplay_manual_mode.py`

```python
"""
Tests for manual mode paired cards feature.

Covers:
1. Queue structure in MANUAL vs RANDOM mode
2. selected_type handling in next_turn
3. Activity tracking (only selected card logged)
4. Credit consumption (1 per turn regardless of mode)
5. Edge cases (include_dare: false, limit reached)
"""

import pytest
import uuid
import os
import jwt
from unittest.mock import patch
from src.models.user import User
from src.models.session import Session
from src.models.activity import Activity
from src.models.activity_history import UserActivityHistory


class TestManualModeQueueStructure:
    """Test queue contains paired cards in MANUAL mode."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_start_game_manual_mode_has_paired_cards(self, client, db_session):
        """MANUAL mode queue items have truth_card and dare_card."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="manual@test.com", subscription_tier='premium')
        db_session.add(user)

        # Add activities
        truth_act = Activity(activity_id=1, type="truth", rating="G", intensity=1, script={'steps':[]})
        dare_act = Activity(activity_id=2, type="dare", rating="G", intensity=1, script={'steps':[]})
        db_session.add_all([truth_act, dare_act])
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        resp = client.post('/api/game/start', json={
            "player_ids": [str(user_id)],
            "settings": {"selection_mode": "MANUAL"}
        }, headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        data = resp.get_json()

        assert data['selection_mode'] == 'MANUAL'
        queue = data['queue']
        assert len(queue) >= 1

        first_item = queue[0]
        assert first_item['card'] is None
        assert first_item['card_id'] is None
        assert first_item['truth_card'] is not None
        assert first_item['dare_card'] is not None
        assert first_item['truth_card']['type'] == 'TRUTH'
        assert first_item['dare_card']['type'] == 'DARE'

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_start_game_random_mode_has_single_card(self, client, db_session):
        """RANDOM mode queue items have card but null truth_card/dare_card."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="random@test.com", subscription_tier='premium')
        db_session.add(user)

        act = Activity(activity_id=1, type="truth", rating="G", intensity=1, script={'steps':[]})
        db_session.add(act)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        resp = client.post('/api/game/start', json={
            "player_ids": [str(user_id)],
            "settings": {"selection_mode": "RANDOM"}
        }, headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        data = resp.get_json()

        assert data['selection_mode'] == 'RANDOM'
        queue = data['queue']
        first_item = queue[0]
        assert first_item['card'] is not None
        assert first_item['truth_card'] is None
        assert first_item['dare_card'] is None


class TestManualModeNextTurn:
    """Test next_turn with selected_type in MANUAL mode."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_next_turn_manual_requires_selected_type(self, client, db_session):
        """MANUAL mode returns 400 if selected_type missing."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="m1@test.com", subscription_tier='premium')
        db_session.add(user)

        session_id = str(uuid.uuid4())
        sess = Session(
            session_id=session_id,
            players=[{'id': str(user_id), 'name': 'P1'}],
            game_settings={"selection_mode": "MANUAL"},
            current_turn_state={
                "queue": [{
                    "step": 1,
                    "status": "SHOW_CARD",
                    "card_id": None,
                    "card": None,
                    "truth_card": {"card_id": "1", "type": "TRUTH", "display_text": "Truth?"},
                    "dare_card": {"card_id": "2", "type": "DARE", "display_text": "Dare!"},
                    "primary_player_idx": 0
                }]
            },
            status='active'
        )
        db_session.add(sess)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        # No selected_type
        resp = client.post(f'/api/game/{session_id}/next', json={},
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 400
        assert 'selected_type required' in resp.get_json().get('message', '')

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_next_turn_manual_accepts_truth(self, client, db_session):
        """MANUAL mode accepts selected_type: TRUTH."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="m2@test.com", subscription_tier='premium')
        db_session.add(user)

        act = Activity(activity_id=3, type="truth", rating="G", intensity=1, script={'steps':[]})
        db_session.add(act)

        session_id = str(uuid.uuid4())
        sess = Session(
            session_id=session_id,
            players=[{'id': str(user_id), 'name': 'P1'}],
            game_settings={"selection_mode": "MANUAL"},
            current_turn_state={
                "queue": [{
                    "step": 1,
                    "card_id": None,
                    "card": None,
                    "truth_card": {"card_id": "1", "type": "TRUTH", "display_text": "Truth?"},
                    "dare_card": {"card_id": "2", "type": "DARE", "display_text": "Dare!"},
                    "primary_player_idx": 0,
                    "status": "SHOW_CARD"
                }]
            },
            status='active'
        )
        db_session.add(sess)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        resp = client.post(f'/api/game/{session_id}/next',
                          json={"selected_type": "TRUTH"},
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_next_turn_manual_rejects_unavailable_dare(self, client, db_session):
        """MANUAL mode returns 400 if selecting DARE when dare_card is null."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="m3@test.com", subscription_tier='premium')
        db_session.add(user)

        session_id = str(uuid.uuid4())
        sess = Session(
            session_id=session_id,
            players=[{'id': str(user_id), 'name': 'P1'}],
            game_settings={"selection_mode": "MANUAL", "include_dare": False},
            current_turn_state={
                "queue": [{
                    "step": 1,
                    "card_id": None,
                    "card": None,
                    "truth_card": {"card_id": "1", "type": "TRUTH", "display_text": "Truth?"},
                    "dare_card": None,  # Dares disabled
                    "primary_player_idx": 0,
                    "status": "SHOW_CARD"
                }]
            },
            status='active'
        )
        db_session.add(sess)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        resp = client.post(f'/api/game/{session_id}/next',
                          json={"selected_type": "DARE"},
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 400
        assert 'DARE not available' in resp.get_json().get('message', '')


class TestManualModeActivityTracking:
    """Test only selected card is logged to history."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_only_selected_card_logged(self, client, db_session):
        """When user selects TRUTH, only truth_card is logged."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="track@test.com", subscription_tier='premium')
        db_session.add(user)

        act = Activity(activity_id=99, type="truth", rating="G", intensity=1, script={'steps':[]})
        db_session.add(act)

        session_id = str(uuid.uuid4())
        sess = Session(
            session_id=session_id,
            players=[{'id': str(user_id), 'name': 'P1'}],
            game_settings={"selection_mode": "MANUAL"},
            current_turn_state={
                "queue": [{
                    "step": 1,
                    "card_id": None,
                    "card": None,
                    "truth_card": {"card_id": "100", "type": "TRUTH", "display_text": "Truth?"},
                    "dare_card": {"card_id": "200", "type": "DARE", "display_text": "Dare!"},
                    "primary_player_idx": 0,
                    "status": "SHOW_CARD"
                }]
            },
            status='active'
        )
        db_session.add(sess)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        # Select TRUTH
        resp = client.post(f'/api/game/{session_id}/next',
                          json={"selected_type": "TRUTH"},
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200

        # Check history - only activity 100 should be logged
        history = db_session.query(UserActivityHistory).filter_by(
            session_id=session_id
        ).all()

        assert len(history) == 1
        assert history[0].activity_id == 100
        assert history[0].activity_type == 'truth'


class TestManualModeCreditConsumption:
    """Test credit consumption in MANUAL mode."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_manual_mode_charges_one_credit(self, client, db_session):
        """Free user is charged 1 credit per turn in MANUAL mode."""
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email="credit@test.com",
            subscription_tier='free',
            lifetime_activity_count=5
        )
        db_session.add(user)

        act = Activity(activity_id=1, type="truth", rating="G", intensity=1, script={'steps':[]})
        db_session.add(act)

        session_id = str(uuid.uuid4())
        sess = Session(
            session_id=session_id,
            players=[{'id': str(user_id), 'name': 'P1'}],
            game_settings={"selection_mode": "MANUAL"},
            current_turn_state={
                "queue": [{
                    "step": 1,
                    "card_id": None,
                    "card": None,
                    "truth_card": {"card_id": "1", "type": "TRUTH", "display_text": "Truth?"},
                    "dare_card": {"card_id": "2", "type": "DARE", "display_text": "Dare!"},
                    "primary_player_idx": 0,
                    "status": "SHOW_CARD"
                }]
            },
            status='active'
        )
        db_session.add(sess)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        resp = client.post(f'/api/game/{session_id}/next',
                          json={"selected_type": "TRUTH"},
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200

        # Check credit incremented by 1 (not 2 for pair)
        db_session.refresh(user)
        assert user.lifetime_activity_count == 6  # Was 5, now 6

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_manual_mode_limit_reached(self, client, db_session):
        """Free user at limit gets limit cards in MANUAL mode."""
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email="limit@test.com",
            subscription_tier='free',
            lifetime_activity_count=10  # At limit
        )
        db_session.add(user)

        act = Activity(activity_id=1, type="truth", rating="G", intensity=1, script={'steps':[]})
        db_session.add(act)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        resp = client.post('/api/game/start', json={
            "player_ids": [str(user_id)],
            "settings": {"selection_mode": "MANUAL"}
        }, headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
        data = resp.get_json()

        # Limit cards should appear
        assert data['limit_status']['limit_reached'] is True
        # Queue should have limit cards
        queue = data['queue']
        has_limit_card = any(
            item.get('truth_card', {}).get('type') == 'LIMIT_REACHED'
            for item in queue
        )
        assert has_limit_card


class TestRandomModeUnchanged:
    """Verify RANDOM mode behavior is unchanged."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_random_mode_ignores_selected_type(self, client, db_session):
        """RANDOM mode works even if selected_type is provided."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="rand@test.com", subscription_tier='premium')
        db_session.add(user)

        act = Activity(activity_id=1, type="truth", rating="G", intensity=1, script={'steps':[]})
        db_session.add(act)

        session_id = str(uuid.uuid4())
        sess = Session(
            session_id=session_id,
            players=[{'id': str(user_id), 'name': 'P1'}],
            game_settings={"selection_mode": "RANDOM"},
            current_turn_state={
                "queue": [{
                    "step": 1,
                    "card_id": "1",
                    "card": {"card_id": "1", "type": "TRUTH", "display_text": "Truth?"},
                    "truth_card": None,
                    "dare_card": None,
                    "primary_player_idx": 0,
                    "status": "SHOW_CARD"
                }]
            },
            status='active'
        )
        db_session.add(sess)
        db_session.commit()

        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")

        # selected_type should be ignored in RANDOM mode
        resp = client.post(f'/api/game/{session_id}/next',
                          json={"selected_type": "DARE"},  # Ignored
                          headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code == 200
```

#### 4.2 Run Full Test Suite

```bash
# Run new manual mode tests
python -m pytest tests/test_gameplay_manual_mode.py -v

# Run all gameplay tests to ensure no regressions
python -m pytest tests/test_gameplay_*.py -v

# Run with coverage
python -m pytest tests/test_gameplay_*.py --cov=src/routes/gameplay --cov-report=term-missing
```

---

### Phase 5: Integration Testing Checklist

| Test Case | Expected Result | Status |
|-----------|-----------------|--------|
| Start game RANDOM mode | `card` populated, `truth_card`/`dare_card` null | |
| Start game MANUAL mode | `card` null, `truth_card`/`dare_card` populated | |
| NextTurn MANUAL without selected_type | 400 Bad Request | |
| NextTurn MANUAL with selected_type: TRUTH | 200, TRUTH card consumed | |
| NextTurn MANUAL with selected_type: DARE | 200, DARE card consumed | |
| NextTurn MANUAL selecting unavailable DARE | 400 Bad Request | |
| NextTurn RANDOM mode (no selected_type) | 200, works as before | |
| NextTurn RANDOM mode (with selected_type) | 200, selected_type ignored | |
| Activity history MANUAL mode | Only selected card logged | |
| Credit charge MANUAL mode | 1 credit per turn (not 2) | |
| Free user limit MANUAL mode | Limit cards for both truth/dare | |
| Premium user MANUAL mode | No credit tracking | |

---

### Phase 6: Deployment & Rollback

#### 6.1 Pre-Deployment Checklist

- [ ] All tests passing locally
- [ ] Code reviewed
- [ ] API documentation updated
- [ ] Commit follows conventional format

#### 6.2 Deployment Steps

```bash
# Final rebase
git fetch origin
git rebase origin/develop

# Push feature branch
git push -u origin feature/manual-mode-paired-cards

# Create PR
gh pr create --title "feat: implement manual mode paired cards" --body "$(cat <<'EOF'
## Summary
Implements paired cards for manual mode gameplay:
- Queue items contain both `truth_card` and `dare_card` in MANUAL mode
- Frontend picks which to display based on user selection
- Backend tracks only the selected card via `selected_type` parameter
- One credit charged per turn regardless of mode

## Changes
- Modified `_generate_turn_data()` to generate both card types in MANUAL mode
- Updated `next_turn()` to read `selected_type` and consume correct card
- Added `selection_mode` to response for frontend awareness
- Added comprehensive tests for manual mode behavior

## Test Plan
- [x] MANUAL mode queue has paired cards
- [x] RANDOM mode unchanged
- [x] selected_type required in MANUAL mode
- [x] Only selected card logged to history
- [x] One credit per turn charged
- [x] Limit cards work in MANUAL mode

## Related
Closes #XXX (Manual mode bug)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

#### 6.3 Rollback Plan

If issues in production:
```bash
git revert <merge-commit-hash>
git push origin develop
```

---

## File Changes Summary

| File | Changes |
|------|---------|
| `backend/src/routes/gameplay.py` | Add `_generate_single_card()`, modify `_generate_turn_data()`, modify `next_turn()`, add `_record_activity_history()`, update `_generate_limit_card()` |
| `backend/tests/test_gameplay_manual_mode.py` | New test file (~200 lines) |
| `docs/API_DOCUMENTATION.md` | Document `selection_mode` in responses, `selected_type` behavior |

---

## Success Criteria

1. **Functional:** Manual mode shows correct content for user's selection
2. **Billing:** Free users charged 1 credit per turn (not 2)
3. **Tracking:** Only selected activity appears in history
4. **Regression:** RANDOM mode behavior unchanged
5. **Tests:** All new and existing gameplay tests pass

---

## Agents & Skills to Leverage

| Agent/Skill | Purpose |
|-------------|---------|
| `gameplay-engineer` | Owns gameplay.py - primary implementer |
| `qa-tester` | Run comprehensive test suite |
| `attuned-testing` | Test patterns and fixtures |
| `attuned-git-workflow` | Branch/commit conventions |
| `code-reviewer` | Review implementation before merge |

---

*Plan created: February 1, 2026*
*Ready for implementation*
