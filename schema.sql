-- ============================================================
--  WELLEXPO 2026 — Kerala Healthcare Expo
--  Database Schema  (SQLite + PostgreSQL compatible)
--  Generated: 2026-05-23
-- ============================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ── 1. LOOKUP / REFERENCE TABLES ─────────────────────────────

-- Industry sectors allowed on the form
CREATE TABLE IF NOT EXISTS industry_sectors (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    NOT NULL UNIQUE
);

-- Booth types
CREATE TABLE IF NOT EXISTS booth_types (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    NOT NULL UNIQUE  -- e.g. 'Shell Scheme', 'Space Only', 'Custom Build'
);

-- Exhibitions (multi-edition ready)
CREATE TABLE IF NOT EXISTS exhibitions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,  -- e.g. 'WellExpo Kerala 2026'
    location    TEXT,
    start_date  TEXT,                     -- ISO-8601 date
    end_date    TEXT,
    description TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1  -- 0 = closed, 1 = open for registration
);

INSERT OR IGNORE INTO exhibitions (name, location, start_date, end_date, is_active)
VALUES ('WellExpo Kerala 2026', 'Kerala, India', '2026-01-01', '2026-12-31', 1);


-- ── 2. CORE ENTITY TABLES ─────────────────────────────────────

-- Companies
CREATE TABLE IF NOT EXISTS companies (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name          TEXT    NOT NULL,
    brand_name            TEXT,
    company_website       TEXT,
    industry_sector_id    INTEGER REFERENCES industry_sectors(id) ON DELETE SET NULL,
    industry_sector_raw   TEXT,            -- free-text fallback / unmatched values
    year_established      TEXT,
    company_description   TEXT,
    created_at            TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at            TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- Contact persons (one company may have multiple contacts)
CREATE TABLE IF NOT EXISTS contacts (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id           INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    contact_person_name  TEXT    NOT NULL,
    email_address        TEXT    NOT NULL,
    phone_number         TEXT,
    whatsapp_number      TEXT,
    country              TEXT,
    city                 TEXT,
    is_primary           INTEGER NOT NULL DEFAULT 1,  -- 1 = primary contact
    created_at           TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_contacts_email
    ON contacts (company_id, email_address);


-- ── 3. REGISTRATION TABLE (core) ─────────────────────────────

CREATE TABLE IF NOT EXISTS registrations (
    id                             INTEGER PRIMARY KEY AUTOINCREMENT,
    exhibition_id                  INTEGER NOT NULL REFERENCES exhibitions(id),
    company_id                     INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    contact_id                     INTEGER NOT NULL REFERENCES contacts(id)  ON DELETE CASCADE,

    -- Exhibition participation
    product_service_category       TEXT,
    target_market                  TEXT,
    previous_exhibition_experience TEXT,   -- 'Yes' | 'No'

    -- Booth requirements
    booth_type_id                  INTEGER REFERENCES booth_types(id) ON DELETE SET NULL,
    booth_type_raw                 TEXT,   -- raw form value
    booth_size                     TEXT,
    number_of_booth_staff          INTEGER,
    power_requirement              TEXT,   -- 'Yes' | 'No'
    internet_requirement           TEXT,   -- 'Yes' | 'No'

    -- Marketing & Promotion
    interested_sponsorship         TEXT,   -- 'Yes' | 'No'
    interested_speaking            TEXT,   -- 'Yes' | 'No'
    interested_product_launch      TEXT,   -- 'Yes' | 'No'

    -- Additional
    special_requirements           TEXT,

    -- Agreements
    terms_conditions               TEXT,   -- 'agreed' | NULL
    consent_marketing              TEXT,   -- 'agreed' | NULL

    -- Status tracking
    status                         TEXT    NOT NULL DEFAULT 'pending',
                                           -- 'pending' | 'approved' | 'rejected' | 'waitlisted'
    reviewed_by                    TEXT,
    reviewed_at                    TEXT,
    notes                          TEXT,   -- internal admin notes

    created_at                     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at                     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE INDEX IF NOT EXISTS idx_registrations_company    ON registrations(company_id);
CREATE INDEX IF NOT EXISTS idx_registrations_exhibition ON registrations(exhibition_id);
CREATE INDEX IF NOT EXISTS idx_registrations_status     ON registrations(status);


-- ── 4. DOCUMENTS TABLE ───────────────────────────────────────

CREATE TABLE IF NOT EXISTS documents (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    registration_id  INTEGER NOT NULL REFERENCES registrations(id) ON DELETE CASCADE,
    document_type    TEXT    NOT NULL,   -- 'company_logo' | 'product_images' | 'company_profile' | 'business_registration'
    file_path        TEXT    NOT NULL,   -- local path OR Cloudinary URL
    original_name    TEXT,
    file_size_bytes  INTEGER,
    mime_type        TEXT,
    uploaded_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE INDEX IF NOT EXISTS idx_documents_registration ON documents(registration_id);
CREATE INDEX IF NOT EXISTS idx_documents_type         ON documents(document_type);


-- ── 5. AUDIT LOG ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS audit_log (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name       TEXT    NOT NULL,
    record_id        INTEGER NOT NULL,
    action           TEXT    NOT NULL,   -- 'INSERT' | 'UPDATE' | 'DELETE'
    changed_by       TEXT,               -- admin user or 'system'
    changed_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    old_values       TEXT,               -- JSON snapshot before change
    new_values       TEXT                -- JSON snapshot after change
);

CREATE INDEX IF NOT EXISTS idx_audit_table_record ON audit_log(table_name, record_id);


-- ── 6. SEED LOOKUP DATA ──────────────────────────────────────

INSERT OR IGNORE INTO industry_sectors (name) VALUES
    ('Pharmaceuticals'),
    ('Medical Devices & Equipment'),
    ('Healthcare IT & Digital Health'),
    ('Hospitals & Clinics'),
    ('Nutraceuticals & Wellness'),
    ('Diagnostics & Laboratory'),
    ('Rehabilitation & Physiotherapy'),
    ('Insurance & Health Finance'),
    ('Ayurveda & Traditional Medicine'),
    ('Cosmetics & Personal Care'),
    ('Fitness & Sports Medicine'),
    ('Medical Tourism'),
    ('Other');

INSERT OR IGNORE INTO booth_types (name) VALUES
    ('Shell Scheme'),
    ('Space Only'),
    ('Custom Build'),
    ('Virtual Booth');
