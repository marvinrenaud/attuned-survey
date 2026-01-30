# Attuned Claude Code Setup Guide

## Quick Install

```bash
# 1. Install Superpowers (foundation)
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace

# 2. Install Supabase tools
npx claude-code-templates@latest --mcp database/supabase

# 3. Install Stripe skill
/plugin install stripe-best-practices

# 4. Copy Attuned custom skills to your project
# Extract attuned-skills.zip and copy .claude/ folder to your backend repo:
cp -r attuned-skills/.claude /path/to/attuned-survey-main/
```

## Directory Structure After Setup

```
attuned-survey-main/
├── .claude/
│   ├── skills/
│   │   ├── attuned-architecture/SKILL.md
│   │   ├── attuned-testing/SKILL.md
│   │   ├── attuned-ai-activities/SKILL.md
│   │   ├── attuned-activity-bank/SKILL.md
│   │   ├── attuned-survey/SKILL.md
│   │   └── attuned-payments/SKILL.md
│   └── agents/
│       ├── qa-tester.md
│       ├── activity-manager.md
│       ├── survey-analyst.md
│       └── payment-implementer.md
├── backend/
│   └── ... (your existing code)
└── CLAUDE.md  # Keep your existing comprehensive CLAUDE.md
```

## Verify Installation

```bash
claude
> /help
# Should show superpowers commands: /brainstorm, /write-plan, /execute-plan

> What skills are available?
# Should list all attuned-* skills
```

## Recommended Workflow

1. **New Feature**: `/superpowers:brainstorm` → Design discussion
2. **Plan**: `/superpowers:write-plan` → Detailed implementation plan
3. **Execute**: `/superpowers:execute-plan` → TDD implementation
4. **Test**: Invoke `qa-tester` agent for full test suite

## Plugin Summary

| Plugin | Purpose |
|--------|---------|
| `superpowers` | Brainstorm, plan, TDD, debugging |
| `supabase-mcp` | Direct DB access |
| `stripe-best-practices` | Payment integration patterns |
| `attuned-*` (custom) | Domain-specific knowledge |

## Notes

- Skills trigger automatically based on context
- Your existing `CLAUDE.md` provides comprehensive project context
- FlutterFlow frontend is read-only from Claude Code
- Always run tests before merging
