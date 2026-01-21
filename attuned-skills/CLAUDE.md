# Attuned Claude Code Skills

Custom skills and agents for Attuned backend development.

## Skills

| Skill | Description |
|-------|-------------|
| `attuned-architecture` | System design, Flask/Supabase patterns |
| `attuned-testing` | Pytest, auth tests, E2E flows |
| `attuned-ai-activities` | Groq/Llama integration, prompts |
| `attuned-activity-bank` | Activity data management |
| `attuned-survey` | Survey scoring, SES/SIS model |
| `attuned-payments` | Stripe subscription backend |

## Agents

| Agent | Purpose |
|-------|---------|
| `qa-tester` | Run test suites |
| `activity-manager` | Manage activity bank |
| `survey-analyst` | Survey/compatibility logic |
| `payment-implementer` | Stripe integration |

## Usage

Skills trigger automatically. Agents can be invoked explicitly.

## Stack Reference

- Backend: Python 3.11+ / Flask
- Database: PostgreSQL via Supabase
- Auth: Supabase JWT
- AI: Groq + Llama 3.3 70B
- Frontend: FlutterFlow (read-only)
