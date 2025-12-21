#!/bin/bash
# Export schema for survey_progress and survey_submissions tables
# Usage: ./export_schema.sh [DATABASE_URL]

DB_URL=${1:-$DATABASE_URL}

if [ -z "$DB_URL" ]; then
  echo "Error: DATABASE_URL is not set. Please provide it as an argument or set the environment variable."
  exit 1
fi

echo "Exporting schema for survey_progress and survey_submissions..."

pg_dump "$DB_URL" \
  --schema-only \
  --table=survey_progress \
  --table=survey_submissions \
  --no-owner \
  --no-privileges

echo "Done."
