# Attuned API Documentation

## Authentication (`/api/auth`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/register` | Register a new user after Supabase Auth signup. |
| `POST` | `/login` | Update last login timestamp. |
| `GET` | `/user/<user_id>` | Get user details.
```json
{
    "user": {
        "id": "uuid",
        "submission_id": "string", // Linked survey submission ID
        "email": "user@example.com"
        // ... other fields
    }
}
```
| `PATCH` | `/user/<user_id>` | Update user profile (display name, demographics, etc.). |
| `DELETE` | `/user/<user_id>` | Delete user account and all associated data. |
| `POST` | `/user/<user_id>/complete-demographics` | Mark demographics as complete (onboarding). |

## Partner Connections (`/api/partners`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/connect` | Send a connection request to another user by email. |
| `GET` | `/connections/<user_id>` | Get all connection requests (sent and received) for a user. |
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
| `GET` | `/remembered/<user_id>` | Get list of remembered partners (quick reconnect). |
| `DELETE` | `/remembered/<user_id>/<partner_id>` | Remove a remembered partner. |

## Notifications (`/api/notifications`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/register` | Register a device token (FCM/APNs) for push notifications. |

## Recommendations (`/api/recommendations`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/` | Generate activity recommendations for a new game session. |
| `GET` | `/<session_id>` | Get activities for an existing session. |
| `POST` | `/<session_id>/activities/<activity_id>/feedback` | Submit feedback (like/dislike) for an activity. |

## Compatibility (`/api/compatibility`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/` | Calculate compatibility between two players. |
| `GET` | `/<sub_a>/<sub_b>` | Get stored compatibility result. |

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
```json
{
  "player_ids": ["uuid1", "uuid2"],
  "settings": {
    "intimacy_level": 3,
    "player_order_mode": "SEQUENTIAL",
    "selection_mode": "RANDOM",
    "include_dare": true
  }
}
```

#### Response
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
| `GET` | `/submissions` | Get all survey submissions. |
| `POST` | `/submissions` | Submit a new survey response. |
| `GET` | `/submissions/<submission_id>` | Get a specific submission. |

## Profile Sharing (`/api/profile-sharing`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/settings/<user_id>` | Get user's profile sharing settings. |
| `PUT` | `/settings/<user_id>` | Update user's profile sharing settings. |
| `GET` | `/partner-profile/<requester_id>/<partner_id>` | Get partner's profile data (filtered by their sharing settings). |

## Admin / Utility

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/validate-token` | Validate Supabase JWT token. |
| `GET` | `/api/survey/baseline` | Get the current baseline submission ID. |
| `POST` | `/api/survey/baseline` | Set a submission as the baseline. |
| `DELETE` | `/api/survey/baseline` | Clear the baseline. |
| `GET` | `/api/survey/export` | Export all survey data. |
