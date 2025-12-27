-- Business-oriented analytical queries

-- 1) Experiment leaderboard with delta vs experiment average (final metric)
-- Replace :metric_key and :scope with your values.
WITH final_metrics AS (
    SELECT
        r.experiment_id,
        r.run_id,
        r.run_name,
        rmv.value,
        md.goal,
        ROW_NUMBER() OVER (
            PARTITION BY r.experiment_id
            ORDER BY
              CASE WHEN md.goal = 'min' THEN rmv.value END ASC,
              CASE WHEN md.goal = 'max' THEN rmv.value END DESC,
              CASE WHEN md.goal = 'last' THEN rmv.recorded_at END DESC
        ) AS rn,
        AVG(rmv.value) OVER (PARTITION BY r.experiment_id) AS avg_value
    FROM runs r
    JOIN run_metric_values rmv ON rmv.run_id = r.run_id AND rmv.step IS NULL
    JOIN metric_definitions md ON md.metric_id = rmv.metric_id
    WHERE md.key = :metric_key
      AND rmv.scope = :scope
)
SELECT
    experiment_id,
    run_id,
    run_name,
    value AS best_value,
    avg_value,
    value - avg_value AS delta_vs_avg
FROM final_metrics
WHERE rn = 1
ORDER BY delta_vs_avg DESC;

-- 2) Dataset version quality trend per project (final metric)
WITH dv_metrics AS (
    SELECT
        e.project_id,
        dv.dataset_version_id,
        dv.version_label,
        rmv.metric_id,
        rmv.scope,
        COUNT(*) AS run_count,
        AVG(rmv.value) AS avg_value,
        MIN(rmv.value) AS min_value,
        MAX(rmv.value) AS max_value
    FROM dataset_versions dv
    JOIN runs r ON r.dataset_version_id = dv.dataset_version_id
    JOIN experiments e ON e.experiment_id = r.experiment_id
    JOIN run_metric_values rmv ON rmv.run_id = r.run_id AND rmv.step IS NULL
    WHERE rmv.metric_id = :metric_id
      AND rmv.scope = :scope
    GROUP BY e.project_id, dv.dataset_version_id, dv.version_label, rmv.metric_id, rmv.scope
)
SELECT
    project_id,
    dataset_version_id,
    version_label,
    run_count,
    avg_value,
    min_value,
    max_value
FROM dv_metrics
ORDER BY project_id, avg_value DESC;

-- 3) Artifact reuse across runs
SELECT
    a.project_id,
    a.artifact_id,
    a.artifact_type,
    COUNT(ra.run_id) AS run_usage_count
FROM artifacts a
JOIN run_artifacts ra ON ra.artifact_id = a.artifact_id
GROUP BY a.project_id, a.artifact_id, a.artifact_type
HAVING COUNT(ra.run_id) > 1
ORDER BY run_usage_count DESC;
