# Performance Report

This report should contain EXPLAIN ANALYZE output before and after indexes.
Run `sql/perf_demo.sql` against a seeded database and paste results below.

## Query: Experiment leaderboard (before indexes)

```
Function Scan on fn_experiment_leaderboard  (cost=0.25..10.25 rows=1000 width=96) (actual time=6.479..6.480 rows=10 loops=1)
Planning Time: 1.323 ms
Execution Time: 8.294 ms
(3 rows)
```

## Query: Experiment leaderboard (after indexes)

```
Function Scan on fn_experiment_leaderboard  (cost=0.25..10.25 rows=1000 width=96) (actual time=0.844..0.845 rows=10 loops=1)
Planning Time: 0.028 ms
Execution Time: 0.857 ms
(3 rows)
```

## Query: Dataset version trend (before indexes)

```
Limit  (cost=1334.05..1334.10 rows=20 width=51) (actual time=2.398..2.402 rows=20 loops=1)
  ->  Sort  (cost=1334.05..1336.66 rows=1042 width=51) (actual time=2.397..2.400 rows=20 loops=1)
        Sort Key: (avg(rmv.value)) DESC
        Sort Method: top-N heapsort  Memory: 29kB
        ->  HashAggregate  (cost=1293.30..1306.32 rows=1042 width=51) (actual time=2.258..2.327 rows=826 loops=1)
              Group Key: e.project_id, dv.dataset_version_id
              Batches: 1  Memory Usage: 321kB
              ->  Hash Join  (cost=51.45..1282.88 rows=1042 width=43) (actual time=0.316..1.927 rows=1000 loops=1)
                    Hash Cond: (r.experiment_id = e.experiment_id)
                    ->  Hash Join  (cost=47.20..1275.78 rows=1042 width=43) (actual time=0.254..1.788 rows=1000 loops=1)
                          Hash Cond: (r.dataset_version_id = dv.dataset_version_id)
                          ->  Hash Join  (cost=40.50..1266.25 rows=1042 width=40) (actual time=0.217..1.646 rows=1000 loops=1)
                                Hash Cond: (rmv.run_id = r.run_id)
                                ->  Seq Scan on run_metric_values rmv  (cost=0.00..1223.00 rows=1042 width=24) (actual time=0.002..1.336 rows=1000 loops=1)
                                      Filter: ((step IS NULL) AND (metric_id = 'c96b1d1f-1b40-4961-a49e-93d7429c33dd'::uuid) AND (scope = 'val'::text))
                                      Rows Removed by Filter: 43000
                                ->  Hash  (cost=28.00..28.00 rows=1000 width=48) (actual time=0.177..0.178 rows=1000 loops=1)
                                      Buckets: 1024  Batches: 1  Memory Usage: 87kB
                                      ->  Seq Scan on runs r  (cost=0.00..28.00 rows=1000 width=48) (actual time=0.002..0.065 rows=1000 loops=1)
                          ->  Hash  (cost=5.20..5.20 rows=120 width=19) (actual time=0.025..0.025 rows=120 loops=1)
                                Buckets: 1024  Batches: 1  Memory Usage: 14kB
                                ->  Seq Scan on dataset_versions dv  (cost=0.00..5.20 rows=120 width=19) (actual time=0.003..0.016 rows=120 loops=1)
                    ->  Hash  (cost=3.00..3.00 rows=100 width=32) (actual time=0.030..0.030 rows=100 loops=1)
                          Buckets: 1024  Batches: 1  Memory Usage: 15kB
                          ->  Seq Scan on experiments e  (cost=0.00..3.00 rows=100 width=32) (actual time=0.004..0.013 rows=100 loops=1)
Planning Time: 0.696 ms
Execution Time: 2.496 ms
(27 rows)
```

## Query: Dataset version trend (after indexes)

```
Limit  (cost=742.25..742.30 rows=20 width=51) (actual time=1.164..1.169 rows=20 loops=1)
  ->  Sort  (cost=742.25..744.86 rows=1042 width=51) (actual time=1.164..1.167 rows=20 loops=1)
        Sort Key: (avg(rmv.value)) DESC
        Sort Method: top-N heapsort  Memory: 29kB
        ->  HashAggregate  (cost=701.50..714.53 rows=1042 width=51) (actual time=1.037..1.100 rows=826 loops=1)
              Group Key: e.project_id, dv.dataset_version_id
              Batches: 1  Memory Usage: 321kB
              ->  Hash Join  (cost=94.41..691.08 rows=1042 width=43) (actual time=0.440..0.802 rows=1000 loops=1)
                    Hash Cond: (r.experiment_id = e.experiment_id)
                    ->  Hash Join  (cost=90.16..683.99 rows=1042 width=43) (actual time=0.418..0.704 rows=1000 loops=1)
                          Hash Cond: (r.dataset_version_id = dv.dataset_version_id)
                          ->  Hash Join  (cost=83.46..674.45 rows=1042 width=40) (actual time=0.396..0.600 rows=1000 loops=1)
                                Hash Cond: (rmv.run_id = r.run_id)
                                ->  Bitmap Heap Scan on run_metric_values rmv  (cost=42.96..631.20 rows=1042 width=24) (actual time=0.233..0.330 rows=1000 loops=1)
                                      Recheck Cond: ((metric_id = 'c96b1d1f-1b40-4961-a49e-93d7429c33dd'::uuid) AND (scope = 'val'::text) AND (step IS NULL))
                                      Heap Blocks: exact=50
                                      ->  Bitmap Index Scan on ix_rmv_final_metric  (cost=0.00..42.70 rows=1042 width=0) (actual time=0.224..0.225 rows=1000 loops=1)
                                            Index Cond: ((metric_id = 'c96b1d1f-1b40-4961-a49e-93d7429c33dd'::uuid) AND (scope = 'val'::text))
                                ->  Hash  (cost=28.00..28.00 rows=1000 width=48) (actual time=0.158..0.159 rows=1000 loops=1)
                                      Buckets: 1024  Batches: 1  Memory Usage: 87kB
                                      ->  Seq Scan on runs r  (cost=0.00..28.00 rows=1000 width=48) (actual time=0.002..0.092 rows=1000 loops=1)
                          ->  Hash  (cost=5.20..5.20 rows=120 width=19) (actual time=0.017..0.017 rows=120 loops=1)
                                Buckets: 1024  Batches: 1  Memory Usage: 14kB
                                ->  Seq Scan on dataset_versions dv  (cost=0.00..5.20 rows=120 width=19) (actual time=0.002..0.010 rows=120 loops=1)
                    ->  Hash  (cost=3.00..3.00 rows=100 width=32) (actual time=0.018..0.018 rows=100 loops=1)
                          Buckets: 1024  Batches: 1  Memory Usage: 15kB
                          ->  Seq Scan on experiments e  (cost=0.00..3.00 rows=100 width=32) (actual time=0.005..0.010 rows=100 loops=1)
Planning Time: 0.457 ms
Execution Time: 1.215 ms
(29 rows)
```
