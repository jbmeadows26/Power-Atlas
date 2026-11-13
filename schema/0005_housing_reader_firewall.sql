-- Production access firewall: run AFTER 0002/0003/0004.
-- Database-owner migration role is separate from the Vercel runtime login.
-- Public runtime readers see only human-approved, non-disputed assertions.
BEGIN;
REVOKE ALL ON SCHEMA atlas_housing FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA atlas_housing FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA atlas_housing FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA atlas_housing FROM PUBLIC;
DO $role$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'atlas_housing_reader') THEN
    CREATE ROLE atlas_housing_reader NOLOGIN;
  END IF;
END $role$;
REVOKE ALL ON SCHEMA atlas_housing FROM atlas_housing_reader;
REVOKE ALL ON ALL TABLES IN SCHEMA atlas_housing FROM atlas_housing_reader;
GRANT USAGE ON SCHEMA atlas_housing TO atlas_housing_reader;
GRANT SELECT ON atlas_housing.public_evidence TO atlas_housing_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA atlas_housing REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA atlas_housing REVOKE ALL ON SEQUENCES FROM PUBLIC;
COMMIT;
-- Configure a distinct LOGIN runtime role outside version control, and grant
-- atlas_housing_reader to it. Never use neondb_owner in Vercel.
