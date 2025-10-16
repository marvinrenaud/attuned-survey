"""JSON Schema for Groq activity recommendation output."""

# JSON Schema for a single activity output
ACTIVITY_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["id", "seq", "type", "rating", "intensity", "roles", "script", "tags", "provenance", "checks"],
    "properties": {
        "id": {
            "type": "string",
            "description": "Unique identifier for this activity instance"
        },
        "seq": {
            "type": "integer",
            "minimum": 1,
            "maximum": 30,
            "description": "Sequence number in the session (1-25 typically)"
        },
        "type": {
            "type": "string",
            "enum": ["truth", "dare"],
            "description": "Activity type"
        },
        "rating": {
            "type": "string",
            "enum": ["G", "R", "X"],
            "description": "Content rating"
        },
        "intensity": {
            "type": "integer",
            "minimum": 1,
            "maximum": 5,
            "description": "Intensity level (1=gentle, 5=extreme)"
        },
        "roles": {
            "type": "object",
            "required": ["active_player", "partner_player"],
            "properties": {
                "active_player": {
                    "type": "string",
                    "enum": ["A", "B"],
                    "description": "Player performing the action"
                },
                "partner_player": {
                    "type": "string",
                    "enum": ["A", "B"],
                    "description": "Partner player"
                }
            }
        },
        "script": {
            "type": "object",
            "required": ["steps"],
            "properties": {
                "steps": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 2,
                    "items": {
                        "type": "object",
                        "required": ["actor", "do"],
                        "properties": {
                            "actor": {
                                "type": "string",
                                "enum": ["A", "B"],
                                "description": "Player performing this step"
                            },
                            "do": {
                                "type": "string",
                                "minLength": 6,
                                "maxLength": 100,
                                "description": "Action description (6-15 words ideal)"
                            }
                        }
                    }
                }
            }
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Activity tags (e.g., verbal, physical, intimate)"
        },
        "provenance": {
            "type": "object",
            "required": ["source"],
            "properties": {
                "source": {
                    "type": "string",
                    "enum": ["bank", "ai_generated"],
                    "description": "Where this activity came from"
                },
                "template_id": {
                    "type": ["integer", "null"],
                    "description": "ID from activity bank if applicable"
                }
            }
        },
        "checks": {
            "type": "object",
            "required": ["respects_hard_limits", "uses_yes_overlap", "maybe_items_present", "anatomy_ok"],
            "properties": {
                "respects_hard_limits": {
                    "type": "boolean",
                    "description": "True if activity respects both players' hard limits"
                },
                "uses_yes_overlap": {
                    "type": "boolean",
                    "description": "True if activity uses mutually desired elements"
                },
                "maybe_items_present": {
                    "type": "boolean",
                    "description": "True if activity includes maybe/uncertain items"
                },
                "anatomy_ok": {
                    "type": "boolean",
                    "description": "True if activity matches players' anatomy"
                },
                "power_alignment": {
                    "type": ["boolean", "null"],
                    "description": "True if power roles align with preferences"
                },
                "notes": {
                    "type": ["string", "null"],
                    "description": "Additional validation notes"
                }
            }
        }
    }
}

# JSON Schema for complete session recommendations
SESSION_RECOMMENDATIONS_SCHEMA = {
    "type": "object",
    "required": ["session_id", "activities"],
    "properties": {
        "session_id": {
            "type": "string",
            "description": "Session identifier"
        },
        "activities": {
            "type": "array",
            "minItems": 1,
            "maxItems": 30,
            "items": ACTIVITY_OUTPUT_SCHEMA
        }
    }
}


def get_groq_json_schema():
    """Get the JSON schema formatted for Groq API."""
    return {
        "name": "attuned_recommendation",
        "schema": SESSION_RECOMMENDATIONS_SCHEMA,
        "strict": True
    }

