# Attuned API Documentation

## Authentication & Security
All protected endpoints require a valid Supabase JWT in the Authorization header:
`Authorization: Bearer <your_access_token>`

The backend validates:
- Token format/signature (HMAC HS256)
- Expiration (`exp`)
- Audience (`aud="authenticated"`)
- Subject (`sub`) matches request parameters where applicable (Ownership Enforcement).

## Rate Limiting
Global rate limits are enforced to protect the API:
- **Daily Limit**: 2000 requests per IP per day.
- **Hourly Limit**: 500 requests per IP per hour.
- Exceeding limits returns `429 Too Many Requests`.

## Authentication (`/api/auth`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/register` | Register a new user after Supabase Auth signup. |
| `POST` | `/login` | Update last login timestamp. |
| `GET` | `/profile` | Get authenticated user details. |
| `PATCH` | `/profile` | Update user profile (display name, demographics, etc.). |
| `DELETE` | `/profile` | Delete user account and all associated data. |
| `POST` | `/complete-demographics` | Mark demographics as complete (onboarding). |
| `GET` | `/users/profile-ui` | Get derived profile data formatted for UI. |

### User Profile UI
### User Profile UI
`GET /api/users/profile-ui`

**Auth Required**: User ID extracted from token.

Returns the calculated profile data (arousal, power, domains, etc.) formatted for the frontend.

**Response:**
```json
{
  "user_id": "uuid",
  "display_name": "User Name", // Added for personalization
  "submission_id": "sub_123",
  "general": {
    "arousal_profile": { ... },
    "power": { ... },
    "domains": [ ... ],
    "boundaries": [ ... ]
  },
  "interests": [ ... ]
}
```

## Partner Connections (`/api/partners`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/connect` | Send a connection request to another user by email. |
| `GET` | `/connections` | Get active connection requests (pending, accepted) for authenticated user. |
**Endpoint:** `POST /api/partners/connections/<connection_id>/accept`

**Description:** Accept a pending connection request.

**Request Body:**
```json
{
  "recipient_user_id": "uuid" // Optional if user already exists in system
}
```

**Response:**
```json
{
  "message": "Connection accepted",
  "connection": { ... }
}
```
| `POST` | `/connections/<connection_id>/decline` | Decline a connection request. |
| `GET` | `/remembered` | Get list of remembered partners (quick reconnect). |
| `DELETE` | `/remembered/<partner_id>` | Remove a remembered partner. |

## Notifications (`/api/notifications`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/register` | Register a device token (FCM/APNs) for push notifications. |

## Recommendations (`/api/recommendations`)

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| `POST` | `/` | Generate activity recommendations for a new game session. | **Optional** (If logged in, checks ownership of profiles) |
| `GET` | `/<session_id>` | Get activities for an existing session. | **Required** (Must be a participant) |
| `POST` | `/<session_id>/activities/<activity_id>/feedback` | Submit feedback (like/dislike) for an activity. | **Optional** (Required if user_id provided) |

## Compatibility (`/api/compatibility`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/` | Calculate compatibility between two players. |
| `GET` | `/api/survey/compatibility/<sub_a>/<sub_b>` | Get compatibility by **Submission ID** (Anonymous/Debug). |
| `GET` | `/api/compatibility/<user_a>/<user_b>` | Get compatibility by **User ID** (Authenticated). |

### Compatibility Scoring (User-Based)
`GET /api/compatibility/<user_id>/<partner_id>`

Returns the calculated compatibility score and details between a user and their partner. The response is filtered according to the partner's privacy settings:
- `demographics_only`: Returns only the overall score and interpretation.
- `overlapping_only`: Returns score, detailed breakdown, mutual interests/topics, and filtered overlapping profile data.
- `all_responses`: Returns score, detailed breakdown, and full partner profile.

**Response (Example - Overlapping Only):**
```json
{
  "overall_compatibility": {
    "score": 85,
    "interpretation": "Exceptional compatibility"
  },
  "sharing_setting": "overlapping_only",
  "calculation_date": "2023-10-27T10:00:00",
  "breakdown": {
    "power_complement": 90,
    "domain_similarity": 60,
    "activity_overlap": 80,
    "truth_overlap": 70
  },
  "mutual_activities": ["kissing", "cuddling"],
  "growth_opportunities": ["massage"],
  "mutual_truth_topics": ["fantasies"],
  "blocked_activities": {
    "reason": "hard_boundaries",
    "activities": ["choking"]
  },
  "boundary_conflicts": []
}
```

### Compatibility UI (Optimized)
`GET /api/compatibility/<user_id>/<partner_id>/ui`

Returns a flattened, null-safe response designed for the frontend summary page.
- **Strict Domain Order**: Sensation, Connection, Power, Exploration, Verbal.
- **Smart Matching**: "Giving" and "Receiving" pairs are marked as "mutual".
- **Conflict Detection**: Checks "Hard Limits" against partner interests.

**Response:**
```json
{
  "compatibility_summary": {
    "overall_score": 85,
    "comparison_scores": {
      "power_score": 90,
      "domain_score": 60,
      "activity_score": 80,
      "truth_score": 70
    },
    "sharing_setting": "overlapping_only"
  },
  "comparison_data": {
    "domains": [
      { "domain": "Sensation", "user_score": 64, "partner_score": 70 },
      ...
    ],
    "power_overlap": {
      "user_label": "Bottom",
      "partner_label": "Top",
      "complement_score": 90
    },
    "arousal": {
      "user_sexual_excitation": 0.5,
      "partner_sexual_excitation": 0.6
      // ...
    }
  },
  "interests_comparison": [
    {
      "section": "Physical Touch",
      "tags": [
        { "name": "Massage (Receiving)", "status": "mutual", "compatible": true },
        { "name": "Spanking", "status": "conflict", "compatible": false }
      ]
    }
  ],
  "partner_profile": {
     // Standard profile-ui structure (General, Power, Domains, Interests)
     "general": { ... },
     "interests": [ ... ]
  }
}
```

## Gameplay (`/api/game`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/start` | Start a new N-player game session. |
| `POST` | `/<session_id>/next` | Advance turn, rotate players, and get next activity. |

### 1. Start Game
`POST /api/game/start`

Start a new game session. Returns a queue of 3 cards to minimize latency.

**Credit Consumption:** Consumes **1 credit** immediately (for the first card).

#### Payload
You can provide either a list of IDs (`player_ids`) OR a list of full player objects (`players`). Use `players` to support **Guest Players** (users without accounts).

**Option 1: Registered Users Only (Legacy)**
```json
{
  "player_ids": ["uuid1", "uuid2"],
  "settings": { ... }
}
```

**Option 2: Guest Players (Preferred for Mixed/Guest Groups)**
Guest players allow you to specify anatomy and preferences directly.
```json
{
  "players": [
    { "id": "uuid1" }, // Registered user (ID only)
    {
      "id": "guest-uuid", // Optional, generated if missing
      "name": "Guest Name",
      "anatomy": ["penis"], // HAS: penis, vagina, breasts
      "anatomy_preference": ["vagina", "breasts"] // LIKES: Defaults to ["penis", "vagina", "breasts"] if omitted
    }
  ],
  "settings": {
    "intimacy_level": 3,
    "player_order_mode": "SEQUENTIAL",
    "selection_mode": "RANDOM",
    "include_dare": true
  }
}
```

#### Response
- `status`: 200 OK
- `limit_status`: Object describing usage (e.g. `{ "limit_reached": true }`).
- `queue`: Array of turn objects. **NOTE:** If the daily limit is reached, cards will have `type: "LIMIT_REACHED"`.

#### Card Object (Limit Reached)
When the limit is reached, the card object will look like this:
```json
{
  "type": "LIMIT_REACHED",
  "display_text": "Daily limit reached. Tap to unlock unlimited turns.",
  "intensity_rating": 1,
  "card_id": "limit-barrier-..."
}
```
The frontend should display a subscription prompt for this card type.
```json
{
  "session_id": "uuid",
  "limit_status": {
    "limit_reached": false,
    "remaining": 24,
    "is_capped": true
  },
  "queue": [
    {
      "status": "SHOW_CARD",
      "step": 1,
      "card_id": "101",
      "card": {
        "card_id": "101",
        "type": "TRUTH",
        "primary_player": "Alice",
        "secondary_players": ["Bob"],
        "display_text": "Tell Bob a secret.",
        "intensity_rating": 1
      },
      "progress": { ... }
    },
    { ... },
    { ... }
  ],
  "current_turn": { ... } // Legacy support (Head of queue)
}
```

### 2. Next Turn
`POST /api/game/<session_id>/next`

Advance to the next turn. Consumes the current card (head of queue) and generates a new one at the end to maintain a buffer of 3.

**Credit Consumption:** Consumes **1 credit** for the card that was just played/skipped.

#### Payload
```json
{
  "action": "NEXT",
  "selected_type": "TRUTH" // Optional
}
```

#### Response
```json
{
  "session_id": "uuid",
  "limit_status": { ... },
  "queue": [ ... ], // Updated queue of 3 items
  "current_turn": { ... } // The new head of the queue
}
```

## Survey (`/api/survey`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/submissions` | Get all survey submissions (Admin). |
| `POST` | `/submissions` | Submit a raw survey response (Anonymous/Legacy). |
| `GET` | `/submissions/<submission_id>` | Get a specific submission. |
| `POST` | `/submit` | **Atomic User Submission**: Submit survey, calculate profile, and update user status. **(PREFERRED)** |

### Atomic Survey Submission
`POST /api/survey/submit`

Submits survey answers, calculates the profile, updates the user's onboarding status, and marks the survey progress as complete in a single atomic transaction.

**Headers:**
- `Authorization`: `Bearer <JWT>`

**Request Body:**
```json
{
  "survey_version": "0.4",
  "retake": true, // Optional: Set to true to force a retake (creates new profile version)
  "answers": {
    "A1": 5,
    "B1a": "Y",
    ...
  }
}
```

**Parameters:**
- `retake` (boolean, optional): If `true`, allows submitting a new survey even if a previous one exists. Creates a new `Profile` and `SurveySubmission` record while preserving history. Defaults to `false` (which blocks duplicates).

**Response:**
```json
{
  "message": "Survey submitted successfully",
  "profile_id": 123
}
```

## Profile Sharing (`/api/profile-sharing`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/settings` | Get user's profile sharing settings. |
| `PUT` | `/settings` | Update user's profile sharing settings. |
| `GET` | `/partner-profile/<partner_id>` | Get partner's profile data. |

## Admin / Utility

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/validate-token` | Validate Supabase JWT token. |
| `GET` | `/api/survey/baseline` | Get the current baseline submission ID. |
| `POST` | `/api/survey/baseline` | Set a submission as the baseline. |
| `DELETE` | `/api/survey/baseline` | Clear the baseline. |
| `GET` | `/api/survey/export` | Export all survey data. |
