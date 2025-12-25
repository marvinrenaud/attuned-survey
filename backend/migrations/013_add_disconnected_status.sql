-- Add 'disconnected' to connection_status_enum
-- NOTE: ALTER TYPE cannot run inside a transaction block in PostgreSQL
COMMIT;
ALTER TYPE connection_status_enum ADD VALUE IF NOT EXISTS 'disconnected';
