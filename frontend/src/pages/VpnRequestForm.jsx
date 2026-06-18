import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/axios";
import { ShieldCheck, CheckCircle2, XCircle } from "lucide-react";

export default function VpnRequestForm() {
  const [adUsername, setAdUsername] = useState("");
  const [adPassword, setAdPassword] = useState("");
  const [status, setStatus] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    document.title = "Request VPN Access — Sentinel VAC";
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus(null);
    setMessage("");
    setLoading(true);
    try {
      const { data } = await api.post("/vpn/request", {
        ad_username: adUsername,
        ad_password: adPassword,
      });
      setStatus("success");
      setMessage(
        `Request submitted for ${data.display_name}. An administrator will review your request.`
      );
      setAdUsername("");
      setAdPassword("");
    } catch (err) {
      setStatus("error");
      setMessage(
        err.response?.data?.detail ||
          "Could not submit your request. Check your credentials and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-chrome-900 px-4">
      <div className="w-full max-w-md">
        <div className="mb-6 flex flex-col items-center">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-md bg-chrome-600 text-white">
            <ShieldCheck size={26} />
          </div>
          <div className="text-lg font-bold text-white">Sentinel VAC</div>
          <div className="text-xs text-ink-400">VPN Access Request — hightech.local</div>
        </div>

        <div className="card">
          <div className="card-body">
            <h1 className="mb-1 text-sm font-semibold text-ink-900">
              Request VPN Access
            </h1>
            <p className="mb-4 text-xs text-ink-500">
              Sign in with your Active Directory credentials to submit a VPN access
              request. Your password is used only to verify your identity and is
              never stored.
            </p>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div>
                <label className="field-label">AD Username</label>
                <input
                  className="input"
                  type="text"
                  placeholder="jdoe@hightech.local"
                  value={adUsername}
                  onChange={(e) => setAdUsername(e.target.value)}
                  required
                  autoFocus
                />
              </div>
              <div>
                <label className="field-label">AD Password</label>
                <input
                  className="input"
                  type="password"
                  value={adPassword}
                  onChange={(e) => setAdPassword(e.target.value)}
                  required
                />
              </div>

              {status === "success" && (
                <div className="flex items-start gap-2 rounded border border-ok/30 bg-ok/5 px-3 py-2 text-xs text-ok">
                  <CheckCircle2 size={16} className="mt-0.5 shrink-0" />
                  <span>{message}</span>
                </div>
              )}
              {status === "error" && (
                <div className="flex items-start gap-2 rounded border border-sev-critical/30 bg-sev-critical/5 px-3 py-2 text-xs text-sev-critical">
                  <XCircle size={16} className="mt-0.5 shrink-0" />
                  <span>{message}</span>
                </div>
              )}

              <button type="submit" className="btn-primary w-full py-2" disabled={loading}>
                {loading ? "Submitting…" : "Submit Request"}
              </button>
            </form>
          </div>
        </div>

        <p className="mt-4 text-center text-[11px] text-ink-400">
          Administrator or analyst?{" "}
          <Link to="/login" className="text-accent hover:underline">
            Sign in to the console
          </Link>
        </p>
      </div>
    </div>
  );
}
