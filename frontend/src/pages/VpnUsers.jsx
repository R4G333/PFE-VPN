import { useCallback, useEffect, useState } from "react";
import api from "../api/axios";
import { useAuth } from "../context/AuthContext";
import { RefreshCw, UserMinus, Search } from "lucide-react";

export default function VpnUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [revokeTarget, setRevokeTarget] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const { hasRole } = useAuth();

  const isAdmin = hasRole("ADMIN");

  useEffect(() => {
    document.title = "VPN Users — Sentinel VAC";
  }, []);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/vpn-users");
      setUsers(data);
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load VPN users");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleRevoke = async (samAccount) => {
    setActionLoading(true);
    try {
      await api.delete(`/vpn-users/${samAccount}`);
      setRevokeTarget(null);
      await fetchUsers();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to revoke access");
    } finally {
      setActionLoading(false);
    }
  };

  const filtered = users.filter(
    (u) =>
      u.sam_account.toLowerCase().includes(search.toLowerCase()) ||
      u.display_name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">VPN Users</h1>
          <p className="page-subtitle">
            Members of the VPN_Users Active Directory group. Revoking access
            removes the user from this group immediately.
          </p>
        </div>
        <button className="btn-ghost" onClick={fetchUsers}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">VPN_Users ({filtered.length})</span>
          <div className="relative w-56">
            <Search
              size={14}
              className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-400"
            />
            <input
              className="input pl-8"
              placeholder="Search users…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
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
                <th>sAMAccountName</th>
                <th>Display Name</th>
                {isAdmin && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={3} className="text-center text-ink-400 py-6">
                    Loading…
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={3} className="text-center text-ink-400 py-6">
                    No VPN users found
                  </td>
                </tr>
              ) : (
                filtered.map((u) => (
                  <tr key={u.sam_account}>
                    <td className="mono">{u.sam_account}</td>
                    <td>{u.display_name}</td>
                    {isAdmin && (
                      <td>
                        {revokeTarget === u.sam_account ? (
                          <div className="flex items-center gap-1.5">
                            <span className="text-xs text-ink-600">
                              Revoke access for {u.sam_account}?
                            </span>
                            <button
                              className="btn-danger"
                              disabled={actionLoading}
                              onClick={() => handleRevoke(u.sam_account)}
                            >
                              Confirm
                            </button>
                            <button
                              className="btn-ghost"
                              disabled={actionLoading}
                              onClick={() => setRevokeTarget(null)}
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <button
                            className="btn-danger"
                            onClick={() => setRevokeTarget(u.sam_account)}
                          >
                            <UserMinus size={13} /> Revoke Access
                          </button>
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
