CREATE OR REPLACE FUNCTION fn_best_run_id(
    p_experiment_id uuid,
    p_metric_key text,
    p_scope text
) RETURNS uuid AS $$
DECLARE
    v_goal text;
    v_run_id uuid;
BEGIN
    SELECT goal
    INTO v_goal
    FROM metric_definitions
    WHERE key = p_metric_key;

    IF v_goal IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT rmv.run_id
    INTO v_run_id
    FROM run_metric_values rmv
    JOIN metric_definitions md ON md.metric_id = rmv.metric_id
    JOIN runs r ON r.run_id = rmv.run_id
    WHERE r.experiment_id = p_experiment_id
      AND md.key = p_metric_key
      AND rmv.scope = p_scope
      AND rmv.step IS NULL
    ORDER BY
      CASE WHEN v_goal = 'min' THEN rmv.value END ASC,
      CASE WHEN v_goal = 'max' THEN rmv.value END DESC,
      CASE WHEN v_goal = 'last' THEN rmv.recorded_at END DESC
    LIMIT 1;

    RETURN v_run_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_experiment_leaderboard(
    p_experiment_id uuid,
    p_metric_key text,
    p_scope text,
    p_limit integer
)
RETURNS TABLE(
    run_id uuid,
    run_name text,
    metric_value double precision,
    started_at timestamptz,
    status text
) AS $$
DECLARE
    v_goal text;
BEGIN
    SELECT goal
    INTO v_goal
    FROM metric_definitions
    WHERE key = p_metric_key;

    IF v_goal IS NULL THEN
        RETURN;
    END IF;

    RETURN QUERY
    SELECT r.run_id, r.run_name, rmv.value, r.started_at, r.status
    FROM runs r
    JOIN run_metric_values rmv ON rmv.run_id = r.run_id
    JOIN metric_definitions md ON md.metric_id = rmv.metric_id
    WHERE r.experiment_id = p_experiment_id
      AND md.key = p_metric_key
      AND rmv.scope = p_scope
      AND rmv.step IS NULL
    ORDER BY
      CASE WHEN v_goal = 'min' THEN rmv.value END ASC,
      CASE WHEN v_goal = 'max' THEN rmv.value END DESC,
      CASE WHEN v_goal = 'last' THEN rmv.recorded_at END DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
