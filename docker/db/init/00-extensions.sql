-- Runs once, when the PostgreSQL data volume is initialised.
-- Tables are created by the API's SQLAlchemy metadata on startup, which matches
-- the runtime models; backend/migrations/001_init.sql is the geo-complete schema
-- for when location/embedding columns are actually populated.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
