import { useCallback, useEffect, useState } from "react";
import api from "../api/axios";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Users,
  Wifi,
  ArrowDownToLine,
  ArrowUpFromLine,
  ShieldAlert,
  Ban,
  AlertTriangle,
} from "lucide-react";

function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let i = 0;
  let val = bytes;
  while (val >= 1024 && i < units.length - 1) {
    val /= 1024;
    i++;
  }
  return `${val.toFixed(val < 10 && i > 0 ? 1 : 0)} ${units[i]}`;
}

function formatDateTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function KpiTile({ icon: Icon, label, value, sub, accent }) {
  return (
    <div className="kpi-tile">
      <div className="flex items-center justify-between">
        <span className="kpi-label">{label}</span>
        <Icon size={16} className={accent || "text-ink-400"} />
      </div>
      <div className="kpi-value">{value}</div>
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    document.title = "Dashboard — Sentinel VAC";
  }, []);

  const fetchData = useCallback(async () => {
    try {
      const { data } = await api.get("/monitoring/overview");
      setData(data);
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load monitoring data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex flex-col gap-5">
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-7">
          {Array.from({ length: 7 }).map((_, i) => (
            <div key={i} className="kpi-tile animate-pulse">
              <div className="h-3 w-16 rounded bg-ink-100" />
              <div className="mt-2 h-7 w-20 rounded bg-ink-100" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded border border-sev-critical/30 bg-sev-critical/5 px-4 py-3 text-sm text-sev-critical">
        {error}
      </div>
    );
  }

  const chartData = (data.traffic_timeseries || []).map((p) => ({
    time: new Date(p.recorded_at).toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
    }),
    received: p.bytes_received,
    sent: p.bytes_sent,
  }));

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="page-title">VPN Monitoring Dashboard</h1>
        <p className="page-subtitle">
          Live overview of VPN access, sessions, and security posture for hightech.local
        </p>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-7">
        <KpiTile
          icon={Users}
          label="Authorized Users"
          value={data.total_vpn_authorized_users}
          sub="VPN_Users (AD group)"
          accent="text-sev-low"
        />
        <KpiTile
          icon={Wifi}
          label="Connected Now"
          value={data.currently_connected}
          sub="Active sessions"
          accent="text-ok"
        />
        <KpiTile
          icon={ArrowDownToLine}
          label="Received (24h)"
          value={formatBytes(data.total_bytes_received_24h)}
          accent="text-sev-low"
        />
        <KpiTile
          icon={ArrowUpFromLine}
          label="Sent (24h)"
          value={formatBytes(data.total_bytes_sent_24h)}
          accent="text-sev-low"
        />
        <KpiTile
          icon={AlertTriangle}
          label="Failed Auth (24h)"
          value={data.failed_auth_attempts_24h}
          accent={data.failed_auth_attempts_24h > 0 ? "text-sev-high" : "text-ink-400"}
        />
        <KpiTile
          icon={ShieldAlert}
          label="Open Alerts"
          value={data.open_alerts_count}
          accent={data.open_alerts_count > 0 ? "text-sev-critical" : "text-ink-400"}
        />
        <KpiTile
          icon={Ban}
          label="Blocked IPs"
          value={data.active_blocked_ips_count}
          accent={data.active_blocked_ips_count > 0 ? "text-sev-medium" : "text-ink-400"}
        />
      </div>

      {/* Connections + traffic chart */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="card lg:col-span-2">
          <div className="card-header">
            <span className="card-title">Traffic — Last 24 Hours</span>
            <span className="text-[11px] text-ink-500">Aggregated bytes per snapshot</span>
          </div>
          <div className="card-body h-64">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="recv" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2D7DD2" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#2D7DD2" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="sent" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#1F9D55" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#1F9D55" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#DEE3E8" />
                  <XAxis dataKey="time" tick={{ fontSize: 11, fill: "#7C8AA0" }} />
                  <YAxis
                    tick={{ fontSize: 11, fill: "#7C8AA0" }}
                    tickFormatter={(v) => formatBytes(v)}
                    width={70}
                  />
                  <Tooltip
                    formatter={(value) => formatBytes(value)}
                    contentStyle={{ fontSize: 12, borderRadius: 4 }}
                  />
                  <Area
                    type="monotone"
                    dataKey="received"
                    name="Received"
                    stroke="#2D7DD2"
                    fill="url(#recv)"
                    strokeWidth={2}
                  />
                  <Area
                    type="monotone"
                    dataKey="sent"
                    name="Sent"
                    stroke="#1F9D55"
                    fill="url(#sent)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-xs text-ink-400">
                No traffic data yet. Run the collector scripts to populate this chart.
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Connection Activity</span>
          </div>
          <div className="card-body flex flex-col gap-3">
            <div className="flex items-center justify-between rounded border border-border px-3 py-2">
              <span className="text-xs text-ink-600">Connections today</span>
              <span className="font-mono text-sm font-bold text-ink-900">
                {data.connections_today}
              </span>
            </div>
            <div className="flex items-center justify-between rounded border border-border px-3 py-2">
              <span className="text-xs text-ink-600">Connections this week</span>
              <span className="font-mono text-sm font-bold text-ink-900">
                {data.connections_this_week}
              </span>
            </div>
            <div className="flex items-center justify-between rounded border border-border px-3 py-2">
              <span className="text-xs text-ink-600">Active sessions</span>
              <span className="font-mono text-sm font-bold text-ok">
                {data.currently_connected}
              </span>
            </div>
            <div className="flex items-center justify-between rounded border border-border px-3 py-2">
              <span className="text-xs text-ink-600">Open security alerts</span>
              <span
                className={`font-mono text-sm font-bold ${
                  data.open_alerts_count > 0 ? "text-sev-critical" : "text-ink-900"
                }`}
              >
                {data.open_alerts_count}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Active sessions */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Active VPN Sessions</span>
          <span className="text-[11px] text-ink-500">
            {data.active_sessions.length} connected
          </span>
        </div>
        <div className="table-wrap overflow-x-auto">
          <table className="grid-table">
            <thead>
              <tr>
                <th>Status</th>
                <th>Common Name</th>
                <th>Real Address</th>
                <th>Virtual Address</th>
                <th>Connected Since</th>
                <th>Received</th>
                <th>Sent</th>
              </tr>
            </thead>
            <tbody>
              {data.active_sessions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center text-ink-400 py-6">
                    No active sessions
                  </td>
                </tr>
              ) : (
                data.active_sessions.map((s, i) => (
                  <tr key={i} className="sev-bar-ok">
                    <td>
                      <span className="sev-pill-ok">
                        <span className="live-dot" /> Active
                      </span>
                    </td>
                    <td className="mono">{s.common_name}</td>
                    <td className="mono">{s.real_address}</td>
                    <td className="mono">{s.virtual_address || "—"}</td>
                    <td className="mono">{formatDateTime(s.connected_since)}</td>
                    <td className="mono">{formatBytes(s.bytes_received)}</td>
                    <td className="mono">{formatBytes(s.bytes_sent)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent disconnects */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Recent Disconnects</span>
        </div>
        <div className="table-wrap overflow-x-auto">
          <table className="grid-table">
            <thead>
              <tr>
                <th>Common Name</th>
                <th>Real Address</th>
                <th>Disconnected At</th>
                <th>Received</th>
                <th>Sent</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_disconnects.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center text-ink-400 py-6">
                    No recent disconnects
                  </td>
                </tr>
              ) : (
                data.recent_disconnects.map((s, i) => (
                  <tr key={i} className="sev-bar-info">
                    <td className="mono">{s.common_name}</td>
                    <td className="mono">{s.real_address}</td>
                    <td className="mono">{formatDateTime(s.disconnected_at)}</td>
                    <td className="mono">{formatBytes(s.bytes_received)}</td>
                    <td className="mono">{formatBytes(s.bytes_sent)}</td>
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
