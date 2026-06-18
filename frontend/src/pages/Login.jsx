import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ShieldCheck } from "lucide-react";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { user, loading, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    document.title = "Sign In — Sentinel VAC";
  }, []);

  useEffect(() => {
    if (!loading && user) {
      navigate("/dashboard", { replace: true });
    }
  }, [user, loading, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(username, password);
      const dest = location.state?.from?.pathname || "/dashboard";
      navigate(dest, { replace: true });
    } catch (err) {
      setError(
        err.response?.data?.detail || "Login failed. Check your credentials."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-chrome-900 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-md bg-chrome-600 text-white">
            <ShieldCheck size={26} />
          </div>
          <div className="text-lg font-bold text-white">Sentinel VAC</div>
          <div className="text-xs text-ink-400">VPN Access Console — hightech.local</div>
        </div>

        <div className="card">
          <div className="card-body">
            <h1 className="mb-4 text-sm font-semibold text-ink-900">
              Sign in to your account
            </h1>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div>
                <label className="field-label">Username</label>
                <input
                  className="input"
                  type="text"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  autoFocus
                />
              </div>
              <div>
                <label className="field-label">Password</label>
                <input
                  className="input"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              {error && (
                <div className="rounded border border-sev-critical/30 bg-sev-critical/5 px-3 py-2 text-xs text-sev-critical">
                  {error}
                </div>
              )}

              <button type="submit" className="btn-primary w-full py-2" disabled={submitting || loading}>
                {submitting ? "Signing in…" : "Sign in"}
              </button>
            </form>
          </div>
        </div>

        <p className="mt-4 text-center text-[11px] text-ink-400">
          Internal use only. All access is logged and audited.
        </p>
      </div>
    </div>
  );
}
