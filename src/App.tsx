import { AppProvider, useApp } from "./context/AppContext";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import CommandCenter from "./components/CommandCenter";
import ReviewQueue from "./components/ReviewQueue";
import VendorIntelligence from "./components/VendorIntelligence";
import DocumentControl from "./components/DocumentControl";
import Operations from "./components/Operations";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";
import type { AuthMode, PageId, RoleName, WorkspaceId } from "./context/AppContext";
import { ROLES, workspaces } from "./mockData";

// ─── Role badge colours ───────────────────────────────────────────────────────
const ROLE_COLORS: Record<string, string> = {
  Auditor: "#7c3aed",
  Gatekeeper: "#0ea5e9",
  Strategist: "#10b981",
};

// ─── Login Page ───────────────────────────────────────────────────────────────
function LoginScreen() {
  const { signIn, setAuthMode } = useApp();
  const [email, setEmail]       = useState("admin@procureiq.com");
  const [password, setPassword] = useState("admin123");
  const [error, setError]       = useState<string | null>(null);
  const [loading, setLoading]   = useState(false);

  function handleSubmit() {
    if (!email || !password) { setError("Email and password are required."); return; }
    setLoading(true);
    setTimeout(() => {
      const err = signIn(email, password);
      setLoading(false);
      if (err) setError(err);
    }, 600);
  }

  return (
    <div className="auth-shell">
      <motion.section
        className="auth-panel"
        initial={{ opacity: 0, y: 20, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
      >
        {/* Brand */}
        <div className="auth-brand">
          <div className="auth-logo">⚡</div>
          <span className="auth-product">ProcureIQ</span>
          <span className="auth-tagline">AI Procurement Intelligence</span>
        </div>

        <div className="auth-divider" />

        <h2 className="auth-heading">Welcome back</h2>
        <p className="auth-sub">Sign in to your procurement workspace</p>

        {/* Demo hint */}
        <div className="auth-hint">
          <strong>Demo credentials pre-filled.</strong> You can also login as any approved
          user below — e.g. <code>arjun@procureiq.com</code> (no password needed in demo mode).
        </div>

        {error && <div className="auth-error">{error}</div>}

        <div className="auth-form">
          <label className="auth-label">
            Email address
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setError(null); }}
              placeholder="you@company.com"
              className="auth-input"
            />
          </label>

          <label className="auth-label">
            Password
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setError(null); }}
              placeholder="••••••••"
              className="auth-input"
            />
          </label>

          <button
            id="login-submit"
            type="button"
            className="auth-btn-primary"
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? <span className="auth-spinner" /> : "Sign in"}
          </button>
        </div>

        <div className="auth-footer">
          Don't have access?{" "}
          <button type="button" className="auth-link" onClick={() => setAuthMode("signup")}>
            Request access
          </button>
        </div>

        {/* Quick-login tiles */}
        <div className="auth-divider" />
        <p className="auth-quick-label">Quick login (demo)</p>
        <div className="auth-quick-grid">
          {[
            { name: "Arjun Mehta", email: "arjun@procureiq.com", role: "Auditor" },
            { name: "Priya Sharma", email: "priya@procureiq.com", role: "Gatekeeper" },
            { name: "Ravi Nair", email: "ravi@procureiq.com", role: "Strategist" },
          ].map((u) => (
            <button
              key={u.email}
              type="button"
              className="auth-quick-tile"
              onClick={() => { setEmail(u.email); setPassword("demo"); signIn(u.email, "any"); }}
            >
              <span className="quick-avatar" style={{ background: ROLE_COLORS[u.role] }}>
                {u.name[0]}
              </span>
              <span className="quick-info">
                <strong>{u.name}</strong>
                <span className="quick-role" style={{ color: ROLE_COLORS[u.role] }}>{u.role}</span>
              </span>
            </button>
          ))}
        </div>
      </motion.section>
    </div>
  );
}

// ─── Signup / Request Access Page ────────────────────────────────────────────
function SignupScreen() {
  const { submitSignupRequest, setAuthMode } = useApp();
  const [name, setName]           = useState("");
  const [email, setEmail]         = useState("");
  const [role, setRole]           = useState<RoleName>("Auditor");
  const [wsId, setWsId]           = useState<WorkspaceId>(workspaces[0].id);
  const [error, setError]         = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit() {
    if (!name || !email) { setError("Name and email are required."); return; }
    const err = submitSignupRequest(name, email, role, wsId);
    if (err) { setError(err); return; }
    setSubmitted(true);
  }

  if (submitted) {
    return (
      <div className="auth-shell">
        <motion.section
          className="auth-panel auth-panel--center"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
        >
          <div className="auth-success-icon">✓</div>
          <h2 className="auth-heading">Request submitted</h2>
          <p className="auth-sub">
            Your access request for the <strong>{role}</strong> role has been sent to the admin.
            You'll be notified once it's approved.
          </p>
          <button type="button" className="auth-btn-secondary" onClick={() => setAuthMode("login")}>
            Back to login
          </button>
        </motion.section>
      </div>
    );
  }

  return (
    <div className="auth-shell">
      <motion.section
        className="auth-panel"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="auth-brand">
          <div className="auth-logo">⚡</div>
          <span className="auth-product">ProcureIQ</span>
        </div>
        <div className="auth-divider" />

        <h2 className="auth-heading">Request access</h2>
        <p className="auth-sub">An admin will review and approve your role assignment.</p>

        {error && <div className="auth-error">{error}</div>}

        <div className="auth-form">
          <label className="auth-label">
            Full name
            <input className="auth-input" value={name} onChange={(e) => { setName(e.target.value); setError(null); }} placeholder="Aman Verma" />
          </label>
          <label className="auth-label">
            Work email
            <input className="auth-input" type="email" value={email} onChange={(e) => { setEmail(e.target.value); setError(null); }} placeholder="you@company.com" />
          </label>
          <label className="auth-label">
            Requested role
            <select className="auth-input" value={role} onChange={(e) => setRole(e.target.value as RoleName)}>
              {Object.entries(ROLES).map(([key, info]) => (
                <option key={key} value={key}>{key} — {info.description}</option>
              ))}
            </select>
          </label>
          <label className="auth-label">
            Workspace
            <select className="auth-input" value={wsId} onChange={(e) => setWsId(e.target.value as WorkspaceId)}>
              {workspaces.map((w) => (
                <option key={w.id} value={w.id}>{w.name} · {w.project}</option>
              ))}
            </select>
          </label>

          <button id="signup-submit" type="button" className="auth-btn-primary" onClick={handleSubmit}>
            Submit request
          </button>
        </div>

        <div className="auth-footer">
          Already have access?{" "}
          <button type="button" className="auth-link" onClick={() => setAuthMode("login")}>
            Sign in
          </button>
        </div>
      </motion.section>
    </div>
  );
}

// ─── Admin Approval Dashboard ─────────────────────────────────────────────────
function AdminDashboard() {
  const { pendingUsers, approveUser, rejectUser, signOut } = useApp();
  const [filter, setFilter] = useState<"all" | "pending" | "approved" | "rejected">("pending");

  const filtered = pendingUsers.filter((u) => filter === "all" || u.status === filter);
  const counts = {
    pending:  pendingUsers.filter((u) => u.status === "pending").length,
    approved: pendingUsers.filter((u) => u.status === "approved").length,
    rejected: pendingUsers.filter((u) => u.status === "rejected").length,
  };

  return (
    <div className="admin-shell">
      <header className="admin-header">
        <div className="admin-header-brand">
          <span className="auth-logo" style={{ fontSize: 20 }}>⚡</span>
          <span className="auth-product">ProcureIQ</span>
          <span className="admin-badge">Admin Console</span>
        </div>
        <button type="button" className="auth-btn-secondary admin-signout" onClick={signOut}>
          Sign out
        </button>
      </header>

      <div className="admin-body">
        <div className="admin-stats">
          {[
            { label: "Pending", count: counts.pending, color: "#f59e0b" },
            { label: "Approved", count: counts.approved, color: "#10b981" },
            { label: "Rejected", count: counts.rejected, color: "#ef4444" },
          ].map((s) => (
            <div className="admin-stat-card" key={s.label}>
              <span className="stat-count" style={{ color: s.color }}>{s.count}</span>
              <span className="stat-label">{s.label}</span>
            </div>
          ))}
        </div>

        <div className="admin-table-header">
          <h2 className="admin-title">User Access Requests</h2>
          <div className="admin-filters">
            {(["all", "pending", "approved", "rejected"] as const).map((f) => (
              <button
                key={f}
                type="button"
                className={`admin-filter-btn${filter === f ? " active" : ""}`}
                onClick={() => setFilter(f)}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Requested Role</th>
                <th>Workspace</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr><td colSpan={6} className="admin-empty">No users in this filter.</td></tr>
              )}
              {filtered.map((u) => (
                <motion.tr
                  key={u.id}
                  className="admin-row"
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <td className="admin-cell-name">
                    <span className="user-avatar" style={{ background: ROLE_COLORS[u.requestedRole] }}>
                      {u.name[0]}
                    </span>
                    {u.name}
                  </td>
                  <td className="admin-cell-muted">{u.email}</td>
                  <td>
                    <span className="role-pill" style={{ color: ROLE_COLORS[u.requestedRole], borderColor: ROLE_COLORS[u.requestedRole] + "44", background: ROLE_COLORS[u.requestedRole] + "15" }}>
                      {u.requestedRole}
                    </span>
                  </td>
                  <td className="admin-cell-muted">{u.workspaceId}</td>
                  <td>
                    <span className={`status-pill status-${u.status}`}>
                      {u.status.charAt(0).toUpperCase() + u.status.slice(1)}
                    </span>
                  </td>
                  <td className="admin-actions">
                    {u.status === "pending" && (
                      <>
                        <button type="button" className="action-btn action-approve" onClick={() => approveUser(u.id)}>
                          Approve
                        </button>
                        <button type="button" className="action-btn action-reject" onClick={() => rejectUser(u.id)}>
                          Reject
                        </button>
                      </>
                    )}
                    {u.status === "approved" && (
                      <button type="button" className="action-btn action-reject" onClick={() => rejectUser(u.id)}>
                        Revoke
                      </button>
                    )}
                    {u.status === "rejected" && (
                      <button type="button" className="action-btn action-approve" onClick={() => approveUser(u.id)}>
                        Reinstate
                      </button>
                    )}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ─── Main App Shell (authenticated user view) ─────────────────────────────────
function Shell() {
  const { page, role, setPage, isAuthenticated, isAdmin, authMode } = useApp();
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    const allowedPages: PageId[] =
      role === "Gatekeeper"
        ? ["documents"]
        : role === "Strategist"
          ? ["overview", "vendors", "operations"]
          : ["overview", "review", "vendors", "documents", "operations"];
    if (!allowedPages.includes(page)) setPage(allowedPages[0]);
  }, [page, role, setPage]);

  // Not authenticated — show auth screens
  if (!isAuthenticated) {
    if (authMode === "signup") return <SignupScreen />;
    return <LoginScreen />;
  }

  // Admin view
  if (isAdmin) return <AdminDashboard />;

  // Regular user view
  const pageContent: Record<PageId, JSX.Element> = {
    overview:   <CommandCenter />,
    review:     <ReviewQueue />,
    vendors:    <VendorIntelligence />,
    documents:  <DocumentControl />,
    operations: <Operations />,
  };

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-shell">
        <Topbar />
        <div className="page-frame">
          <AnimatePresence mode="wait">
            <motion.div
              key={page}
              className="page-stage"
              initial={{ opacity: 0, y: reduceMotion ? 0 : 18, filter: reduceMotion ? "none" : "blur(6px)" }}
              animate={{ opacity: 1, y: 0, filter: "none" }}
              exit={{ opacity: 0, y: reduceMotion ? 0 : -12, filter: reduceMotion ? "none" : "blur(4px)" }}
              transition={{ duration: reduceMotion ? 0 : 0.28, ease: [0.22, 1, 0.36, 1] }}
            >
              {pageContent[page]}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <Shell />
    </AppProvider>
  );
}