-- Migration to ensure compatibility_results table exists
-- This table might already exist in some environments, so we use IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS compatibility_results (
    id SERIAL PRIMARY KEY,
    
    -- Players (ordered: lower id first for consistency, referencing profiles)
    player_a_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    player_b_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    
    -- Compatibility scores
    overall_score FLOAT NOT NULL,  -- 0.0-1.0
    overall_percentage INTEGER NOT NULL,  -- 0-100
    interpretation VARCHAR(128),  -- Text interpretation
    
    -- Detailed breakdown
    breakdown JSON NOT NULL,
    
    -- Mutual interests and opportunities
    mutual_activities JSON,
    growth_opportunities JSON,
    mutual_truth_topics JSON,
    
    -- Blocked activities and conflicts
    blocked_activities JSON,
    boundary_conflicts JSON,
    
    -- Metadata
    calculation_version VARCHAR(16) NOT NULL DEFAULT '0.4',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Ensure unique compatibility pair
    CONSTRAINT uq_compatibility_pair UNIQUE (player_a_id, player_b_id)
);

CREATE INDEX IF NOT EXISTS idx_compatibility_player_a ON compatibility_results(player_a_id);
CREATE INDEX IF NOT EXISTS idx_compatibility_player_b ON compatibility_results(player_b_id);

-- Enable RLS
ALTER TABLE compatibility_results ENABLE ROW LEVEL SECURITY;

-- Policies
-- Users can see compatibility if they own one of the profiles
CREATE POLICY compatibility_select_own ON compatibility_results FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM profiles p
        WHERE (p.id = compatibility_results.player_a_id OR p.id = compatibility_results.player_b_id)
        AND p.user_id = auth.uid()
    )
);

-- Insert policy (backend usually handles this, but for completeness)
CREATE POLICY compatibility_insert_all ON compatibility_results FOR INSERT WITH CHECK (true);
