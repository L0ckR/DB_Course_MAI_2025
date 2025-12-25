CREATE OR REPLACE FUNCTION fn_audit_log() RETURNS trigger AS $$
DECLARE
    v_user_id uuid;
    v_pk text;
BEGIN
    v_user_id := NULLIF(current_setting('app.user_id', true), '')::uuid;

    IF TG_OP = 'INSERT' THEN
        v_pk := to_jsonb(NEW) ->> TG_ARGV[0];
        INSERT INTO audit_log (table_name, operation, row_pk, changed_by, old_data, new_data)
        VALUES (TG_TABLE_NAME, 'I', v_pk, v_user_id, NULL, to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        v_pk := to_jsonb(NEW) ->> TG_ARGV[0];
        INSERT INTO audit_log (table_name, operation, row_pk, changed_by, old_data, new_data)
        VALUES (TG_TABLE_NAME, 'U', v_pk, v_user_id, to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        v_pk := to_jsonb(OLD) ->> TG_ARGV[0];
        INSERT INTO audit_log (table_name, operation, row_pk, changed_by, old_data, new_data)
        VALUES (TG_TABLE_NAME, 'D', v_pk, v_user_id, to_jsonb(OLD), NULL);
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_users ON users;
CREATE TRIGGER trg_audit_users
AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW EXECUTE FUNCTION fn_audit_log('user_id');

DROP TRIGGER IF EXISTS trg_audit_ml_projects ON ml_projects;
CREATE TRIGGER trg_audit_ml_projects
AFTER INSERT OR UPDATE OR DELETE ON ml_projects
FOR EACH ROW EXECUTE FUNCTION fn_audit_log('project_id');

DROP TRIGGER IF EXISTS trg_audit_datasets ON datasets;
CREATE TRIGGER trg_audit_datasets
AFTER INSERT OR UPDATE OR DELETE ON datasets
FOR EACH ROW EXECUTE FUNCTION fn_audit_log('dataset_id');

DROP TRIGGER IF EXISTS trg_audit_dataset_versions ON dataset_versions;
CREATE TRIGGER trg_audit_dataset_versions
AFTER INSERT OR UPDATE OR DELETE ON dataset_versions
FOR EACH ROW EXECUTE FUNCTION fn_audit_log('dataset_version_id');

DROP TRIGGER IF EXISTS trg_audit_experiments ON experiments;
CREATE TRIGGER trg_audit_experiments
AFTER INSERT OR UPDATE OR DELETE ON experiments
FOR EACH ROW EXECUTE FUNCTION fn_audit_log('experiment_id');

DROP TRIGGER IF EXISTS trg_audit_runs ON runs;
CREATE TRIGGER trg_audit_runs
AFTER INSERT OR UPDATE OR DELETE ON runs
FOR EACH ROW EXECUTE FUNCTION fn_audit_log('run_id');

DROP TRIGGER IF EXISTS trg_audit_run_configs ON run_configs;
CREATE TRIGGER trg_audit_run_configs
AFTER INSERT OR UPDATE OR DELETE ON run_configs
FOR EACH ROW EXECUTE FUNCTION fn_audit_log('run_id');

DROP TRIGGER IF EXISTS trg_audit_artifacts ON artifacts;
CREATE TRIGGER trg_audit_artifacts
AFTER INSERT OR UPDATE OR DELETE ON artifacts
FOR EACH ROW EXECUTE FUNCTION fn_audit_log('artifact_id');

DROP TRIGGER IF EXISTS trg_audit_metric_definitions ON metric_definitions;
CREATE TRIGGER trg_audit_metric_definitions
AFTER INSERT OR UPDATE OR DELETE ON metric_definitions
FOR EACH ROW EXECUTE FUNCTION fn_audit_log('metric_id');
