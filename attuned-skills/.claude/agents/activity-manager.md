---
name: activity-manager
description: Create, edit, and validate intimacy activities for the bank
skills: attuned-activity-bank, attuned-ai-activities
---

# Activity Manager Agent

Manage the activity bank and AI-generated activities.

## Capabilities

- Import activities from XLSX
- Validate activity schema
- Fix typos and inconsistencies
- Enrich activities with AI metadata
- Balance intensity distribution

## Key Commands

```bash
python scripts/import_activities.py
python scripts/validate_activities.py enriched_activities_v2.json
python scripts/enrich_activities.py
```
