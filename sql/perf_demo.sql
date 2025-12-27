-- Example performance demo script
-- Run inside psql and capture EXPLAIN ANALYZE output for the report.

\set ON_ERROR_STOP on
\pset pager off
\timing on

-- Reduce plan variance where possible.
SET jit = off;
SET track_io_timing = on;

-- Drop indexes to capture baseline
DROP INDEX IF EXISTS ix_runs_experiment_status_started;
DROP INDEX IF EXISTS ix_rmv_run_metric_scope_step;
DROP INDEX IF EXISTS ix_rmv_final_metric;
DROP INDEX IF EXISTS ix_experiments_project_id;
DROP INDEX IF EXISTS ix_runs_dataset_version_id;

ANALYZE experiments;
ANALYZE runs;
ANALYZE run_metric_values;
ANALYZE dataset_versions;

CHECKPOINT;
DISCARD ALL;

\echo '=== BASELINE (no indexes) - leaderboard (3 runs) ==='
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM fn_experiment_leaderboard(
    (SELECT experiment_id FROM experiments ORDER BY created_at LIMIT 1),
    'accuracy',
    'val',
    10
);
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM fn_experiment_leaderboard(
    (SELECT experiment_id FROM experiments ORDER BY created_at LIMIT 1),
    'accuracy',
    'val',
    10
);
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM fn_experiment_leaderboard(
    (SELECT experiment_id FROM experiments ORDER BY created_at LIMIT 1),
    'accuracy',
    'val',
    10
);

\echo '=== BASELINE (no indexes) - dataset trend (3 runs) ==='
EXPLAIN (ANALYZE, BUFFERS)
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
WHERE rmv.metric_id = (SELECT metric_id FROM metric_definitions WHERE key = 'accuracy' LIMIT 1)
  AND rmv.scope = 'val'
GROUP BY e.project_id, dv.dataset_version_id, dv.version_label
ORDER BY avg_value DESC
LIMIT 20;
EXPLAIN (ANALYZE, BUFFERS)
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
WHERE rmv.metric_id = (SELECT metric_id FROM metric_definitions WHERE key = 'accuracy' LIMIT 1)
  AND rmv.scope = 'val'
GROUP BY e.project_id, dv.dataset_version_id, dv.version_label
ORDER BY avg_value DESC
LIMIT 20;
EXPLAIN (ANALYZE, BUFFERS)
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
WHERE rmv.metric_id = (SELECT metric_id FROM metric_definitions WHERE key = 'accuracy' LIMIT 1)
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

ANALYZE experiments;
ANALYZE runs;
ANALYZE run_metric_values;
ANALYZE dataset_versions;

CHECKPOINT;
DISCARD ALL;

\echo '=== WITH INDEXES - leaderboard (3 runs) ==='
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM fn_experiment_leaderboard(
    (SELECT experiment_id FROM experiments ORDER BY created_at LIMIT 1),
    'accuracy',
    'val',
    10
);
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM fn_experiment_leaderboard(
    (SELECT experiment_id FROM experiments ORDER BY created_at LIMIT 1),
    'accuracy',
    'val',
    10
);
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM fn_experiment_leaderboard(
    (SELECT experiment_id FROM experiments ORDER BY created_at LIMIT 1),
    'accuracy',
    'val',
    10
);

\echo '=== WITH INDEXES - dataset trend (3 runs) ==='
EXPLAIN (ANALYZE, BUFFERS)
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
WHERE rmv.metric_id = (SELECT metric_id FROM metric_definitions WHERE key = 'accuracy' LIMIT 1)
  AND rmv.scope = 'val'
GROUP BY e.project_id, dv.dataset_version_id, dv.version_label
ORDER BY avg_value DESC
LIMIT 20;
EXPLAIN (ANALYZE, BUFFERS)
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
WHERE rmv.metric_id = (SELECT metric_id FROM metric_definitions WHERE key = 'accuracy' LIMIT 1)
  AND rmv.scope = 'val'
GROUP BY e.project_id, dv.dataset_version_id, dv.version_label
ORDER BY avg_value DESC
LIMIT 20;
EXPLAIN (ANALYZE, BUFFERS)
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
WHERE rmv.metric_id = (SELECT metric_id FROM metric_definitions WHERE key = 'accuracy' LIMIT 1)
  AND rmv.scope = 'val'
GROUP BY e.project_id, dv.dataset_version_id, dv.version_label
ORDER BY avg_value DESC
LIMIT 20;
