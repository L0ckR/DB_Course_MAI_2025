CREATE OR REPLACE FUNCTION fn_update_project_metric_summary() RETURNS trigger AS $$
DECLARE
    v_metric_id uuid;
    v_scope text;
    v_project_id uuid;
    v_goal text;
    v_best_run_id uuid;
    v_best_value double precision;
    v_sample_size integer;
BEGIN
    IF TG_OP = 'DELETE' THEN
        IF OLD.step IS NOT NULL THEN
            RETURN OLD;
        END IF;
        v_metric_id := OLD.metric_id;
        v_scope := OLD.scope;
        SELECT e.project_id
        INTO v_project_id
        FROM runs r
        JOIN experiments e ON e.experiment_id = r.experiment_id
        WHERE r.run_id = OLD.run_id;
    ELSE
        IF NEW.step IS NOT NULL THEN
            RETURN NEW;
        END IF;
        v_metric_id := NEW.metric_id;
        v_scope := NEW.scope;
        SELECT e.project_id
        INTO v_project_id
        FROM runs r
        JOIN experiments e ON e.experiment_id = r.experiment_id
        WHERE r.run_id = NEW.run_id;
    END IF;

    IF v_project_id IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT goal
    INTO v_goal
    FROM metric_definitions
    WHERE metric_id = v_metric_id;

    IF v_goal IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT COUNT(*)
    INTO v_sample_size
    FROM run_metric_values rmv
    JOIN runs r ON r.run_id = rmv.run_id
    JOIN experiments e ON e.experiment_id = r.experiment_id
    WHERE e.project_id = v_project_id
      AND rmv.metric_id = v_metric_id
      AND rmv.scope = v_scope
      AND rmv.step IS NULL;

    IF v_sample_size = 0 THEN
        DELETE FROM project_metric_summary
        WHERE project_id = v_project_id
          AND metric_id = v_metric_id
          AND scope = v_scope;
        RETURN NULL;
    END IF;

    SELECT rmv.run_id, rmv.value
    INTO v_best_run_id, v_best_value
    FROM run_metric_values rmv
    JOIN runs r ON r.run_id = rmv.run_id
    JOIN experiments e ON e.experiment_id = r.experiment_id
    WHERE e.project_id = v_project_id
      AND rmv.metric_id = v_metric_id
      AND rmv.scope = v_scope
      AND rmv.step IS NULL
    ORDER BY
      CASE WHEN v_goal = 'min' THEN rmv.value END ASC,
      CASE WHEN v_goal = 'max' THEN rmv.value END DESC,
      CASE WHEN v_goal = 'last' THEN rmv.recorded_at END DESC
    LIMIT 1;

    INSERT INTO project_metric_summary (
        project_id,
        metric_id,
        scope,
        best_value,
        best_run_id,
        updated_at,
        sample_size
    ) VALUES (
        v_project_id,
        v_metric_id,
        v_scope,
        v_best_value,
        v_best_run_id,
        now(),
        v_sample_size
    )
    ON CONFLICT (project_id, metric_id, scope) DO UPDATE SET
        best_value = EXCLUDED.best_value,
        best_run_id = EXCLUDED.best_run_id,
        updated_at = EXCLUDED.updated_at,
        sample_size = EXCLUDED.sample_size;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_project_metric_summary ON run_metric_values;
CREATE TRIGGER trg_project_metric_summary
AFTER INSERT OR UPDATE OR DELETE ON run_metric_values
FOR EACH ROW EXECUTE FUNCTION fn_update_project_metric_summary();
