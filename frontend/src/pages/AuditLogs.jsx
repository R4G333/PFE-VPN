import { useEffect, useState } from "react";
import api from "../api/axios";
import { RefreshCw, Search } from "lucide-react";

function formatDateTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

const ACTION_SEVERITY = {
  REQUEST_AUTH_FAILED: "sev-bar-high",
  REQUEST_REJECTED: "sev-bar-high",
  ACCESS_REVOKED: "sev-bar-critical",
  DEVICE_BLOCKED: "sev-bar-critical",
  ALERT_RESOLVED: "sev-bar-ok",
  REQUEST_APPROVED: "sev-bar-ok",
  DEVICE_UNBLOCKED: "sev-bar-ok",
  REQUEST_CREATED: "sev-bar-low",
};

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [actor, setActor] = useState("");
  const [action, setAction] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    document.title = "Audit Logs — Sentinel VAC";
  }, []);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = {};
      if (actor) params.actor = actor;
      if (action) params.action = action;
      const { data } = await api.get("/logs", { params });
      setLogs(data.items);
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchLogs();
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Audit Logs</h1>
          <p className="page-subtitle">
            Immutable record of all security-sensitive actions across the platform.
          </p>
        </div>
        <button className="btn-ghost" onClick={fetchLogs}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Logs ({logs.length})</span>
          <form onSubmit={handleSearch} className="flex items-center gap-2">
            <input
              className="input w-44"
              placeholder="Filter by actor"
              value={actor}
              onChange={(e) => setActor(e.target.value)}
            />
            <input
              className="input w-44"
              placeholder="Filter by action"
              value={action}
              onChange={(e) => setAction(e.target.value)}
            />
            <button type="submit" className="btn-ghost">
              <Search size={13} /> Search
            </button>
          </form>
        </div>

        {error && (
          <div className="border-b border-sev-critical/30 bg-sev-critical/5 px-4 py-2 text-xs text-sev-critical">
            {error}
          </div>
        )}

        <div className="table-wrap overflow-x-auto">
          <table className="grid-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Target</th>
                <th>Detail</th>
                <th>IP Address</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center text-ink-400 py-6">
                    Loading…
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center text-ink-400 py-6">
                    No audit log entries found
                  </td>
                </tr>
              ) : (
                logs.map((l) => (
                  <tr key={l.id} className={ACTION_SEVERITY[l.action] || "sev-bar-info"}>
                    <td className="mono">{formatDateTime(l.created_at)}</td>
                    <td className="mono">{l.actor}</td>
                    <td className="mono font-semibold">{l.action}</td>
                    <td className="mono">{l.target}</td>
                    <td className="text-ink-500">{l.detail || "—"}</td>
                    <td className="mono">{l.ip_address || "—"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
