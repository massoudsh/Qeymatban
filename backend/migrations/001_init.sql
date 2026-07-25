-- Qeymatban — schema اولیه
-- نیازمند: PostgreSQL 15+، پسوند postgis، پسوند pgvector (برای embeddings)

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- برای gen_random_uuid()

CREATE TYPE property_status AS ENUM ('active', 'sold', 'withdrawn');

-- هر رکورد یک فایل/ملک است (چه در بازار فعال، چه فروخته‌شده)
CREATE TABLE properties (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title             TEXT,
    address           TEXT,
    neighborhood      TEXT NOT NULL,
    city              TEXT NOT NULL DEFAULT 'تهران',
    location          GEOGRAPHY(POINT, 4326) NOT NULL,

    area_sqm          NUMERIC(8,2) NOT NULL,
    year_built        SMALLINT,
    floor             SMALLINT,
    total_floors      SMALLINT,
    rooms             SMALLINT,

    has_parking       BOOLEAN NOT NULL DEFAULT FALSE,
    has_elevator      BOOLEAN NOT NULL DEFAULT FALSE,
    has_storage       BOOLEAN NOT NULL DEFAULT FALSE,
    renovated         BOOLEAN NOT NULL DEFAULT FALSE,

    light_score       SMALLINT CHECK (light_score BETWEEN 1 AND 5),
    view_score        SMALLINT CHECK (view_score BETWEEN 1 AND 5),
    access_score      SMALLINT CHECK (access_score BETWEEN 1 AND 5),

    listed_price      NUMERIC(16,0),
    status            property_status NOT NULL DEFAULT 'active',

    -- بردار ویژگی برای جست‌وجوی شباهت (comparables)؛ ابعاد بعداً بر اساس مدل نهایی می‌شود
    feature_embedding VECTOR(32),

    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_properties_location     ON properties USING GIST (location);
CREATE INDEX idx_properties_neighborhood ON properties (neighborhood);
CREATE INDEX idx_properties_status       ON properties (status);
CREATE INDEX idx_properties_embedding    ON properties USING ivfflat (feature_embedding vector_cosine_ops);

-- معاملات واقعاً بسته‌شده — داده آموزشی اصلی مدل قیمت‌گذاری
CREATE TABLE transactions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id  UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    sold_price   NUMERIC(16,0) NOT NULL,
    sold_date    DATE NOT NULL,
    source       TEXT, -- آگهی / دفتر املاک / self-reported
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_transactions_property ON transactions (property_id);
CREATE INDEX idx_transactions_sold_date ON transactions (sold_date);

-- خروجی مدل برای هر ملک: بازه قیمت + عدم قطعیت + توضیح SHAP (audit trail قابل دفاع)
CREATE TABLE valuations (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id       UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,

    price_low         NUMERIC(16,0) NOT NULL,
    price_mid         NUMERIC(16,0) NOT NULL,
    price_high        NUMERIC(16,0) NOT NULL,
    confidence_level  NUMERIC(4,3) NOT NULL DEFAULT 0.8, -- مثلاً بازه ۸۰٪

    shap_values       JSONB NOT NULL, -- {"area_sqm": 320000000, "floor": -50000000, ...}
    model_version     TEXT NOT NULL,

    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_valuations_property ON valuations (property_id);

-- فایل‌های مشابه استفاده‌شده در هر ارزش‌گذاری، به‌ترتیب شباهت
CREATE TABLE valuation_comparables (
    valuation_id   UUID NOT NULL REFERENCES valuations(id) ON DELETE CASCADE,
    comparable_id  UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    similarity     NUMERIC(5,4) NOT NULL, -- 0..1 (cosine similarity)
    rank           SMALLINT NOT NULL,
    PRIMARY KEY (valuation_id, comparable_id)
);
