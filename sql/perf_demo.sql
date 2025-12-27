-- Example performance demo script
-- Adjust identifiers and run inside psql. Capture EXPLAIN ANALYZE output into docs/perf_report.md.

-- Drop indexes to capture baseline
DROP INDEX IF EXISTS ix_runs_experiment_status_started;
DROP INDEX IF EXISTS ix_rmv_run_metric_scope_step;
DROP INDEX IF EXISTS ix_rmv_final_metric;
DROP INDEX IF EXISTS ix_experiments_project_id;
DROP INDEX IF EXISTS ix_runs_dataset_version_id;

EXPLAIN ANALYZE
SELECT *
FROM fn_experiment_leaderboard(
    '00000000-0000-0000-0000-000000000000',
    'accuracy',
    'val',
    10
);

EXPLAIN ANALYZE
SELECT
    e.project_id,
    dv.dataset_version_id,
    dv.version_label,
    COUNT(*) AS run_count,
    AVG(rmv.value) AS avg_value
FROM dataset_versions dv
JOIN runs r ON r.dataset_version_id = dv.dataset_version_id
JOIN experiments e ON e.experiment_id = r.experiment_id
JOIN run_metric_values rmv ON rmv.run_id = r.run_id AND rmv.step IS NULL
WHERE rmv.metric_id = '00000000-0000-0000-0000-000000000000'
  AND rmv.scope = 'val'
GROUP BY e.project_id, dv.dataset_version_id, dv.version_label
ORDER BY avg_value DESC
LIMIT 20;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS ix_runs_experiment_status_started
    ON runs (experiment_id, status, started_at);

CREATE INDEX IF NOT EXISTS ix_rmv_run_metric_scope_step
    ON run_metric_values (run_id, metric_id, scope, step);

CREATE INDEX IF NOT EXISTS ix_experiments_project_id
    ON experiments (project_id);

CREATE INDEX IF NOT EXISTS ix_runs_dataset_version_id
    ON runs (dataset_version_id);

CREATE INDEX IF NOT EXISTS ix_rmv_final_metric
    ON run_metric_values (metric_id, scope, value)
    WHERE step IS NULL;

EXPLAIN ANALYZE
SELECT *
FROM fn_experiment_leaderboard(
    '00000000-0000-0000-0000-000000000000',
    'accuracy',
    'val',
    10
);

EXPLAIN ANALYZE
SELECT
    e.project_id,
    dv.dataset_version_id,
    dv.version_label,
    COUNT(*) AS run_count,
    AVG(rmv.value) AS avg_value
FROM dataset_versions dv
JOIN runs r ON r.dataset_version_id = dv.dataset_version_id
JOIN experiments e ON e.experiment_id = r.experiment_id
JOIN run_metric_values rmv ON rmv.run_id = r.run_id AND rmv.step IS NULL
WHERE rmv.metric_id = '00000000-0000-0000-0000-000000000000'
  AND rmv.scope = 'val'
GROUP BY e.project_id, dv.dataset_version_id, dv.version_label
ORDER BY avg_value DESC
LIMIT 20;
