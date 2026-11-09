CREATE SCHEMA IF NOT EXISTS revenue;
SET LOCAL search_path TO revenue, pg_catalog;
CREATE ROLE revenue_runtime NOLOGIN;
REVOKE ALL ON SCHEMA revenue FROM PUBLIC;
GRANT USAGE ON SCHEMA revenue TO revenue_runtime;

CREATE TABLE revenue_records (
    student_id text primary key,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
ALTER TABLE revenue_records ENABLE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON revenue_records TO revenue_runtime;
CREATE POLICY service_access ON revenue_records TO revenue_runtime USING (true) WITH CHECK (true);

CREATE TABLE income_certificates (
    certificate_ref text primary key,
    student_id text not null references revenue_records,
    annual_income numeric(14,2) not null check (annual_income >= 0),
    issued_on date not null,
    expires_on date not null check (expires_on >= issued_on),
    status text not null check (status in ('VALID','EXPIRED','REVOKED')),
    issuing_authority text not null,
    updated_at timestamptz not null default now()
);
ALTER TABLE income_certificates ENABLE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON income_certificates TO revenue_runtime;
CREATE POLICY service_access ON income_certificates TO revenue_runtime USING (true) WITH CHECK (true);
CREATE INDEX ON income_certificates (student_id);

CREATE TABLE caste_certificates (
    certificate_ref text primary key,
    student_id text not null references revenue_records,
    caste_category text not null,
    issued_on date not null,
    expires_on date not null check (expires_on >= issued_on),
    status text not null check (status in ('VALID','EXPIRED','REVOKED')),
    issuing_authority text not null,
    updated_at timestamptz not null default now()
);
ALTER TABLE caste_certificates ENABLE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE ON caste_certificates TO revenue_runtime;
CREATE POLICY service_access ON caste_certificates TO revenue_runtime USING (true) WITH CHECK (true);
CREATE INDEX ON caste_certificates (student_id);

CREATE TABLE certificate_history (
    id bigint generated always as identity primary key,
    income_ref text references income_certificates,
    caste_ref text references caste_certificates,
    status text not null,
    recorded_at timestamptz not null default now(),
    check(num_nonnulls(income_ref,caste_ref)=1)
);
ALTER TABLE certificate_history ENABLE ROW LEVEL SECURITY;
GRANT SELECT, INSERT ON certificate_history TO revenue_runtime;
CREATE POLICY service_access ON certificate_history TO revenue_runtime USING (true) WITH CHECK (true);
CREATE INDEX ON certificate_history (income_ref);
CREATE INDEX ON certificate_history (caste_ref);
GRANT USAGE ON ALL SEQUENCES IN SCHEMA revenue TO revenue_runtime;
