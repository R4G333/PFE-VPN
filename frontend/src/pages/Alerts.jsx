import { useCallback, useEffect, useState } from "react";
import api from "../api/axios";
import { useAuth } from "../context/AuthContext";
import { StatusPill, AlertTypePill } from "../components/StatusBadge";
import { RefreshCw, ShieldCheck, Ban } from "lucide-react";

function formatDateTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [statusFilter, setStatusFilter] = useState("OPEN");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionId, setActionId] = useState(null);
  const [blockTarget, setBlockTarget] = useState(null);
  const [blockReason, setBlockReason] = useState("");
  const { hasRole } = useAuth();

  const canAct = hasRole("ADMIN", "SECURITY_ANALYST");

  useEffect(() => {
    document.title = "Alerts — Sentinel VAC";
  }, []);

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (statusFilter) params.status_filter = statusFilter;
      const { data } = await api.get("/alerts", { params });
      setAlerts(data.items);
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load alerts");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 15000);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  const handleAcknowledge = async (id) => {
    setActionId(id);
    try {
      await api.post(`/alerts/${id}/acknowledge`);
      await fetchAlerts();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to acknowledge alert");
    } finally {
      setActionId(null);
    }
  };

  const handleResolve = async (id) => {
    setActionId(id);
    try {
      await api.post(`/alerts/${id}/resolve`, {});
      await fetchAlerts();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to resolve alert");
    } finally {
      setActionId(null);
    }
  };

  const handleBlock = async (alert) => {
    setActionId(alert.id);
    try {
      await api.post("/blocked-devices", {
        ip_address: alert.source_ip,
        reason: blockReason || `${alert.alert_type} alert (${alert.id})`,
        alert_id: alert.id,
      });
      setBlockTarget(null);
      setBlockReason("");
      await fetchAlerts();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to block device");
    } finally {
      setActionId(null);
    }
  };

  const sevClassFor = (type) =>
    type === "BRUTE_FORCE" ? "sev-bar-critical" : "sev-bar-high";

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Security Alerts</h1>
          <p className="page-subtitle">
            Brute force and password spraying detections from authentication logs.
          </p>
        </div>
        <button className="btn-ghost" onClick={fetchAlerts}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Alerts</span>
          <select
            className="input w-44"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All statuses</option>
            <option value="OPEN">Open</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="RESOLVED">Resolved</option>
          </select>
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
                <th>Type</th>
                <th>Status</th>
                <th>Source IP</th>
                <th>Target User</th>
                <th>Occurrences</th>
                <th>Window Start</th>
                <th>Window End</th>
                <th>Detected At</th>
                <th>Resolved By</th>
                {canAct && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={10} className="text-center text-ink-400 py-6">
                    Loading…
                  </td>
                </tr>
              ) : alerts.length === 0 ? (
                <tr>
                  <td colSpan={10} className="text-center text-ink-400 py-6">
                    No alerts found
                  </td>
                </tr>
              ) : (
                alerts.map((a) => (
                  <tr key={a.id} className={sevClassFor(a.alert_type)}>
                    <td>
                      <AlertTypePill type={a.alert_type} />
                    </td>
                    <td>
                      <StatusPill status={a.status} />
                    </td>
                    <td className="mono">{a.source_ip}</td>
                    <td className="mono">{a.target_username || "—"}</td>
                    <td className="mono">{a.occurrence_count}</td>
                    <td className="mono">{formatDateTime(a.window_start)}</td>
                    <td className="mono">{formatDateTime(a.window_end)}</td>
                    <td className="mono">{formatDateTime(a.detected_at)}</td>
                    <td className="mono">{a.resolved_by || "—"}</td>
                    {canAct && (
                      <td>
                        {a.status === "RESOLVED" ? (
                          <span className="text-ink-400">—</span>
                        ) : blockTarget === a.id ? (
                          <div className="flex items-center gap-1.5">
                            <input
                              className="input w-40 py-1"
                              placeholder="Block reason (optional)"
                              value={blockReason}
                              onChange={(e) => setBlockReason(e.target.value)}
                              autoFocus
                            />
                            <button
                              className="btn-danger"
                              disabled={actionId === a.id}
                              onClick={() => handleBlock(a)}
                            >
                              Confirm
                            </button>
                            <button
                              className="btn-ghost"
                              onClick={() => {
                                setBlockTarget(null);
                                setBlockReason("");
                              }}
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1.5">
                            {a.status === "OPEN" && (
                              <button
                                className="btn-ghost"
                                disabled={actionId === a.id}
                                onClick={() => handleAcknowledge(a.id)}
                              >
                                Acknowledge
                              </button>
                            )}
                            <button
                              className="btn-success"
                              disabled={actionId === a.id}
                              onClick={() => handleResolve(a.id)}
                            >
                              <ShieldCheck size={13} /> Resolve
                            </button>
                            <button
                              className="btn-danger"
                              disabled={actionId === a.id}
                              onClick={() => setBlockTarget(a.id)}
                            >
                              <Ban size={13} /> Block IP
                            </button>
                          </div>
                        )}
                      </td>
                    )}
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
