-- Example performance demo script
-- Adjust identifiers and run inside psql. Capture EXPLAIN ANALYZE output into docs/perf_report.md.

-- Drop indexes to capture baseline
DROP INDEX IF EXISTS ix_runs_experiment_status_started;
DROP INDEX IF EXISTS ix_rmv_run_metric_scope_step;

EXPLAIN ANALYZE
SELECT *
FROM fn_experiment_leaderboard(
    '00000000-0000-0000-0000-000000000000',
    'accuracy',
    'val',
    10
);

-- Recreate indexes
CREATE INDEX IF NOT EXISTS ix_runs_experiment_status_started
    ON runs (experiment_id, status, started_at);

CREATE INDEX IF NOT EXISTS ix_rmv_run_metric_scope_step
    ON run_metric_values (run_id, metric_id, scope, step);

EXPLAIN ANALYZE
SELECT *
FROM fn_experiment_leaderboard(
    '00000000-0000-0000-0000-000000000000',
    'accuracy',
    'val',
    10
);
