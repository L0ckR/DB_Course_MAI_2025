CREATE OR REPLACE VIEW v_runs_with_final_metrics AS
SELECT
    r.run_id,
    r.experiment_id,
    r.dataset_version_id,
    r.run_name,
    r.status,
    r.started_at,
    r.finished_at,
    r.created_by,
    r.git_commit,
    r.notes,
    jsonb_object_agg(md.key, rmv.value) FILTER (WHERE rmv.step IS NULL) AS final_metrics
FROM runs r
LEFT JOIN run_metric_values rmv
    ON rmv.run_id = r.run_id AND rmv.step IS NULL
LEFT JOIN metric_definitions md
    ON md.metric_id = rmv.metric_id
GROUP BY
    r.run_id,
    r.experiment_id,
    r.dataset_version_id,
    r.run_name,
    r.status,
    r.started_at,
    r.finished_at,
    r.created_by,
    r.git_commit,
    r.notes;

CREATE OR REPLACE VIEW v_best_runs_per_experiment AS
SELECT
    experiment_id,
    run_id,
    run_name,
    metric_value,
    started_at,
    status
FROM (
    SELECT
        r.experiment_id,
        r.run_id,
        r.run_name,
        rmv.value AS metric_value,
        r.started_at,
        r.status,
        ROW_NUMBER() OVER (
            PARTITION BY r.experiment_id
            ORDER BY
              CASE WHEN md.goal = 'min' THEN rmv.value END ASC,
              CASE WHEN md.goal = 'max' THEN rmv.value END DESC,
              CASE WHEN md.goal = 'last' THEN rmv.recorded_at END DESC
        ) AS rn
    FROM runs r
    JOIN run_metric_values rmv ON rmv.run_id = r.run_id AND rmv.step IS NULL
    JOIN metric_definitions md ON md.metric_id = rmv.metric_id
    WHERE md.key = 'accuracy'
) ranked
WHERE rn = 1;

CREATE OR REPLACE VIEW v_project_quality_dashboard AS
SELECT
    p.project_id,
    p.name AS project_name,
    COUNT(DISTINCT e.experiment_id) AS experiments_count,
    COUNT(DISTINCT r.run_id) AS runs_count,
    COALESCE(
        ROUND(
            100.0 * SUM(CASE WHEN r.status = 'finished' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(r.run_id), 0),
            2
        ),
        0
    ) AS success_rate_pct,
    PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY EXTRACT(EPOCH FROM (r.finished_at - r.started_at))
    ) FILTER (WHERE r.finished_at IS NOT NULL AND r.started_at IS NOT NULL)
      AS median_train_seconds,
    pms.best_value AS best_metric_value,
    pms.best_run_id
FROM ml_projects p
LEFT JOIN experiments e ON e.project_id = p.project_id
LEFT JOIN runs r ON r.experiment_id = e.experiment_id
LEFT JOIN metric_definitions md ON md.key = 'accuracy'
LEFT JOIN project_metric_summary pms
    ON pms.project_id = p.project_id
   AND pms.metric_id = md.metric_id
   AND pms.scope = 'val'
GROUP BY p.project_id, p.name, pms.best_value, pms.best_run_id;
