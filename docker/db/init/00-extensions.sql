-- Runs once, when the PostgreSQL data volume is initialised.
--
-- Only pgcrypto is required by the current API. The runtime code does not use
-- PostGIS or pgvector yet: comparables are computed in-process, and the
-- location/feature_embedding columns are not written by the API.
--
-- When you do start using the geo-complete schema (backend/migrations/001_init.sql),
-- switch to the PostGIS image with the bundled override:
--     docker compose -f compose.yaml -f compose.geo.yaml up -d --build
CREATE EXTENSION IF NOT EXISTS pgcrypto;
