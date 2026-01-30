-- Rollback for Migration 030: Remove remembered_partners sync triggers
-- ============================================================================

-- Drop triggers first (they depend on the functions)
DROP TRIGGER IF EXISTS trg_sync_remembered_partner_name ON public.users;
DROP TRIGGER IF EXISTS trg_sync_remembered_partner_email ON public.users;

-- Drop functions
DROP FUNCTION IF EXISTS sync_remembered_partner_name();
DROP FUNCTION IF EXISTS sync_remembered_partner_email();

-- ============================================================================
-- Rollback complete
--
-- After rollback, changes to users.display_name and users.email will no longer
-- sync to remembered_partners. Partner lists will show stale data until the
-- partner entry is recreated (e.g., by playing with that partner again).
--
-- The application-level sync in repository.py will continue to work, but
-- only for partners that explicitly use those code paths.
-- ============================================================================
