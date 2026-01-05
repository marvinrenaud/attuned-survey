-- Migration: Add Config RPC and Seed Data

-- 1. Create RPC function for FlutterFlow/Frontend


-- 2. Seed default values (ensuring no overwrite of existing custom values)
INSERT INTO app_config (key, value, description) VALUES
    ('profile_version', '0.4', 'Current profile/survey version'),
    ('default_target_activities', '25', 'Default number of activities per game session'),
    ('default_bank_ratio', '0.5', 'Ratio for activity banking algorithm'),
    ('default_rating', 'R', 'Default content rating filter (G, PG, PG13, R, NC17)'),
    ('daily_free_limit', '25', 'Daily activity limit for free tier users'),
    ('gen_temperature', '0.6', 'Default temperature for LLM generation'),
    ('repair_use_ai', 'true', 'Feature flag to use AI for relationship repair suggestions')
ON CONFLICT (key) DO NOTHING;
