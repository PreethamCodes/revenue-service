-- Synthetic fixtures; snapshot date 2026-11-09.
BEGIN;
SET LOCAL search_path TO revenue, pg_catalog;
INSERT INTO revenue_records VALUES ('MHSTU0001') ON CONFLICT DO NOTHING;
INSERT INTO income_certificates VALUES ('income-1', 'MHSTU0001', 150000, '2025-01-01', '2027-01-01', 'VALID', 'Demo Revenue') ON CONFLICT DO NOTHING;
INSERT INTO caste_certificates VALUES ('caste-1', 'MHSTU0001', 'DEMO-A', '2025-01-01', '2027-01-01', 'VALID', 'Demo Revenue') ON CONFLICT DO NOTHING;
INSERT INTO revenue_records VALUES ('MHSTU0002') ON CONFLICT DO NOTHING;
INSERT INTO income_certificates VALUES ('income-2', 'MHSTU0002', 350000, '2025-01-01', '2027-01-01', 'VALID', 'Demo Revenue') ON CONFLICT DO NOTHING;
INSERT INTO caste_certificates VALUES ('caste-2', 'MHSTU0002', 'DEMO-A', '2025-01-01', '2027-01-01', 'VALID', 'Demo Revenue') ON CONFLICT DO NOTHING;
INSERT INTO revenue_records VALUES ('MHSTU0003') ON CONFLICT DO NOTHING;
INSERT INTO income_certificates VALUES ('income-3', 'MHSTU0003', 150000, '2025-01-01', '2026-01-01', 'EXPIRED', 'Demo Revenue') ON CONFLICT DO NOTHING;
INSERT INTO caste_certificates VALUES ('caste-3', 'MHSTU0003', 'DEMO-A', '2025-01-01', '2026-01-01', 'EXPIRED', 'Demo Revenue') ON CONFLICT DO NOTHING;
INSERT INTO revenue_records VALUES ('MHSTU0004') ON CONFLICT DO NOTHING;
INSERT INTO income_certificates VALUES ('income-4', 'MHSTU0004', 150000, '2025-01-01', '2027-01-01', 'VALID', 'Demo Revenue') ON CONFLICT DO NOTHING;
INSERT INTO caste_certificates VALUES ('caste-4', 'MHSTU0004', 'DEMO-A', '2025-01-01', '2027-01-01', 'VALID', 'Demo Revenue') ON CONFLICT DO NOTHING;
INSERT INTO revenue_records VALUES ('MHSTU0005') ON CONFLICT DO NOTHING;
INSERT INTO income_certificates VALUES ('income-5', 'MHSTU0005', 150000, '2025-01-01', '2027-01-01', 'VALID', 'Demo Revenue') ON CONFLICT DO NOTHING;
INSERT INTO caste_certificates VALUES ('caste-5', 'MHSTU0005', 'DEMO-A', '2025-01-01', '2027-01-01', 'VALID', 'Demo Revenue') ON CONFLICT DO NOTHING;
COMMIT;
