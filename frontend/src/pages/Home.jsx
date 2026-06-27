import { useEffect, useMemo, useState } from "react";

import api from "../api/api";

const HISTORY_KEY = "codeguard.analysis.history";

const navItems = [
  ["dashboard", "Dashboard", "dashboard", true],
  ["analytics", "New Analysis", "analysis", true],
  ["history", "History", "history", true],
  ["assessment", "Reports", "history", false],
  ["rule", "Standards", "dashboard", false],
  ["science", "Test Gen", "analysis", false],
];

function Home() {
  const [activeView, setActiveView] = useState("dashboard");
  const [repository, setRepository] = useState(null);
  const [analysisTitle, setAnalysisTitle] = useState("");
  const [bugReport, setBugReport] = useState("");
  const [errorLog, setErrorLog] = useState("");
  const [summary, setSummary] = useState(null);
  const [suspects, setSuspects] = useState([]);
  const [diagnosis, setDiagnosis] = useState(null);
  const [agentReports, setAgentReports] = useState([]);
  const [history, setHistory] = useState(() => loadSavedHistory());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, 25)));
  }, [history]);

  const repositoryName = useMemo(() => {
    if (!repository?.name) return "No source selected";
    return repository.name.replace(/\.zip$/i, "");
  }, [repository]);

  const hasResult = Boolean(summary || diagnosis || suspects.length);
  const confidence = diagnosis?.confidence || "Pending";
  const confidenceClass = getConfidenceClass(confidence);

  const dashboardStats = useMemo(() => {
    const totalSuspects = history.reduce((total, run) => total + (run.suspects?.length || 0), 0);
    const highConfidence = history.filter((run) => {
      return String(run.diagnosis?.confidence || "").toLowerCase().includes("high");
    }).length;
    const correctedCode = history.filter((run) => run.diagnosis?.corrected_code).length;

    return {
      analyses: history.length,
      suspects: totalSuspects,
      highConfidence,
      correctedCode,
    };
  }, [history]);

  async function analyze(event) {
    event.preventDefault();

    if (!repository) {
      setError("Select a repository ZIP before starting analysis.");
      return;
    }

    if (!bugReport.trim()) {
      setError("Add diagnostic context before starting analysis.");
      return;
    }

    const formData = new FormData();
    formData.append("repository", repository);
    formData.append("bug_report", [analysisTitle, bugReport].filter(Boolean).join("\n\n"));
    formData.append("error_log", errorLog);

    setLoading(true);
    setError("");

    try {
      const response = await api.post("/api/analyze", formData);
      const nextSummary = response.data.summary;
      const nextSuspects = response.data.suspects || [];
      const nextDiagnosis = response.data.diagnosis || {};
      const nextAgentReports = response.data.agent_reports || [];

      setSummary(nextSummary);
      setSuspects(nextSuspects);
      setDiagnosis(nextDiagnosis);
      setAgentReports(nextAgentReports);

      const historyEntry = {
        id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
        title: analysisTitle || repositoryName,
        repositoryName,
        bugReport,
        errorLog,
        summary: nextSummary,
        suspects: nextSuspects,
        diagnosis: nextDiagnosis,
        agentReports: nextAgentReports,
        createdAt: new Date().toISOString(),
      };

      setHistory((current) => [historyEntry, ...current].slice(0, 25));
      setActiveView("dashboard");
    } catch (err) {
      setError(err?.response?.data?.detail || "Analysis failed. Check the backend server and API key.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  function resetAnalysis() {
    setRepository(null);
    setAnalysisTitle("");
    setBugReport("");
    setErrorLog("");
    setSummary(null);
    setSuspects([]);
    setDiagnosis(null);
    setAgentReports([]);
    setError("");
    setActiveView("analysis");
  }

  function loadHistoryRun(run) {
    setAnalysisTitle(run.title || "");
    setBugReport(run.bugReport || "");
    setErrorLog(run.errorLog || "");
    setSummary(run.summary || null);
    setSuspects(run.suspects || []);
    setDiagnosis(run.diagnosis || null);
    setAgentReports(run.agentReports || []);
    setError("");
    setActiveView("analysis");
  }

  function clearHistory() {
    setHistory([]);
  }

  return (
    <div className="app-shell">
      <aside className="side-nav">
        <div className="brand">
          <span className="material-symbols-outlined brand-icon">security</span>
          <div>
            <h1>CodeGuard AI</h1>
            <p>Debug. Test. Verify.</p>
          </div>
        </div>

        <nav className="nav-list" aria-label="Main navigation">
          {navItems.map(([icon, label, view, canBeActive]) => (
            <button
              className={`nav-item ${canBeActive && activeView === view ? "active" : ""}`}
              key={label}
              type="button"
              onClick={() => setActiveView(view)}
            >
              <span className="material-symbols-outlined">{icon}</span>
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="nav-footer">
          {[
            ["api", "API"],
            ["settings", "Settings"],
            ["description", "Docs"],
          ].map(([icon, label]) => (
            <button className="nav-item compact" key={label} type="button">
              <span className="material-symbols-outlined">{icon}</span>
              <span>{label}</span>
            </button>
          ))}
        </div>
      </aside>

      <div className="workspace">
        <header className="top-bar">
          <div className="breadcrumbs" aria-label="Breadcrumb">
            <span>Projects</span>
            <span className="material-symbols-outlined">chevron_right</span>
            <span>{activeView === "dashboard" ? "Overview" : repositoryName}</span>
            <span className="material-symbols-outlined">chevron_right</span>
            <strong>{getViewTitle(activeView, hasResult)}</strong>
          </div>

          <div className="top-actions">
            <span className="branch-chip">Branch: main</span>
            <span className={`status-chip ${loading ? "warning" : "success"}`}>
              {loading ? "Agents running" : "API online"}
            </span>
            <button className="icon-button" type="button" aria-label="Notifications">
              <span className="material-symbols-outlined">notifications</span>
            </button>
            <button className="icon-button" type="button" aria-label="Help">
              <span className="material-symbols-outlined">help</span>
            </button>
          </div>
        </header>

        {activeView === "dashboard" && (
          <DashboardView
            dashboardStats={dashboardStats}
            diagnosis={diagnosis}
            history={history}
            setActiveView={setActiveView}
            summary={summary}
            suspects={suspects}
            loadHistoryRun={loadHistoryRun}
          />
        )}

        {activeView === "analysis" && (
          <AnalysisView
            agentReports={agentReports}
            analysisTitle={analysisTitle}
            bugReport={bugReport}
            confidence={confidence}
            confidenceClass={confidenceClass}
            diagnosis={diagnosis}
            error={error}
            errorLog={errorLog}
            loading={loading}
            repository={repository}
            resetAnalysis={resetAnalysis}
            setAnalysisTitle={setAnalysisTitle}
            setBugReport={setBugReport}
            setErrorLog={setErrorLog}
            setRepository={setRepository}
            summary={summary}
            suspects={suspects}
            analyze={analyze}
          />
        )}

        {activeView === "history" && (
          <HistoryView
            clearHistory={clearHistory}
            history={history}
            loadHistoryRun={loadHistoryRun}
            setActiveView={setActiveView}
          />
        )}
      </div>
    </div>
  );
}

function DashboardView({
  dashboardStats,
  diagnosis,
  history,
  loadHistoryRun,
  setActiveView,
  summary,
  suspects,
}) {
  const latestRun = history[0];
  const activityData = buildActivityData(history);

  return (
    <main className="content-canvas">
      <section className="page-heading">
        <div>
          <p className="eyebrow">Developer Quality Overview</p>
          <h2>Dashboard</h2>
        </div>
        <button className="primary-button" type="button" onClick={() => setActiveView("analysis")}>
          <span className="material-symbols-outlined">play_arrow</span>
          Start New Analysis
        </button>
      </section>

      <section className="metric-grid" aria-label="Dashboard metrics">
        <MetricCard icon="analytics" label="Analyses Run" value={dashboardStats.analyses} tone="primary" />
        <MetricCard icon="bug_report" label="Suspects Found" value={dashboardStats.suspects} tone="danger" />
        <MetricCard icon="verified" label="High Confidence" value={dashboardStats.highConfidence} tone="secondary" />
        <MetricCard icon="edit_document" label="Code Fixes" value={dashboardStats.correctedCode} tone="tertiary" />
      </section>

      <section className="dashboard-grid">
        <div className="dashboard-main">
          <section className="panel chart-panel">
            <div className="panel-header">
              <div>
                <h3>
                  <span className="material-symbols-outlined">monitoring</span>
                  Analysis Activity
                </h3>
                <p>{history.length ? "Each bar is a recent analysis, scaled by suspicious functions found" : "Activity appears after the first run"}</p>
              </div>
            </div>
            {activityData.length ? (
              <div className="activity-chart" aria-label="Recent analysis activity">
                {activityData.map((item) => (
                  <div className="activity-bar-item" key={item.id}>
                    <div className="activity-bar-track">
                      <span
                        className="activity-bar-fill"
                        style={{ "--height": `${item.height}%` }}
                        title={`${item.label}: ${item.suspects} suspicious functions`}
                      />
                    </div>
                    <span className="activity-bar-label">{item.shortLabel}</span>
                    <strong>{item.suspects}</strong>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state inline">
                <span className="material-symbols-outlined">monitoring</span>
                <p>Run an analysis to start building the activity chart.</p>
              </div>
            )}
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <h3>
                  <span className="material-symbols-outlined">folder_open</span>
                  Current Repository Summary
                </h3>
                <p>{summary ? "Latest analysis result" : "Run an analysis to populate this panel"}</p>
              </div>
            </div>
            <div className="summary-strip">
              <MiniStat label="Python files" value={summary?.python_files ?? "--"} />
              <MiniStat label="Functions" value={summary?.functions ?? "--"} />
              <MiniStat label="Classes" value={summary?.classes ?? "--"} />
              <MiniStat label="Suspects" value={suspects.length || "--"} />
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <h3>
                  <span className="material-symbols-outlined">history</span>
                  Recent Analyses
                </h3>
                <p>{history.length ? "Select a run to inspect it" : "No history yet"}</p>
              </div>
              <button className="secondary-button small" type="button" onClick={() => setActiveView("history")}>
                View All
              </button>
            </div>
            <RunList emptyText="No analyses have been run yet." runs={history.slice(0, 5)} onOpen={loadHistoryRun} />
          </section>
        </div>

        <aside className="dashboard-side">
          <section className="panel diagnosis-panel">
            <div className="panel-header">
              <div>
                <h3>
                  <span className="material-symbols-outlined">psychology</span>
                  Latest Diagnosis
                </h3>
                <p>{latestRun ? latestRun.title : "No diagnosis yet"}</p>
              </div>
              <span className={`status-chip ${getConfidenceClass(diagnosis?.confidence)}`}>
                {diagnosis?.confidence || "Pending"}
              </span>
            </div>
            {diagnosis ? (
              <div className="diagnosis-content">
                <ResultBlock label="Root Cause" value={diagnosis.root_cause} />
                <ResultBlock label="Suggested Fix" value={diagnosis.suggested_fix} />
              </div>
            ) : (
              <div className="empty-state">
                <span className="material-symbols-outlined">terminal</span>
                <p>Run an analysis to see the latest diagnosis.</p>
              </div>
            )}
          </section>
        </aside>
      </section>
    </main>
  );
}

function AnalysisView({
  agentReports,
  analysisTitle,
  analyze,
  bugReport,
  confidence,
  confidenceClass,
  diagnosis,
  error,
  errorLog,
  loading,
  repository,
  resetAnalysis,
  setAnalysisTitle,
  setBugReport,
  setErrorLog,
  setRepository,
  summary,
  suspects,
}) {
  return (
    <main className="content-canvas">
      <section className="page-heading">
        <div>
          <p className="eyebrow">AI Multi-Agent Bug Analyzer</p>
          <h2>New Analysis Workspace</h2>
        </div>
        <button className="secondary-button" type="button" onClick={resetAnalysis}>
          <span className="material-symbols-outlined">restart_alt</span>
          Reset
        </button>
      </section>

      <section className="metric-grid" aria-label="Analysis metrics">
        <MetricCard icon="folder_open" label="Python Files" value={summary?.python_files ?? "--"} tone="primary" />
        <MetricCard icon="function" label="Functions" value={summary?.functions ?? "--"} tone="secondary" />
        <MetricCard icon="schema" label="Classes" value={summary?.classes ?? "--"} tone="tertiary" />
        <MetricCard icon="bug_report" label="Suspects" value={suspects.length || "--"} tone="danger" />
      </section>

      <section className="analysis-grid">
        <form className="analysis-panel" onSubmit={analyze}>
          <div className="panel-header">
            <div>
              <h3>
                <span className="material-symbols-outlined">folder_managed</span>
                Target Source
              </h3>
              <p>{repository ? repository.name : "Repository ZIP required"}</p>
            </div>
            <span className={`status-chip ${repository ? "success" : "neutral"}`}>
              {repository ? "Loaded" : "Waiting"}
            </span>
          </div>

          <label className="upload-zone">
            <input
              accept=".zip"
              type="file"
              onChange={(event) => setRepository(event.target.files?.[0] || null)}
            />
            <span className="material-symbols-outlined">cloud_upload</span>
            <strong>{repository ? repository.name : "Choose repository ZIP"}</strong>
            <small>{repository ? `${Math.max(repository.size / 1024, 1).toFixed(0)} KB` : ".zip source archive"}</small>
          </label>

          <div className="field-group">
            <label htmlFor="analysis-title">Analysis Title</label>
            <input
              id="analysis-title"
              placeholder="Race condition in checkout workflow"
              type="text"
              value={analysisTitle}
              onChange={(event) => setAnalysisTitle(event.target.value)}
            />
          </div>

          <div className="field-group">
            <label htmlFor="bug-report">Diagnostic Context</label>
            <textarea
              id="bug-report"
              placeholder="Describe the failing behavior, endpoint, function, or user flow."
              rows="5"
              value={bugReport}
              onChange={(event) => setBugReport(event.target.value)}
            />
          </div>

          <div className="field-group">
            <label htmlFor="error-log">Raw Logs / Stack Trace</label>
            <textarea
              className="code-input"
              id="error-log"
              placeholder="Paste logs here."
              rows="7"
              value={errorLog}
              onChange={(event) => setErrorLog(event.target.value)}
            />
          </div>

          {error && (
            <div className="notice danger">
              <span className="material-symbols-outlined">error</span>
              {error}
            </div>
          )}

          <div className="form-actions">
            <button className="primary-button" disabled={loading} type="submit">
              <span className="material-symbols-outlined">{loading ? "progress_activity" : "play_arrow"}</span>
              {loading ? "Analyzing" : "Run Analysis"}
            </button>
          </div>
        </form>

        <div className="results-stack">
          <section className="panel">
            <div className="panel-header">
              <div>
                <h3>
                  <span className="material-symbols-outlined">analytics</span>
                  Agent Pipeline
                </h3>
                <p>{loading ? "Scanner, bug hunter, and diagnosis agents are active" : "Ready for next run"}</p>
              </div>
              <span className={`status-dot ${loading ? "pulse" : ""}`} />
            </div>

            <div className="step-list">
              <PipelineStep icon="travel_explore" label="Scan repository" active={loading} complete={Boolean(summary)} />
              <PipelineStep icon="target" label="Rank suspicious functions" active={loading} complete={suspects.length > 0} />
              <PipelineStep icon="psychology" label="Generate diagnosis" active={loading} complete={Boolean(diagnosis)} />
            </div>
          </section>

          <AgentReportsPanel reports={agentReports} />

          <DiagnosisPanel
            confidence={confidence}
            confidenceClass={confidenceClass}
            diagnosis={diagnosis}
          />
        </div>
      </section>

      <SuspectsPanel suspects={suspects} />
    </main>
  );
}

function HistoryView({ clearHistory, history, loadHistoryRun, setActiveView }) {
  return (
    <main className="content-canvas">
      <section className="page-heading">
        <div>
          <p className="eyebrow">Local Analysis Timeline</p>
          <h2>History</h2>
        </div>
        <div className="button-row">
          <button className="secondary-button" type="button" onClick={clearHistory} disabled={!history.length}>
            <span className="material-symbols-outlined">delete</span>
            Clear
          </button>
          <button className="primary-button" type="button" onClick={() => setActiveView("analysis")}>
            <span className="material-symbols-outlined">add</span>
            New Analysis
          </button>
        </div>
      </section>

      <section className="history-grid">
        <section className="panel history-panel">
          <div className="panel-header">
            <div>
              <h3>
                <span className="material-symbols-outlined">history</span>
                Saved Runs
              </h3>
              <p>{history.length ? `${history.length} local analyses` : "Nothing saved yet"}</p>
            </div>
          </div>
          <RunList emptyText="Run an analysis and it will be saved here." runs={history} onOpen={loadHistoryRun} />
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h3>
                <span className="material-symbols-outlined">info</span>
                History Scope
              </h3>
              <p>Stored in this browser</p>
            </div>
          </div>
          <div className="history-note">
            <p>
              History is saved in local browser storage for this frontend. It is useful for quick demos and repeat
              inspection, but it is not a shared server-side audit log yet.
            </p>
          </div>
        </section>
      </section>
    </main>
  );
}

function AgentReportsPanel({ reports }) {
  return (
    <section className="panel agent-trace-panel">
      <div className="panel-header">
        <div>
          <h3>
            <span className="material-symbols-outlined">account_tree</span>
            Agent Trace
          </h3>
          <p>{reports.length ? "Role, tools, and summary for each LangGraph agent" : "Agent reports appear after analysis"}</p>
        </div>
      </div>

      {reports.length ? (
        <div className="agent-report-list">
          {reports.map((report) => (
            <article className="agent-report" key={report.agent}>
              <div>
                <strong>{formatAgentName(report.agent)}</strong>
                <span>{report.role}</span>
              </div>
              <p>{report.summary}</p>
              <div className="tool-chip-row">
                {(report.tools || []).map((tool) => (
                  <span className="tool-chip" key={tool}>{tool}</span>
                ))}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state inline">
          <span className="material-symbols-outlined">account_tree</span>
          <p>Run an analysis to inspect the agent trace.</p>
        </div>
      )}
    </section>
  );
}

function DiagnosisPanel({ confidence, confidenceClass, diagnosis }) {
  return (
    <section className="panel diagnosis-panel">
      <div className="panel-header">
        <div>
          <h3>
            <span className="material-symbols-outlined">psychology</span>
            AI Diagnosis
          </h3>
          <p>{diagnosis ? "Model response" : "No diagnosis yet"}</p>
        </div>
        <span className={`status-chip ${confidenceClass}`}>{confidence}</span>
      </div>

      {diagnosis ? (
        <div className="diagnosis-content">
          <ResultBlock label="Root Cause" value={diagnosis.root_cause} />
          <ResultBlock label="Suggested Fix" value={diagnosis.suggested_fix} />
          {(diagnosis.target_file || diagnosis.target_function) && (
            <div className="result-meta">
              {diagnosis.target_file && <span>{diagnosis.target_file}</span>}
              {diagnosis.target_function && <strong>{diagnosis.target_function}</strong>}
            </div>
          )}
          {diagnosis.corrected_code && (
            <div className="code-review">
              <div className="code-review-header">
                <span className="material-symbols-outlined">edit_document</span>
                <span>Corrected Code</span>
              </div>
              <pre>{diagnosis.corrected_code}</pre>
            </div>
          )}
        </div>
      ) : (
        <div className="empty-state">
          <span className="material-symbols-outlined">terminal</span>
          <p>Results will appear here after analysis.</p>
        </div>
      )}
    </section>
  );
}

function SuspectsPanel({ suspects }) {
  return (
    <section className="panel suspects-panel">
      <div className="panel-header">
        <div>
          <h3>
            <span className="material-symbols-outlined">bug_report</span>
            Suspicious Functions
          </h3>
          <p>{suspects.length ? `${suspects.length} ranked suspects` : "No suspects ranked yet"}</p>
        </div>
      </div>

      {suspects.length ? (
        <div className="suspect-table">
          <div className="table-row table-head">
            <span>Function</span>
            <span>File</span>
            <span>Line</span>
            <span>Score</span>
          </div>
          {suspects.map((suspect, index) => (
            <div className="table-row" key={`${suspect.file}-${suspect.function}-${index}`}>
              <strong>{suspect.function}</strong>
              <code>{suspect.file}</code>
              <span>{suspect.line ?? "--"}</span>
              <span className="score-pill">{suspect.score}</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state inline">
          <span className="material-symbols-outlined">manage_search</span>
          <p>Run an analysis to populate suspect ranking.</p>
        </div>
      )}
    </section>
  );
}

function RunList({ emptyText, onOpen, runs }) {
  if (!runs.length) {
    return (
      <div className="empty-state inline">
        <span className="material-symbols-outlined">history</span>
        <p>{emptyText}</p>
      </div>
    );
  }

  return (
    <div className="run-list">
      {runs.map((run) => (
        <button className="run-row" key={run.id} type="button" onClick={() => onOpen(run)}>
          <span className="run-icon material-symbols-outlined">analytics</span>
          <span className="run-main">
            <strong>{run.title || run.repositoryName || "Untitled analysis"}</strong>
            <small>{run.repositoryName || "Unknown repository"}</small>
          </span>
          <span className="run-meta">
            <span className={`status-chip ${getConfidenceClass(run.diagnosis?.confidence)}`}>
              {run.diagnosis?.confidence || "Unknown"}
            </span>
            <small>{formatDate(run.createdAt)}</small>
          </span>
        </button>
      ))}
    </div>
  );
}

function MetricCard({ icon, label, value, tone }) {
  return (
    <article className={`metric-card ${tone}`}>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
      <span className="material-symbols-outlined">{icon}</span>
    </article>
  );
}

function MiniStat({ label, value }) {
  return (
    <div className="mini-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function PipelineStep({ icon, label, active, complete }) {
  return (
    <div className={`pipeline-step ${complete ? "complete" : ""} ${active ? "active" : ""}`}>
      <span className="material-symbols-outlined">{complete ? "check_circle" : icon}</span>
      <span>{label}</span>
    </div>
  );
}

function ResultBlock({ label, value }) {
  return (
    <div className="result-block">
      <span>{label}</span>
      <p>{value || "Not provided"}</p>
    </div>
  );
}

function getConfidenceClass(confidence = "") {
  const normalized = String(confidence).toLowerCase();

  if (normalized.includes("high")) return "success";
  if (normalized.includes("medium")) return "warning";
  if (normalized.includes("low")) return "danger";
  return "neutral";
}

function getViewTitle(activeView, hasResult) {
  if (activeView === "dashboard") return "Dashboard";
  if (activeView === "history") return "History";
  return hasResult ? "Analysis Ready" : "New Analysis";
}

function formatDate(value) {
  if (!value) return "Unknown time";

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatAgentName(value = "") {
  return value
    .split("_")
    .filter(Boolean)
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(" ");
}

function buildActivityData(history) {
  const recentRuns = history.slice(0, 12).reverse();
  const maxSuspects = Math.max(...recentRuns.map((run) => run.suspects?.length || 0), 1);

  return recentRuns.map((run, index) => {
    const suspects = run.suspects?.length || 0;
    const date = run.createdAt ? new Date(run.createdAt) : null;
    const shortLabel = date
      ? new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(date)
      : `Run ${index + 1}`;
    const label = run.title || run.repositoryName || shortLabel;

    return {
      id: run.id || `${run.createdAt}-${index}`,
      height: Math.max((suspects / maxSuspects) * 100, suspects ? 12 : 4),
      label,
      shortLabel,
      suspects,
    };
  });
}

function loadSavedHistory() {
  try {
    const savedHistory = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    return Array.isArray(savedHistory) ? savedHistory : [];
  } catch {
    return [];
  }
}

export default Home;
