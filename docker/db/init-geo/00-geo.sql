-- Used by compose.geo.yaml (PostGIS base image).
--
-- The stock postgis/postgis image ships PostGIS but NOT pgvector, so creating
-- the vector extension would abort database initialisation. Guard it: create
-- PostGIS (always available here) and create pgvector only if the extension
-- files are present, otherwise warn and continue.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS vector;
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'pgvector is not available in this image; skipping. Use a PostGIS image built with postgresql-16-pgvector to enable it.';
END
$$;
