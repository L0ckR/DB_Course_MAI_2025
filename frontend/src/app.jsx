import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "./api.js";
import { clearSession, getSession, saveSession } from "./storage.js";

const scopes = ["train", "val", "test"];

const statusLabel = {
  queued: "Queued",
  running: "Running",
  finished: "Finished",
  failed: "Failed",
  killed: "Killed"
};

export default function App() {
  const [session, setSession] = useState(() => getSession());

  const handleLogin = (payload) => {
    saveSession(payload);
    setSession(payload);
  };

  const handleLogout = () => {
    clearSession();
    setSession(null);
  };

  return session ? (
    <Dashboard session={session} onLogout={handleLogout} />
  ) : (
    <LoginScreen onLogin={handleLogin} />
  );
}

function LoginScreen({ onLogin }) {
  const [userId, setUserId] = useState("");
  const [users, setUsers] = useState([]);
  const [emailQuery, setEmailQuery] = useState("");
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [status, setStatus] = useState({ state: "idle", message: "" });

  const loadUsers = async () => {
    setLoadingUsers(true);
    setStatus({ state: "idle", message: "" });
    try {
      const data = await apiFetch("/users?limit=500");
      setUsers(data);
      setStatus({ state: "success", message: "Users loaded" });
    } catch (err) {
      setStatus({ state: "error", message: err.message });
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleEmailLookup = () => {
    const match = users.find((user) => user.email === emailQuery.trim());
    if (match) {
      setUserId(match.user_id);
      setStatus({ state: "success", message: "User matched" });
    } else {
      setStatus({ state: "error", message: "No user found" });
    }
  };

  const handleSelectUser = (event) => {
    const selectedId = event.target.value;
    setUserId(selectedId);
  };

  const handleLoginSubmit = () => {
    if (!userId.trim()) {
      setStatus({ state: "error", message: "User id is required" });
      return;
    }

    const matched = users.find((user) => user.user_id === userId.trim());
    onLogin({
      user_id: userId.trim(),
      email: matched?.email || "",
      full_name: matched?.full_name || ""
    });
  };

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-header">
          <span className="eyebrow">RunAtlas</span>
          <h1>ML runs, clean and audited.</h1>
          <p>
            Connect to your database-backed experiment store and unlock dashboards,
            leaderboards, and audit trails in one place.
          </p>
        </div>

        <div className="auth-form">
          <label className="field">
            <span>User id</span>
            <input
              type="text"
              placeholder="UUID from users"
              value={userId}
              onChange={(event) => setUserId(event.target.value)}
            />
          </label>

          <div className="field-row">
            <label className="field">
              <span>Email lookup</span>
              <input
                type="email"
                placeholder="user@example.com"
                value={emailQuery}
                onChange={(event) => setEmailQuery(event.target.value)}
              />
            </label>
            <button
              className="btn ghost"
              type="button"
              onClick={handleEmailLookup}
              disabled={!users.length}
            >
              Find
            </button>
          </div>

          <div className="field-row">
            <button
              className="btn ghost"
              type="button"
              onClick={loadUsers}
              disabled={loadingUsers}
            >
              {loadingUsers ? "Loading..." : "Load users"}
            </button>
            <select className="select" onChange={handleSelectUser} value={userId}>
              <option value="">Pick a user</option>
              {users.map((user) => (
                <option key={user.user_id} value={user.user_id}>
                  {user.full_name} · {user.email}
                </option>
              ))}
            </select>
          </div>

          <button className="btn primary" type="button" onClick={handleLoginSubmit}>
            Enter workspace
          </button>
          {status.message && (
            <div className={`status ${status.state}`}>{status.message}</div>
          )}
        </div>
      </div>
      <div className="auth-aside">
        <div className="pill">Audit-ready</div>
        <h2>Stay in control</h2>
        <p>
          Use the same X-User-Id header as the backend to keep audit trails
          consistent. Every insert, update, and delete keeps a fingerprint.
        </p>
        <ul>
          <li>Project quality dashboards in seconds</li>
          <li>Leaderboard comparisons across runs</li>
          <li>Batch import monitoring for metrics</li>
        </ul>
      </div>
    </div>
  );
}

function Dashboard({ session, onLogout }) {
  const [projects, setProjects] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [runs, setRuns] = useState([]);
  const [datasets, setDatasets] = useState([]);
  const [projectId, setProjectId] = useState("");
  const [experimentId, setExperimentId] = useState("");
  const [metricKey, setMetricKey] = useState("");
  const [scope, setScope] = useState("val");
  const [limit, setLimit] = useState(10);
  const [projectDashboard, setProjectDashboard] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshIndex, setRefreshIndex] = useState(0);

  useEffect(() => {
    let isActive = true;

    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const [projectsData, experimentsData, metricsData, runsData, datasetsData] =
          await Promise.all([
            apiFetch("/projects?limit=500", {}, session),
            apiFetch("/experiments?limit=500", {}, session),
            apiFetch("/metric-definitions?limit=200", {}, session),
            apiFetch("/runs?limit=200", {}, session),
            apiFetch("/datasets?limit=200", {}, session)
          ]);
        if (!isActive) {
          return;
        }
        setProjects(projectsData);
        setExperiments(experimentsData);
        setMetrics(metricsData);
        setRuns(runsData);
        setDatasets(datasetsData);
      } catch (err) {
        if (isActive) {
          setError(err.message);
        }
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    };

    load();
    return () => {
      isActive = false;
    };
  }, [session, refreshIndex]);

  useEffect(() => {
    if (!projectId && projects.length) {
      setProjectId(projects[0].project_id);
    }
  }, [projects, projectId]);

  const projectExperiments = useMemo(() => {
    if (!projectId) {
      return experiments;
    }
    return experiments.filter((experiment) => experiment.project_id === projectId);
  }, [experiments, projectId]);

  useEffect(() => {
    if (!projectExperiments.length) {
      setExperimentId("");
      return;
    }
    const exists = projectExperiments.some(
      (experiment) => experiment.experiment_id === experimentId
    );
    if (!exists) {
      setExperimentId(projectExperiments[0].experiment_id);
    }
  }, [projectExperiments, experimentId]);

  useEffect(() => {
    if (!metricKey && metrics.length) {
      setMetricKey(metrics[0].key);
    }
  }, [metrics, metricKey]);

  useEffect(() => {
    let isActive = true;
    if (!projectId) {
      return;
    }
    apiFetch(`/reports/projects/${projectId}/dashboard`, {}, session)
      .then((data) => {
        if (isActive) {
          setProjectDashboard(data);
        }
      })
      .catch((err) => {
        if (isActive) {
          setError(err.message);
        }
      });

    return () => {
      isActive = false;
    };
  }, [projectId, session]);

  useEffect(() => {
    let isActive = true;
    if (!experimentId || !metricKey || !scope) {
      return;
    }
    const params = new URLSearchParams({
      metric_key: metricKey,
      scope,
      limit: String(limit)
    });
    apiFetch(`/reports/experiments/${experimentId}/leaderboard?${params}`, {}, session)
      .then((data) => {
        if (isActive) {
          setLeaderboard(data);
        }
      })
      .catch((err) => {
        if (isActive) {
          setError(err.message);
        }
      });

    return () => {
      isActive = false;
    };
  }, [experimentId, metricKey, scope, limit, session]);

  const statusCounts = useMemo(() => {
    const counts = { queued: 0, running: 0, finished: 0, failed: 0, killed: 0 };
    runs.forEach((run) => {
      counts[run.status] = (counts[run.status] || 0) + 1;
    });
    return counts;
  }, [runs]);

  const recentRuns = useMemo(() => {
    return [...runs]
      .sort((a, b) => (b.started_at || "").localeCompare(a.started_at || ""))
      .slice(0, 6);
  }, [runs]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="logo">RA</span>
          <div>
            <strong>RunAtlas</strong>
            <span>Experiment cockpit</span>
          </div>
        </div>
        <nav className="nav">
          <button className="nav-item active" type="button">
            Overview
          </button>
          <button className="nav-item" type="button">
            Leaderboards
          </button>
          <button className="nav-item" type="button">
            Runs
          </button>
          <button className="nav-item" type="button">
            Imports
          </button>
        </nav>
        <div className="sidebar-footer">
          <div className="user-badge">
            <span>{session.full_name || "Signed in"}</span>
            <small>{session.email || session.user_id}</small>
          </div>
          <button className="btn ghost" type="button" onClick={onLogout}>
            Sign out
          </button>
        </div>
      </aside>

      <main className="content">
        <header className="topbar">
          <div>
            <h1>Dashboard</h1>
            <p>Keep tabs on quality, velocity, and best-performing runs.</p>
          </div>
          <div className="topbar-actions">
            <button
              className="btn ghost"
              type="button"
              onClick={() => setRefreshIndex((value) => value + 1)}
            >
              Refresh data
            </button>
            <span className="pill">API {loading ? "syncing" : "ready"}</span>
          </div>
        </header>

        {error && <div className="status error">{error}</div>}

        <section className="grid two">
          <div className="card">
            <div className="card-head">
              <div>
                <h2>Project quality</h2>
                <p>Aggregates from v_project_quality_dashboard.</p>
              </div>
              <select
                className="select"
                value={projectId}
                onChange={(event) => setProjectId(event.target.value)}
              >
                <option value="">Select project</option>
                {projects.map((project) => (
                  <option key={project.project_id} value={project.project_id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="stat-grid">
              <StatCard
                label="Experiments"
                value={projectDashboard?.experiments_count ?? "-"}
              />
              <StatCard
                label="Runs"
                value={projectDashboard?.runs_count ?? "-"}
              />
              <StatCard
                label="Success rate"
                value={formatPercent(projectDashboard?.success_rate_pct)}
              />
              <StatCard
                label="Median train time"
                value={formatDuration(projectDashboard?.median_train_seconds)}
              />
              <StatCard
                label="Best metric"
                value={formatNumber(projectDashboard?.best_metric_value)}
              />
              <StatCard
                label="Best run"
                value={shortId(projectDashboard?.best_run_id)}
              />
            </div>
          </div>

          <div className="card">
            <div className="card-head">
              <div>
                <h2>Run health</h2>
                <p>Active and historical run distribution.</p>
              </div>
            </div>
            <div className="status-grid">
              {Object.keys(statusCounts).map((key) => (
                <div key={key} className={`status-pill ${key}`}>
                  <strong>{statusCounts[key]}</strong>
                  <span>{statusLabel[key]}</span>
                </div>
              ))}
            </div>
            <div className="mini-list">
              <h3>Recent runs</h3>
              {recentRuns.length === 0 && <EmptyState label="No runs yet" />}
              {recentRuns.map((run) => (
                <div key={run.run_id} className="list-row">
                  <div>
                    <strong>{run.run_name || "Untitled"}</strong>
                    <span>{shortId(run.run_id)}</span>
                  </div>
                  <div className={`badge ${run.status}`}>{statusLabel[run.status]}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="grid two">
          <div className="card">
            <div className="card-head">
              <div>
                <h2>Experiment leaderboard</h2>
                <p>Top runs for the chosen metric and scope.</p>
              </div>
            </div>
            <div className="filters">
              <select
                className="select"
                value={experimentId}
                onChange={(event) => setExperimentId(event.target.value)}
              >
                <option value="">Select experiment</option>
                {projectExperiments.map((experiment) => (
                  <option
                    key={experiment.experiment_id}
                    value={experiment.experiment_id}
                  >
                    {experiment.name}
                  </option>
                ))}
              </select>
              <select
                className="select"
                value={metricKey}
                onChange={(event) => setMetricKey(event.target.value)}
              >
                {metrics.map((metric) => (
                  <option key={metric.metric_id} value={metric.key}>
                    {metric.display_name}
                  </option>
                ))}
              </select>
              <select className="select" value={scope} onChange={(e) => setScope(e.target.value)}>
                {scopes.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
              <input
                className="input"
                type="number"
                min="1"
                max="100"
                value={limit}
                onChange={(event) => setLimit(Number(event.target.value))}
              />
            </div>

            <div className="table">
              <div className="table-row header">
                <span>Run</span>
                <span>Metric</span>
                <span>Started</span>
                <span>Status</span>
              </div>
              {leaderboard.length === 0 && <EmptyState label="No leaderboard data" />}
              {leaderboard.map((row) => (
                <div key={row.run_id} className="table-row">
                  <span>
                    <strong>{row.run_name || shortId(row.run_id)}</strong>
                    <small>{shortId(row.run_id)}</small>
                  </span>
                  <span>{formatNumber(row.metric_value)}</span>
                  <span>{formatDate(row.started_at)}</span>
                  <span className={`badge ${row.status}`}>{statusLabel[row.status]}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <div className="card-head">
              <div>
                <h2>Dataset pulse</h2>
                <p>Coverage of datasets across active projects.</p>
              </div>
            </div>
            <div className="stat-grid">
              <StatCard label="Datasets" value={datasets.length} />
              <StatCard label="Projects" value={projects.length} />
              <StatCard label="Experiments" value={experiments.length} />
              <StatCard label="Metric defs" value={metrics.length} />
            </div>
            <div className="mini-list">
              <h3>Latest datasets</h3>
              {datasets.slice(0, 5).map((dataset) => (
                <div key={dataset.dataset_id} className="list-row">
                  <div>
                    <strong>{dataset.name}</strong>
                    <span>{dataset.task_type}</span>
                  </div>
                  <div className="tag">{shortId(dataset.dataset_id)}</div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function EmptyState({ label }) {
  return (
    <div className="empty">
      <span>{label}</span>
    </div>
  );
}

function formatNumber(value) {
  if (value === null || value === undefined) {
    return "-";
  }
  return Number(value).toFixed(4);
}

function formatPercent(value) {
  if (value === null || value === undefined) {
    return "-";
  }
  return `${Number(value).toFixed(1)}%`;
}

function formatDuration(value) {
  if (!value) {
    return "-";
  }
  const seconds = Number(value);
  if (Number.isNaN(seconds)) {
    return "-";
  }
  if (seconds < 60) {
    return `${seconds.toFixed(0)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remaining = Math.floor(seconds % 60);
  return `${minutes}m ${remaining}s`;
}

function formatDate(value) {
  if (!value) {
    return "-";
  }
  try {
    return new Date(value).toLocaleDateString();
  } catch (err) {
    return "-";
  }
}

function shortId(value) {
  if (!value) {
    return "-";
  }
  const str = String(value);
  return `${str.slice(0, 6)}...${str.slice(-4)}`;
}
