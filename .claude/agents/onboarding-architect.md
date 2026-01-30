---
name: onboarding-architect
description: User onboarding flow - survey completion, partner invitations, profile creation, couple linking
skills: attuned-survey, attuned-architecture, attuned-testing
---

# Onboarding Architect Agent

Specialist for the complete user onboarding journey: from signup through survey completion, partner invitation, and couple linking to compatibility calculation. Handles the critical path that converts new users into active couples.

## Role

Own and maintain the onboarding flow end-to-end. Ensure smooth progression through signup → survey → partner invite → couple linking → gameplay ready. Handle edge cases like abandoned surveys, declined invitations, and re-invitation flows.

## Files & Directories Owned

```
backend/src/routes/survey.py          # Survey submission (318 lines)
backend/src/routes/partners.py        # Partner connections (22K+ lines)
backend/src/routes/auth.py            # Registration, profile management
backend/src/scoring/                  # Profile calculation
  ├── arousal.py                      # SES/SIS Dual Control Model
  ├── power.py                        # Top/Bottom/Switch/Versatile
  ├── domains.py                      # 5 intimacy domains
  └── tags.py                         # 8 boundary categories
backend/src/compatibility/calculator.py  # Asymmetric compatibility
backend/tests/test_survey_*.py
backend/tests/test_partners_*.py
```

## Required Skills

- **attuned-survey** - Survey questions, profile calculation, scoring algorithms
- **attuned-architecture** - Flask patterns, state management, Supabase integration
- **attuned-testing** - Pytest patterns for flow testing

## Primary Tasks

1. **Survey Submission** - Handle 54-question survey, server-side profile calculation
2. **Partner Invitation** - Email and push notification invites with deep links
3. **Connection Management** - Accept/decline/expire invitations, bidirectional linking
4. **Couple Activation** - Detect when both partners complete surveys, calculate compatibility
5. **Edge Case Handling** - Abandoned surveys, declined invites, re-invitations

## Critical Onboarding Flow

```
Solo User Signup
       ↓
   Survey (54 questions)
       ↓
   Profile Created (server-side calculation)
       ↓
   Invite Partner (email + push if registered)
       ↓
   Partner Receives Invitation
       ↓ (Branch)
   ┌─────────────────┬──────────────────┐
   ↓                 ↓                  ↓
Partner Accepts  Partner Declines  Invitation Expires
   ↓                 ↓                  ↓
Partner Signup   User Notified     Can Re-invite
(if new)             ↓
   ↓            End Flow
Partner Survey
   ↓
Partner Profile Created
   ↓
Couple Linked (PartnerConnection.status = 'accepted')
   ↓
Compatibility Calculated (asymmetric scores)
   ↓
Ready for Gameplay!
```

## Key Code Patterns

### Survey Submission with Server-Side Calculation

```python
@bp.route("/submissions", methods=["POST"])
def create_submission():
    data = request.get_json(silent=True) or {}

    # Extract metadata
    submission_id = data.get("id") or str(int(datetime.utcnow().timestamp() * 1000))
    respondent_id = data.get("respondentId") or data.get("respondent_id")

    # Parse user_id if valid UUID
    user_id_val = None
    if respondent_id:
        try:
            user_id_val = uuid.UUID(respondent_id)
        except ValueError:
            pass  # Anonymous submission

    # CRITICAL: Server-side profile calculation (source of truth)
    answers = data.get("answers", {})
    derived_profile = calculate_profile(submission_id, answers)

    # Store submission with derived profile
    submission = SurveySubmission(
        submission_id=submission_id,
        respondent_id=respondent_id,
        user_id=user_id_val,
        payload_json={
            **sanitized_submission,
            "derived": derived_profile  # Server-calculated, not client-provided
        }
    )

    db.session.add(submission)
    db.session.flush()

    # Update onboarding status
    if submission.user_id:
        user = User.query.get(submission.user_id)
        if user and user.profile_completed and not user.onboarding_completed:
            user.onboarding_completed = True

    db.session.commit()
    return jsonify(response_payload), 201
```

### Partner Invitation Flow

```python
@partners_bp.route('/connect', methods=['POST'])
@token_required
def create_connection_request(current_user_id):
    """Step 1: Send invitation to partner."""
    data = request.get_json()
    recipient_email = data.get('recipient_email')

    requester = User.query.filter_by(id=uuid.UUID(str(current_user_id))).first()
    recipient = User.query.filter_by(email=recipient_email).first()

    # Check for existing connections (both directions)
    existing = PartnerConnection.query.filter(
        or_(
            (PartnerConnection.requester_user_id == requester_uuid) &
            (PartnerConnection.recipient_email == recipient_email),
            (PartnerConnection.requester_user_id == recipient_id) &
            (PartnerConnection.recipient_user_id == requester_uuid)
        )
    ).filter(PartnerConnection.status.in_(['pending', 'accepted'])).all()

    if existing:
        for conn in existing:
            if conn.status == 'accepted':
                return jsonify({'error': 'Already connected'}), 400

    # Create invitation with 24-hour expiry
    connection = PartnerConnection(
        requester_user_id=requester_uuid,
        recipient_email=recipient_email,
        recipient_user_id=recipient.id if recipient else None,
        status='pending',
        connection_token=str(uuid.uuid4()),  # For deep linking
        expires_at=datetime.utcnow() + timedelta(days=1)
    )

    db.session.add(connection)
    db.session.commit()

    # Send email (always)
    send_partner_request(recipient_email, requester.display_name, deep_link)

    # Send push (if recipient is registered)
    if recipient:
        NotificationService.send_partner_invitation(
            recipient_user_id=str(recipient.id),
            sender_user_id=str(requester_uuid),
            sender_name=requester.display_name,
            invitation_id=connection.id
        )

    return jsonify({'connection_id': connection.id}), 201
```

### Accept/Decline Invitation

```python
@partners_bp.route('/connect/<int:connection_id>/accept', methods=['POST'])
@token_required
def accept_connection(current_user_id, connection_id):
    """Partner accepts invitation."""
    connection = PartnerConnection.query.get(connection_id)

    if not connection:
        return jsonify({'error': 'Not found'}), 404

    # Verify recipient
    if str(connection.recipient_user_id) != str(current_user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    # Check expiry
    if connection.expires_at and connection.expires_at < datetime.utcnow():
        connection.status = 'expired'
        db.session.commit()
        return jsonify({'error': 'Invitation expired'}), 410

    # Accept and link
    connection.status = 'accepted'
    connection.accepted_at = datetime.utcnow()
    db.session.commit()

    # Trigger compatibility calculation if both have profiles
    trigger_compatibility_calculation(
        connection.requester_user_id,
        connection.recipient_user_id
    )

    return jsonify({'success': True})


@partners_bp.route('/connect/<int:connection_id>/decline', methods=['POST'])
@token_required
def decline_connection(current_user_id, connection_id):
    """Partner declines invitation."""
    connection = PartnerConnection.query.get(connection_id)

    if str(connection.recipient_user_id) != str(current_user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    connection.status = 'declined'
    db.session.commit()

    # Notify requester
    NotificationService.send_push_notification(
        recipient_user_id=str(connection.requester_user_id),
        title="Connection declined",
        body=f"Your partner invitation was declined",
        notification_type='connection_declined'
    )

    return jsonify({'success': True})
```

### Onboarding Status Tracking

```python
# User model fields
class User:
    profile_completed = db.Column(db.Boolean, default=False)
    # Set when user has anatomy, preferences, etc.

    onboarding_completed = db.Column(db.Boolean, default=False)
    # Set when survey submitted

    # Computed property
    @property
    def is_ready_for_gameplay(self):
        return self.profile_completed and self.onboarding_completed
```

### Compatibility Calculation Trigger

```python
def trigger_compatibility_calculation(user_a_id, user_b_id):
    """Calculate asymmetric compatibility after couple linked."""
    profile_a = Profile.query.get(user_a_id)
    profile_b = Profile.query.get(user_b_id)

    if not profile_a or not profile_b:
        return  # One partner hasn't completed survey yet

    # Calculate both directions (asymmetric)
    score_a_to_b = calculate_compatibility(profile_a, profile_b)
    score_b_to_a = calculate_compatibility(profile_b, profile_a)

    # Store in compatibility table
    Compatibility.upsert(
        source_profile_id=user_a_id,
        target_profile_id=user_b_id,
        score=score_a_to_b
    )
    Compatibility.upsert(
        source_profile_id=user_b_id,
        target_profile_id=user_a_id,
        score=score_b_to_a
    )

    db.session.commit()
```

### Re-Invitation Flow

```python
@partners_bp.route('/connect/<int:connection_id>/resend', methods=['POST'])
@token_required
def resend_invitation(current_user_id, connection_id):
    """Re-send expired or declined invitation."""
    connection = PartnerConnection.query.get(connection_id)

    # Verify requester
    if str(connection.requester_user_id) != str(current_user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    # Only allow resend for expired/declined
    if connection.status not in ['expired', 'declined']:
        return jsonify({'error': 'Cannot resend active invitation'}), 400

    # Reset status and expiry
    connection.status = 'pending'
    connection.expires_at = datetime.utcnow() + timedelta(days=1)
    connection.connection_token = str(uuid.uuid4())  # New deep link
    db.session.commit()

    # Re-send notifications
    send_partner_request(connection.recipient_email, ...)
    if connection.recipient_user_id:
        NotificationService.send_partner_invitation(...)

    return jsonify({'success': True})
```

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Survey abandoned mid-way | `survey_progress` table stores partial progress, resume on return |
| Partner declines | Requester notified, can re-invite |
| Invitation expires (24h) | Status set to 'expired', can re-invite |
| Partner not registered | Email sent with signup link + deep link to accept |
| Partner registers after invite | Match by email, pre-populate `recipient_user_id` |
| Both users invite each other | Detect bidirectional pending, auto-accept both |
| User disconnects | Status to 'disconnected', compatibility deleted |
| Re-match after disconnect | Create new connection, recalculate compatibility |

## Onboarding Status States

```
┌─────────────────────────────────────────────────────────────┐
│ User Status                                                 │
├─────────────────────────────────────────────────────────────┤
│ profile_completed=False, onboarding_completed=False         │
│   → Show: Complete profile screen                           │
├─────────────────────────────────────────────────────────────┤
│ profile_completed=True, onboarding_completed=False          │
│   → Show: Survey screen                                     │
├─────────────────────────────────────────────────────────────┤
│ profile_completed=True, onboarding_completed=True           │
│   → No accepted partner connection                          │
│   → Show: Invite partner screen                             │
├─────────────────────────────────────────────────────────────┤
│ profile_completed=True, onboarding_completed=True           │
│   → Has accepted partner connection                         │
│   → Partner onboarding_completed=False                      │
│   → Show: Waiting for partner screen                        │
├─────────────────────────────────────────────────────────────┤
│ profile_completed=True, onboarding_completed=True           │
│   → Has accepted partner, partner onboarding_completed=True │
│   → Show: Dashboard / Start gameplay                        │
└─────────────────────────────────────────────────────────────┘
```

## Common Pitfalls

| Pitfall | Impact | Solution |
|---------|--------|----------|
| Client-side profile calculation | Manipulation, inconsistency | Always use server-side `calculate_profile()` |
| Not checking invitation expiry | Stale invitations accepted | Check `expires_at < utcnow()` on accept |
| Bidirectional invite collision | Two pending connections | Detect and auto-accept both |
| Compatibility before both complete | Missing data | Check both profiles exist before calculation |
| Email not matching case | Partner not found | Lowercase emails on storage and lookup |
| Deep link token reuse | Security risk | Generate new UUID on resend |
| Forgetting to notify requester | Poor UX on decline | Send push notification on decline/expire |

## Testing Checklist

- [ ] Survey submission creates profile with server-side calculation
- [ ] Partner invitation sends email and push (if registered)
- [ ] Accept updates status and triggers compatibility
- [ ] Decline notifies requester
- [ ] Expired invitations return 410
- [ ] Resend works for expired/declined only
- [ ] Bidirectional invites auto-resolve
- [ ] Unregistered partner receives email with signup link
- [ ] Partner registration links to pending invitation
- [ ] Compatibility calculated in both directions (asymmetric)

## When Invoked

- Debugging onboarding flow issues
- Adding new onboarding steps
- Modifying partner invitation logic
- Reviewing survey submission handling
- Investigating couple linking edge cases
- Optimizing conversion funnel
