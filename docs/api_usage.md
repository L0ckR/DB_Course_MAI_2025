# API usage: scikit-learn experiment

This example runs a real ML experiment (Logistic Regression on the scikit-learn
breast cancer dataset) and logs everything via the API.

Prereqs:
- `docker compose up --build`
- `docker compose exec backend alembic upgrade head`
- `docker compose exec backend python scripts/seed.py`
- `pip install requests scikit-learn`

Set credentials (use values from `.env`, e.g. `SEED_TEST_USER_EMAIL` /
`SEED_TEST_USER_PASSWORD`):

```bash
export API_URL=http://localhost:8000
export API_EMAIL=your@email
export API_PASSWORD=your_password
export NO_PROXY=localhost,127.0.0.1
```

Run the demo script:

```bash
python scripts/demo_sklearn_experiment.py
```

What the script does:
- creates org, project, dataset, dataset version, experiment, and run
- trains a real model and logs final metrics (`accuracy`, `f1`, `auc`, `val_loss`)
- logs a few step metrics for charts
- registers a model artifact and links it to the run
- queries leaderboard and dashboard endpoints (functions + views)
- prints a small audit log sample

Optional demos:

```bash
# Batch import with row-level error logging
python scripts/demo_batch_import.py

# Performance demo (EXPLAIN ANALYZE before/after indexes)
./scripts/run_perf_demo.sh > docs/perf_demo_output.txt
```
