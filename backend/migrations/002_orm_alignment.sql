-- Qeymatban — align hand-written schema with the SQLAlchemy runtime models.
-- Safe to run repeatedly; API startup also applies missing columns automatically.

ALTER TABLE properties
    ADD COLUMN IF NOT EXISTS listed_price NUMERIC(16,0),
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active',
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE valuations
    ADD COLUMN IF NOT EXISTS confidence_level NUMERIC(4,3) NOT NULL DEFAULT 0.8,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

CREATE INDEX IF NOT EXISTS idx_valuations_created_at ON valuations (created_at DESC);
