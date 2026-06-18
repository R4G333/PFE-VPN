import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  LayoutDashboard,
  ShieldAlert,
  Users,
  Network,
  Ban,
  ScrollText,
  UserCog,
  LogOut,
  ShieldCheck,
} from "lucide-react";

const NAV_SECTIONS = {
  monitor: {
    label: "Monitor",
    icon: LayoutDashboard,
    links: [
      { to: "/dashboard", label: "Dashboard", roles: null },
    ],
  },
  access: {
    label: "Access Control",
    icon: Network,
    links: [
      { to: "/requests", label: "VPN Requests", roles: ["ADMIN", "SECURITY_ANALYST"] },
      { to: "/vpn-users", label: "VPN Users", roles: ["ADMIN", "SECURITY_ANALYST"] },
    ],
  },
  security: {
    label: "Security",
    icon: ShieldAlert,
    links: [
      { to: "/alerts", label: "Alerts", roles: null },
      { to: "/blocked-devices", label: "Blocked Devices", roles: null },
    ],
  },
  admin: {
    label: "Administration",
    icon: UserCog,
    links: [
      { to: "/users", label: "App Users", roles: ["ADMIN"] },
      { to: "/audit-logs", label: "Audit Logs", roles: null },
    ],
  },
};

const RAIL_ITEMS = [
  { key: "monitor", icon: LayoutDashboard, label: "Monitor" },
  { key: "access", icon: Network, label: "Access Control" },
  { key: "security", icon: ShieldAlert, label: "Security" },
  { key: "admin", icon: UserCog, label: "Administration" },
];

export default function AppLayout() {
  const { user, logout, hasRole } = useAuth();
  const navigate = useNavigate();

  const path = window.location.pathname;
  let activeSection = "monitor";
  for (const [key, section] of Object.entries(NAV_SECTIONS)) {
    if (section.links.some((l) => path.startsWith(l.to))) {
      activeSection = key;
      break;
    }
  }

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const section = NAV_SECTIONS[activeSection];
  const visibleLinks = section.links.filter(
    (l) => !l.roles || hasRole(...l.roles)
  );

  return (
    <div className="app-shell">
      {/* Icon rail */}
      <div className="icon-rail">
        <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-md bg-chrome-600 text-white">
          <ShieldCheck size={20} />
        </div>
        {RAIL_ITEMS.map((item) => {
          const Icon = item.icon;
          const sectionLinks = NAV_SECTIONS[item.key].links.filter(
            (l) => !l.roles || hasRole(...l.roles)
          );
          if (sectionLinks.length === 0) return null;
          const firstLink = sectionLinks[0].to;
          return (
            <button
              key={item.key}
              title={item.label}
              onClick={() => navigate(firstLink)}
              className={`icon-rail-btn ${activeSection === item.key ? "active" : ""}`}
            >
              <Icon size={20} />
            </button>
          );
        })}
        <div className="flex-1" />
        <button
          title="Log out"
          onClick={handleLogout}
          className="icon-rail-btn"
        >
          <LogOut size={20} />
        </button>
      </div>

      {/* Sub-sidebar */}
      <div className="sub-sidebar">
        <div className="sub-sidebar-header">
          <div className="text-sm font-bold text-white">Sentinel VAC</div>
          <div className="text-[11px] text-ink-400">VPN Access Console</div>
        </div>
        <nav className="flex flex-col py-2">
          <div className="px-4 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-widest text-ink-500">
            {section.label}
          </div>
          {visibleLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `nav-link ${isActive ? "active" : ""}`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Main area */}
      <div className="main-area">
        <div className="top-bar">
          <div className="text-xs text-ink-500">
            hightech.local <span className="mx-1.5 text-ink-300">/</span>{" "}
            <span className="text-ink-700 font-medium">{section.label}</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs">
              <span className="live-dot" />
              <span className="text-ink-600">Live</span>
            </div>
            <div className="h-6 w-px bg-border" />
            <div className="text-right">
              <div className="text-xs font-semibold text-ink-900">
                {user?.username}
              </div>
              <div className="text-[11px] text-ink-500">{user?.role}</div>
            </div>
          </div>
        </div>
        <div className="content-area">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
