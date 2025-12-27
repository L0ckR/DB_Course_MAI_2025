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

const navItems = [
  { id: "overview", label: "Overview" },
  { id: "leaderboard", label: "Leaderboards" },
  { id: "runs", label: "Runs" },
  { id: "imports", label: "Imports" }
];

const tabCopy = {
  overview: {
    title: "Overview",
    description: "Keep tabs on quality, velocity, and dataset coverage."
  },
  leaderboard: {
    title: "Leaderboards",
    description: "Compare top runs across metrics and scopes."
  },
  runs: {
    title: "Runs",
    description: "Review experiment activity and execution status."
  },
  imports: {
    title: "Imports",
    description: "Track batch imports and common workflows."
  }
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
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState({ state: "idle", message: "" });

  const handleSubmit = async () => {
    setStatus({ state: "idle", message: "" });
    if (!email.trim() || !password.trim()) {
      setStatus({ state: "error", message: "Email and password are required" });
      return;
    }
    if (mode === "register" && !fullName.trim()) {
      setStatus({ state: "error", message: "Full name is required" });
      return;
    }

    setLoading(true);
    try {
      const payload =
        mode === "login"
          ? { email: email.trim(), password }
          : { email: email.trim(), full_name: fullName.trim(), password };

      const data = await apiFetch(`/auth/${mode}`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
      onLogin({
        user_id: data.user_id,
        email: data.email,
        full_name: data.full_name,
        access_token: data.access_token,
        token_type: data.token_type
      });
    } catch (err) {
      setStatus({ state: "error", message: err.message });
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setMode((current) => (current === "login" ? "register" : "login"));
    setStatus({ state: "idle", message: "" });
  };

  return (
    <div className="auth-shell">
      <div className="auth-card compact">
        <div className="auth-header basic">
          <div className="brand-row">
            <span className="logo small">RA</span>
            <div>
              <h1>RunAtlas</h1>
              <p>Sign in to your tracking workspace.</p>
            </div>
          </div>
        </div>

        <div className="auth-form">
          {mode === "register" && (
            <label className="field">
              <span>Full name</span>
              <input
                type="text"
                placeholder="Jane Doe"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
              />
            </label>
          )}
          <label className="field">
            <span>Email</span>
            <input
              type="email"
              placeholder="you@company.ai"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>

          <label className="field">
            <span>Password</span>
            <input
              type="password"
              placeholder="********"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>

          <button className="btn primary full" type="button" onClick={handleSubmit}>
            {loading ? "Working..." : mode === "login" ? "Sign in" : "Create account"}
          </button>
          <button className="btn ghost full" type="button" onClick={toggleMode}>
            {mode === "login"
              ? "Create a new account"
              : "Back to sign in"}
          </button>
          {status.message && (
            <div className={`status ${status.state}`}>{status.message}</div>
          )}
        </div>
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
  const [runExperimentId, setRunExperimentId] = useState("");
  const [metricKey, setMetricKey] = useState("");
  const [scope, setScope] = useState("val");
  const [limit, setLimit] = useState(10);
  const [projectDashboard, setProjectDashboard] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshIndex, setRefreshIndex] = useState(0);
  const [activeTab, setActiveTab] = useState("overview");

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
    if (!runExperimentId) {
      return;
    }
    const exists = projectExperiments.some(
      (experiment) => experiment.experiment_id === runExperimentId
    );
    if (!exists) {
      setRunExperimentId("");
    }
  }, [projectExperiments, runExperimentId]);

  useEffect(() => {
    if (!metricKey && metrics.length) {
      setMetricKey(metrics[0].key);
    }
  }, [metrics, metricKey]);

  useEffect(() => {
    let isActive = true;
    if (activeTab !== "overview") {
      return () => {
        isActive = false;
      };
    }
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
  }, [activeTab, projectId, session]);

  useEffect(() => {
    let isActive = true;
    if (activeTab !== "leaderboard") {
      return () => {
        isActive = false;
      };
    }
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
  }, [activeTab, experimentId, metricKey, scope, limit, session]);

  const experimentLookup = useMemo(() => {
    const map = {};
    experiments.forEach((experiment) => {
      map[experiment.experiment_id] = experiment;
    });
    return map;
  }, [experiments]);

  const projectExperimentIds = useMemo(
    () => new Set(projectExperiments.map((experiment) => experiment.experiment_id)),
    [projectExperiments]
  );

  const projectRuns = useMemo(() => {
    if (!projectId) {
      return runs;
    }
    return runs.filter((run) => projectExperimentIds.has(run.experiment_id));
  }, [projectId, projectExperimentIds, runs]);

  const filteredRuns = useMemo(() => {
    if (!runExperimentId) {
      return projectRuns;
    }
    return projectRuns.filter((run) => run.experiment_id === runExperimentId);
  }, [projectRuns, runExperimentId]);

  const sortedProjectRuns = useMemo(() => {
    return [...projectRuns].sort((a, b) =>
      (b.started_at || "").localeCompare(a.started_at || "")
    );
  }, [projectRuns]);

  const sortedRuns = useMemo(() => {
    return [...filteredRuns].sort((a, b) =>
      (b.started_at || "").localeCompare(a.started_at || "")
    );
  }, [filteredRuns]);

  const statusCounts = useMemo(() => {
    const counts = { queued: 0, running: 0, finished: 0, failed: 0, killed: 0 };
    projectRuns.forEach((run) => {
      counts[run.status] = (counts[run.status] || 0) + 1;
    });
    return counts;
  }, [projectRuns]);

  const recentRuns = useMemo(() => {
    return sortedProjectRuns.slice(0, 6);
  }, [sortedProjectRuns]);

  const activeMeta = tabCopy[activeTab] || tabCopy.overview;

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
          {navItems.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${activeTab === item.id ? "active" : ""}`}
              type="button"
              onClick={() => setActiveTab(item.id)}
            >
              {item.label}
            </button>
          ))}
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
            <h1>{activeMeta.title}</h1>
            <p>{activeMeta.description}</p>
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

        {activeTab === "overview" && (
          <>
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
                      <div className={`badge ${run.status}`}>
                        {statusLabel[run.status]}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="grid two">
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
          </>
        )}

        {activeTab === "leaderboard" && (
          <section className="grid">
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
                <select
                  className="select"
                  value={scope}
                  onChange={(e) => setScope(e.target.value)}
                >
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
                {leaderboard.length === 0 && (
                  <EmptyState label="No leaderboard data" />
                )}
                {leaderboard.map((row) => (
                  <div key={row.run_id} className="table-row">
                    <span>
                      <strong>{row.run_name || shortId(row.run_id)}</strong>
                      <small>{shortId(row.run_id)}</small>
                    </span>
                    <span>{formatNumber(row.metric_value)}</span>
                    <span>{formatDate(row.started_at)}</span>
                    <span className={`badge ${row.status}`}>
                      {statusLabel[row.status]}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {activeTab === "runs" && (
          <section className="grid">
            <div className="card">
              <div className="card-head">
                <div>
                  <h2>Runs</h2>
                  <p>Latest runs for the selected project.</p>
                </div>
              </div>
              <div className="filters">
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
                <select
                  className="select"
                  value={runExperimentId}
                  onChange={(event) => setRunExperimentId(event.target.value)}
                >
                  <option value="">All experiments</option>
                  {projectExperiments.map((experiment) => (
                    <option
                      key={experiment.experiment_id}
                      value={experiment.experiment_id}
                    >
                      {experiment.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="table">
                <div className="table-row header">
                  <span>Run</span>
                  <span>Experiment</span>
                  <span>Started</span>
                  <span>Status</span>
                </div>
                {sortedRuns.length === 0 && <EmptyState label="No runs yet" />}
                {sortedRuns.slice(0, 20).map((run) => {
                  const experiment = experimentLookup[run.experiment_id];
                  return (
                    <div key={run.run_id} className="table-row">
                      <span>
                        <strong>{run.run_name || "Untitled"}</strong>
                        <small>{shortId(run.run_id)}</small>
                      </span>
                      <span>
                        {experiment?.name || "Unknown experiment"}
                        <small>{shortId(run.experiment_id)}</small>
                      </span>
                      <span>{formatDate(run.started_at)}</span>
                      <span className={`badge ${run.status}`}>
                        {statusLabel[run.status]}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>
        )}

        {activeTab === "imports" && (
          <section className="grid">
            <div className="card">
              <div className="card-head">
                <div>
                  <h2>Batch import</h2>
                  <p>Send metrics or datasets in CSV/JSON.</p>
                </div>
              </div>
              <div className="mini-list">
                <div className="list-row">
                  <div>
                    <strong>Endpoint</strong>
                    <span>/api/batch-import</span>
                  </div>
                  <div className="tag">POST</div>
                </div>
                <div className="list-row">
                  <div>
                    <strong>Job types</strong>
                    <span>metrics, datasets</span>
                  </div>
                  <div className="tag">csv/json</div>
                </div>
                <div className="list-row">
                  <div>
                    <strong>Auth</strong>
                    <span>Bearer token required</span>
                  </div>
                  <div className="tag">RBAC</div>
                </div>
              </div>
            </div>
          </section>
        )}
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
