import { useCallback, useEffect, useState } from "react";
import api from "../api/axios";
import { useAuth } from "../context/AuthContext";
import { StatusPill } from "../components/StatusBadge";
import { Check, X, RefreshCw } from "lucide-react";

function formatDateTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function RequestsList() {
  const [requests, setRequests] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionId, setActionId] = useState(null);
  const [rejectId, setRejectId] = useState(null);
  const [rejectReason, setRejectReason] = useState("");
  const { hasRole } = useAuth();

  const isAdmin = hasRole("ADMIN");

  useEffect(() => {
    document.title = "VPN Requests — Sentinel VAC";
  }, []);

  const fetchRequests = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (statusFilter) params.status_filter = statusFilter;
      const { data } = await api.get("/requests", { params });
      setRequests(data.items);
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load requests");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  const handleApprove = async (id) => {
    setActionId(id);
    try {
      await api.post(`/requests/${id}/approve`);
      await fetchRequests();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to approve request");
    } finally {
      setActionId(null);
    }
  };

  const handleReject = async (id) => {
    if (!rejectReason.trim()) return;
    setActionId(id);
    try {
      await api.post(`/requests/${id}/reject`, { rejection_reason: rejectReason });
      setRejectId(null);
      setRejectReason("");
      await fetchRequests();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to reject request");
    } finally {
      setActionId(null);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">VPN Access Requests</h1>
          <p className="page-subtitle">
            {isAdmin
              ? "Review and approve or reject VPN access requests from Active Directory users."
              : "Read-only view of VPN access requests."}
          </p>
        </div>
        <button className="btn-ghost" onClick={fetchRequests}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Requests</span>
          <select
            className="input w-44"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All statuses</option>
            <option value="PENDING">Pending</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
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
                <th>AD Username</th>
                <th>Display Name</th>
                <th>Submitted</th>
                <th>Reviewed By</th>
                <th>Reviewed At</th>
                <th>Notes</th>
                {isAdmin && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={8} className="text-center text-ink-400 py-6">
                    Loading…
                  </td>
                </tr>
              ) : requests.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center text-ink-400 py-6">
                    No requests found
                  </td>
                </tr>
              ) : (
                requests.map((r) => {
                  const sevClass =
                    r.status === "PENDING"
                      ? "sev-bar-medium"
                      : r.status === "APPROVED"
                      ? "sev-bar-ok"
                      : "sev-bar-critical";
                  return (
                    <tr key={r.id} className={sevClass}>
                      <td>
                        <StatusPill status={r.status} />
                      </td>
                      <td className="mono">{r.ad_username}</td>
                      <td>{r.display_name}</td>
                      <td className="mono">{formatDateTime(r.created_at)}</td>
                      <td className="mono">{r.reviewed_by || "—"}</td>
                      <td className="mono">{formatDateTime(r.reviewed_at)}</td>
                      <td className="text-ink-500">{r.rejection_reason || "—"}</td>
                      {isAdmin && (
                        <td>
                          {r.status === "PENDING" ? (
                            rejectId === r.id ? (
                              <div className="flex items-center gap-1.5">
                                <input
                                  className="input w-40 py-1"
                                  placeholder="Rejection reason"
                                  value={rejectReason}
                                  onChange={(e) => setRejectReason(e.target.value)}
                                  autoFocus
                                />
                                <button
                                  className="btn-danger"
                                  disabled={actionId === r.id || !rejectReason.trim()}
                                  onClick={() => handleReject(r.id)}
                                >
                                  Confirm
                                </button>
                                <button
                                  className="btn-ghost"
                                  onClick={() => {
                                    setRejectId(null);
                                    setRejectReason("");
                                  }}
                                >
                                  Cancel
                                </button>
                              </div>
                            ) : (
                              <div className="flex items-center gap-1.5">
                                <button
                                  className="btn-success"
                                  disabled={actionId === r.id}
                                  onClick={() => handleApprove(r.id)}
                                >
                                  <Check size={13} /> Approve
                                </button>
                                <button
                                  className="btn-danger"
                                  disabled={actionId === r.id}
                                  onClick={() => setRejectId(r.id)}
                                >
                                  <X size={13} /> Reject
                                </button>
                              </div>
                            )
                          ) : (
                            <span className="text-ink-400">—</span>
                          )}
                        </td>
                      )}
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
