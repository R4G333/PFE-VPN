import { useCallback, useEffect, useState } from "react";
import api from "../api/axios";
import { useAuth } from "../context/AuthContext";
import { ActiveBadge, StatusPill } from "../components/StatusBadge";
import { RefreshCw, Plus, Unlock } from "lucide-react";

function formatDateTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function BlockedDevices() {
  const [devices, setDevices] = useState([]);
  const [activeFilter, setActiveFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionId, setActionId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [newIp, setNewIp] = useState("");
  const [newReason, setNewReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { hasRole } = useAuth();

  const canAct = hasRole("ADMIN", "SECURITY_ANALYST");

  useEffect(() => {
    document.title = "Blocked Devices — Sentinel VAC";
  }, []);

  const fetchDevices = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (activeFilter !== "") params.is_active = activeFilter;
      const { data } = await api.get("/blocked-devices", { params });
      setDevices(data.items);
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load blocked devices");
    } finally {
      setLoading(false);
    }
  }, [activeFilter]);

  useEffect(() => {
    fetchDevices();
    const interval = setInterval(fetchDevices, 15000);
    return () => clearInterval(interval);
  }, [fetchDevices]);

  const handleUnblock = async (id) => {
    setActionId(id);
    try {
      await api.post(`/blocked-devices/${id}/unblock`);
      await fetchDevices();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to unblock device");
    } finally {
      setActionId(null);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post("/blocked-devices", {
        ip_address: newIp,
        reason: newReason,
      });
      setNewIp("");
      setNewReason("");
      setShowForm(false);
      await fetchDevices();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to block device");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Blocked Devices</h1>
          <p className="page-subtitle">
            IP addresses blocked at the firewall (UFW). Enforcement is applied by
            a background process and may take a few seconds to take effect.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {canAct && (
            <button className="btn-primary" onClick={() => setShowForm((v) => !v)}>
              <Plus size={13} /> Block IP
            </button>
          )}
          <button className="btn-ghost" onClick={fetchDevices}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {showForm && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Block a new IP address</span>
          </div>
          <div className="card-body">
            <form onSubmit={handleCreate} className="flex items-end gap-3">
              <div className="flex-1">
                <label className="field-label">IP Address</label>
                <input
                  className="input"
                  placeholder="192.168.182.131"
                  value={newIp}
                  onChange={(e) => setNewIp(e.target.value)}
                  required
                  autoFocus
                />
              </div>
              <div className="flex-1">
                <label className="field-label">Reason</label>
                <input
                  className="input"
                  placeholder="Manual block — suspicious activity"
                  value={newReason}
                  onChange={(e) => setNewReason(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="btn-primary" disabled={submitting}>
                {submitting ? "Blocking…" : "Block"}
              </button>
              <button
                type="button"
                className="btn-ghost"
                onClick={() => setShowForm(false)}
              >
                Cancel
              </button>
            </form>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <span className="card-title">Devices</span>
          <select
            className="input w-44"
            value={activeFilter}
            onChange={(e) => setActiveFilter(e.target.value)}
          >
            <option value="">All</option>
            <option value="true">Active blocks</option>
            <option value="false">Unblocked / history</option>
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
                <th>Status</th>
                <th>IP Address</th>
                <th>Reason</th>
                <th>Blocked By</th>
                <th>Blocked At</th>
                <th>Enforcement</th>
                <th>Unblocked By</th>
                <th>Unblocked At</th>
                {canAct && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={9} className="text-center text-ink-400 py-6">
                    Loading…
                  </td>
                </tr>
              ) : devices.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center text-ink-400 py-6">
                    No blocked devices found
                  </td>
                </tr>
              ) : (
                devices.map((d) => (
                  <tr
                    key={d.id}
                    className={d.is_active ? "sev-bar-critical" : "sev-bar-info"}
                  >
                    <td>
                      <ActiveBadge isActive={d.is_active} />
                    </td>
                    <td className="mono">{d.ip_address}</td>
                    <td className="text-ink-600">{d.reason}</td>
                    <td className="mono">{d.blocked_by}</td>
                    <td className="mono">{formatDateTime(d.blocked_at)}</td>
                    <td>
                      <StatusPill status={d.enforcement_status} />
                      {d.enforcement_status === "FAILED" && d.enforcement_error && (
                        <div className="mt-1 text-[10px] text-sev-critical">
                          {d.enforcement_error}
                        </div>
                      )}
                    </td>
                    <td className="mono">{d.unblocked_by || "—"}</td>
                    <td className="mono">{formatDateTime(d.unblocked_at)}</td>
                    {canAct && (
                      <td>
                        {d.is_active ? (
                          <button
                            className="btn-success"
                            disabled={actionId === d.id}
                            onClick={() => handleUnblock(d.id)}
                          >
                            <Unlock size={13} /> Unblock
                          </button>
                        ) : (
                          <span className="text-ink-400">—</span>
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
