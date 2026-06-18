// Maps backend enum values to severity-pill visual classes.

export function StatusPill({ status }) {
  const map = {
    PENDING: { cls: "sev-pill-medium", label: "Pending" },
    APPROVED: { cls: "sev-pill-ok", label: "Approved" },
    REJECTED: { cls: "sev-pill-critical", label: "Rejected" },

    OPEN: { cls: "sev-pill-critical", label: "Open" },
    ACKNOWLEDGED: { cls: "sev-pill-medium", label: "Acknowledged" },
    RESOLVED: { cls: "sev-pill-ok", label: "Resolved" },

    ACTIVE: { cls: "sev-pill-ok", label: "Active" },
    DISCONNECTED: { cls: "sev-pill-info", label: "Disconnected" },

    PENDING_ENFORCE: { cls: "sev-pill-medium", label: "Pending" },
    APPLIED: { cls: "sev-pill-ok", label: "Applied" },
    FAILED: { cls: "sev-pill-critical", label: "Failed" },
  };

  const entry = map[status] || { cls: "sev-pill-info", label: status };
  return <span className={entry.cls}>{entry.label}</span>;
}

export function AlertTypePill({ type }) {
  const map = {
    BRUTE_FORCE: { cls: "sev-pill-critical", label: "Brute Force" },
    PASSWORD_SPRAY: { cls: "sev-pill-high", label: "Password Spray" },
  };
  const entry = map[type] || { cls: "sev-pill-info", label: type };
  return <span className={entry.cls}>{entry.label}</span>;
}

export function RolePill({ role }) {
  const map = {
    ADMIN: { cls: "sev-pill-low", label: "Admin" },
    SECURITY_ANALYST: { cls: "sev-pill-high", label: "Analyst" },
    AUDITOR: { cls: "sev-pill-info", label: "Auditor" },
  };
  const entry = map[role] || { cls: "sev-pill-info", label: role };
  return <span className={entry.cls}>{entry.label}</span>;
}

export function ActiveBadge({ isActive }) {
  return isActive ? (
    <span className="sev-pill-critical">Blocked</span>
  ) : (
    <span className="sev-pill-ok">Unblocked</span>
  );
}
