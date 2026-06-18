import { useCallback, useEffect, useState } from "react";
import api from "../api/axios";
import { RolePill } from "../components/StatusBadge";
import { RefreshCw, Plus, UserCheck, UserX } from "lucide-react";

function formatDateTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "2-digit",
    year: "numeric",
  });
}

const ROLES = ["ADMIN", "SECURITY_ANALYST", "AUDITOR"];

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionId, setActionId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    username: "",
    email: "",
    full_name: "",
    password: "",
    role: "AUDITOR",
  });

  useEffect(() => {
    document.title = "User Management — Sentinel VAC";
  }, []);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/users");
      setUsers(data);
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load users");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await api.post("/users", form);
      setForm({ username: "", email: "", full_name: "", password: "", role: "AUDITOR" });
      setShowForm(false);
      await fetchUsers();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create user");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRoleChange = async (userId, role) => {
    setActionId(userId);
    try {
      await api.put(`/users/${userId}/role`, { role });
      await fetchUsers();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update role");
    } finally {
      setActionId(null);
    }
  };

  const handleToggleActive = async (user) => {
    setActionId(user.id);
    try {
      const endpoint = user.is_active ? "deactivate" : "activate";
      await api.patch(`/users/${user.id}/${endpoint}`);
      await fetchUsers();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update user status");
    } finally {
      setActionId(null);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Application Users</h1>
          <p className="page-subtitle">
            Manage console accounts and RBAC roles for administrators, analysts, and
            auditors.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-primary" onClick={() => setShowForm((v) => !v)}>
            <Plus size={13} /> New User
          </button>
          <button className="btn-ghost" onClick={fetchUsers}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {showForm && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Create application user</span>
          </div>
          <div className="card-body">
            <form onSubmit={handleCreate} className="grid grid-cols-1 gap-3 md:grid-cols-5">
              <div>
                <label className="field-label">Username</label>
                <input
                  className="input"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="field-label">Email</label>
                <input
                  className="input"
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="field-label">Full Name</label>
                <input
                  className="input"
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="field-label">Password</label>
                <input
                  className="input"
                  type="password"
                  minLength={8}
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="field-label">Role</label>
                <select
                  className="input"
                  value={form.role}
                  onChange={(e) => setForm({ ...form, role: e.target.value })}
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>
              <div className="md:col-span-5 flex items-center gap-2">
                <button type="submit" className="btn-primary" disabled={submitting}>
                  {submitting ? "Creating…" : "Create User"}
                </button>
                <button type="button" className="btn-ghost" onClick={() => setShowForm(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <span className="card-title">Users ({users.length})</span>
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
                <th>Username</th>
                <th>Full Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center text-ink-400 py-6">
                    Loading…
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center text-ink-400 py-6">
                    No users found
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id}>
                    <td className="mono">{u.username}</td>
                    <td>{u.full_name}</td>
                    <td className="mono">{u.email}</td>
                    <td>
                      <select
                        className="input w-44 py-1"
                        value={u.role}
                        disabled={actionId === u.id}
                        onChange={(e) => handleRoleChange(u.id, e.target.value)}
                      >
                        {ROLES.map((r) => (
                          <option key={r} value={r}>
                            {r}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      {u.is_active ? (
                        <span className="sev-pill-ok">Active</span>
                      ) : (
                        <span className="sev-pill-info">Disabled</span>
                      )}
                    </td>
                    <td className="mono">{formatDateTime(u.created_at)}</td>
                    <td>
                      <button
                        className={u.is_active ? "btn-danger" : "btn-success"}
                        disabled={actionId === u.id}
                        onClick={() => handleToggleActive(u)}
                      >
                        {u.is_active ? (
                          <>
                            <UserX size={13} /> Deactivate
                          </>
                        ) : (
                          <>
                            <UserCheck size={13} /> Activate
                          </>
                        )}
                      </button>
                    </td>
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
