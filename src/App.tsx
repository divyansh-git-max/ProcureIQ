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
import type { PageId, RoleName, WorkspaceId, PendingUser } from "./context/AppContext";
import { ROLES, workspaces } from "./mockData";
import { Bell, MessageSquare, X } from "lucide-react";

// ─── Role badge colours ───────────────────────────────────────────────────────
const ROLE_COLORS: Record<string, string> = {
  Auditor: "#3b82f6",
  Gatekeeper: "#6366f1",
  Strategist: "#10b981",
};

// ─── Shared Hero Component ───────────────────────────────────────────────────
function AuthHero() {
  return (
    <div className="auth-hero hidden-mobile">
      <div className="auth-hero-content">
        <div className="auth-logo-large">⚡</div>
        <h1>ProcureIQ</h1>
        <p>Next-generation AI procurement intelligence and vendor risk management.</p>
      </div>
    </div>
  );
}

// ─── Login Page ───────────────────────────────────────────────────────────────
function LoginScreen() {
  const { signIn, setAuthMode, sendContactMessage } = useApp();
  const [email, setEmail] = useState("admin@procureiq.demo");
  const [password, setPassword] = useState("admin123");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingContact, setLoadingContact] = useState(false);
  const [showContactForm, setShowContactForm] = useState(false);
  const [contactMessage, setContactMessage] = useState("");
  const [contactSubmitted, setContactSubmitted] = useState(false);

  async function handleSubmit() {
    if (!email || !password) { setError("Email and password are required."); return; }
    setLoading(true);
    const err = await signIn(email, password);
    setLoading(false);
    if (err) {
      setError(err);
      setShowContactForm(true);
    }
  }

  async function handleContactSubmit() {
    if (!contactMessage.trim()) return;
    setLoadingContact(true);
    const err = await sendContactMessage(email, contactMessage);
    setLoadingContact(false);
    if (err) {
      setError(err);
    } else {
      setContactSubmitted(true);
    }
  }

  if (showContactForm) {
    return (
      <div className="auth-shell">
        <AuthHero />
        <div className="auth-content">
          <motion.section
          className="auth-panel"
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
        >
          <div className="auth-brand">
            <div className="auth-logo">⚡</div>
            <span className="auth-product">ProcureIQ</span>
          </div>
          <div className="auth-divider" />

          <h2 className="auth-heading">Login Failed</h2>
          <p className="auth-sub" style={{ color: "#ef4444" }}>{error}</p>

          {contactSubmitted ? (
            <div style={{ textAlign: "center", padding: "2rem 0" }}>
              <div className="auth-success-icon" style={{ marginBottom: "1rem" }}>✓</div>
              <h3 style={{ marginBottom: "0.5rem" }}>Message Sent</h3>
              <p className="auth-sub">The admin has been notified and will contact you shortly.</p>
              <button type="button" className="auth-btn-secondary" style={{ marginTop: "1.5rem" }} onClick={() => { setShowContactForm(false); setContactSubmitted(false); setError(null); }}>
                Back to login
              </button>
            </div>
          ) : (
            <div className="auth-form">
              <p style={{ fontSize: "0.9rem", color: "#64748b", marginBottom: "1rem" }}>
                Having trouble logging in? Send a message directly to the admin team to get your account reviewed.
              </p>
              <label className="auth-label">
                Message to Admin
                <textarea
                  className="auth-input"
                  rows={4}
                  value={contactMessage}
                  onChange={(e) => setContactMessage(e.target.value)}
                  placeholder="I requested access yesterday but..."
                  style={{ resize: "vertical", minHeight: "80px" }}
                />
              </label>

              <div style={{ display: "flex", gap: "1rem" }}>
                <button type="button" className="auth-btn-secondary" onClick={() => setShowContactForm(false)} style={{ flex: 1 }}>
                  Cancel
                </button>
                <button
                  type="button"
                  className="auth-btn-primary"
                  onClick={handleContactSubmit}
                  style={{ flex: 1 }}
                  disabled={loadingContact}
                >
                  {loadingContact ? <span className="auth-spinner" /> : "Send Message"}
                </button>
              </div>
            </div>
          )}
        </motion.section>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-shell">
      <AuthHero />
      <div className="auth-content">
        <motion.section
          className="auth-panel"
          initial={{ opacity: 0, y: 20, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
        >
          <h2 className="auth-heading">Welcome back</h2>
          <p className="auth-sub">Sign in to your procurement workspace</p>


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
              <div style={{ position: "relative" }}>
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setError(null); }}
                  placeholder="••••••••"
                  className="auth-input"
                  style={{ paddingRight: "48px" }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: "absolute", right: "16px", top: "50%", transform: "translateY(-50%)",
                    background: "transparent", border: "none", color: "rgba(255,255,255,0.4)", cursor: "pointer",
                    display: "flex", alignItems: "center", justifyContent: "center", padding: 0
                  }}
                  title={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
                  ) : (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                  )}
                </button>
              </div>
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
        </motion.section>
      </div>
    </div>
  );
}

// ─── Signup / Request Access Page ────────────────────────────────────────────
function SignupScreen() {
  const { submitSignupRequest, setAuthMode } = useApp();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [role, setRole] = useState<RoleName>("Auditor");
  const [wsId, setWsId] = useState<WorkspaceId>(workspaces[0].id);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    if (!name || !email || !password) { setError("Name, email, and password are required."); return; }
    setLoading(true);
    const err = await submitSignupRequest(name, email, role, password);
    setLoading(false);
    if (err) { setError(err); return; }
    setSubmitted(true);
  }

  if (submitted) {
    return (
      <div className="auth-shell">
        <AuthHero />
        <div className="auth-content">
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
      </div>
    );
  }

  return (
    <div className="auth-shell">
      <AuthHero />
      <div className="auth-content">
        <motion.section
          className="auth-panel"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
        >
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
              Password
              <div style={{ position: "relative" }}>
                <input 
                  className="auth-input" 
                  type={showPassword ? "text" : "password"} 
                  value={password} 
                  onChange={(e) => { setPassword(e.target.value); setError(null); }} 
                  placeholder="Create a strong password" 
                  style={{ paddingRight: "48px" }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: "absolute", right: "16px", top: "50%", transform: "translateY(-50%)",
                    background: "transparent", border: "none", color: "rgba(255,255,255,0.4)", cursor: "pointer",
                    display: "flex", alignItems: "center", justifyContent: "center", padding: 0
                  }}
                  title={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
                  ) : (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                  )}
                </button>
              </div>
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

            <button 
              id="signup-submit" 
              type="button" 
              className="auth-btn-primary" 
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading ? <span className="auth-spinner" /> : "Submit request"}
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
    </div>
  );
}

// ─── Admin Approval Dashboard ─────────────────────────────────────────────────
function AdminDashboard() {
  const { pendingUsers, approveUser, rejectUser, signOut } = useApp();
  const [filter, setFilter] = useState<"all" | "pending" | "approved" | "rejected">("pending");
  const [activeRequestUser, setActiveRequestUser] = useState<PendingUser | null>(null);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const filtered = pendingUsers.filter((u) => filter === "all" || u.status === filter);
  const messageRequests = pendingUsers.filter((u) => u.status === "pending" && u.request_message);

  const counts = {
    pending: pendingUsers.filter((u) => u.status === "pending").length,
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
        <div className="admin-header-actions" style={{ display: "flex", alignItems: "center", gap: "16px", position: "relative" }}>
          {/* Notification Bell */}
          <div className="admin-bell-wrap" style={{ position: "relative" }}>
            <button
              type="button"
              className={`admin-bell-btn${notificationsOpen ? " active" : ""}`}
              onClick={() => setNotificationsOpen(!notificationsOpen)}
            >
              <Bell size={20} />
              {messageRequests.length > 0 && (
                <span className="bell-badge">{messageRequests.length}</span>
              )}
            </button>

            {notificationsOpen && (
              <>
                <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, zIndex: 40 }} onClick={() => setNotificationsOpen(false)} />
                <div className="admin-notifications-dropdown" style={{ zIndex: 45 }}>
                  <div className="dropdown-header">
                    <h3>Access Request Messages</h3>
                    {messageRequests.length > 0 && <span className="unread-count">{messageRequests.length} pending</span>}
                  </div>
                  <div className="dropdown-body">
                    {messageRequests.length === 0 ? (
                      <div className="empty-notifications">No new messages.</div>
                    ) : (
                      messageRequests.map((u) => (
                        <div
                          key={u.id}
                          className="notification-item"
                          onClick={() => {
                            setActiveRequestUser(u);
                            setNotificationsOpen(false);
                          }}
                        >
                          <div className="notification-meta">
                            <span className="notif-name">{u.name}</span>
                            <span className="notif-role">{u.role}</span>
                          </div>
                          <p className="notif-excerpt">{u.request_message}</p>
                          <span className="notif-time">{new Date(u.created_at).toLocaleDateString()}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
          <button type="button" className="auth-btn-secondary admin-signout" onClick={signOut}>
            Sign out
          </button>
        </div>
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
                    <span className="user-avatar" style={{ background: ROLE_COLORS[u.role] }}>
                      {u.name[0]}
                    </span>
                    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span>{u.name}</span>
                        {u.request_message && (
                          <button
                            type="button"
                            className="message-indicator-badge"
                            onClick={() => setActiveRequestUser(u)}
                            title="View access request message"
                          >
                            <MessageSquare size={11} />
                            <span>Message</span>
                          </button>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="admin-cell-muted">{u.email}</td>
                  <td>
                    <span className="role-pill" style={{ color: ROLE_COLORS[u.role] || "#7c3aed", borderColor: (ROLE_COLORS[u.role] || "#7c3aed") + "44", background: (ROLE_COLORS[u.role] || "#7c3aed") + "15" }}>
                      {u.role}
                    </span>
                  </td>
                  <td className="admin-cell-muted">{u.workspaceId}</td>
                  <td>
                    <span className={`status-pill status-${u.status}`}>
                      {u.status.charAt(0).toUpperCase() + u.status.slice(1)}
                    </span>
                  </td>
                  <td className="admin-actions">
                    {u.role === "admin" ? (
                      <span className="admin-cell-muted" style={{ fontStyle: "italic", fontSize: "0.85rem" }}>Admin (Protected)</span>
                    ) : (
                      <>
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
                      </>
                    )}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Details Modal Overlay */}
      <AnimatePresence>
        {activeRequestUser && (
          <div className="admin-modal-overlay" onClick={() => setActiveRequestUser(null)}>
            <motion.div
              className="admin-modal-content"
              onClick={(e) => e.stopPropagation()}
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ duration: 0.2 }}
            >
              <div className="modal-header">
                <h2>Access Request Details</h2>
                <button type="button" className="close-btn" onClick={() => setActiveRequestUser(null)}>
                  <X size={18} />
                </button>
              </div>
              <div className="modal-body">
                <div className="user-profile-summary">
                  <span className="user-avatar-large" style={{ background: ROLE_COLORS[activeRequestUser.role] }}>
                    {activeRequestUser.name[0]}
                  </span>
                  <div>
                    <h3>{activeRequestUser.name}</h3>
                    <p className="user-email">{activeRequestUser.email}</p>
                  </div>
                </div>

                <div className="metadata-grid">
                  <div className="meta-card">
                    <span className="meta-label">Requested Role</span>
                    <span className="role-pill" style={{ color: ROLE_COLORS[activeRequestUser.role] || "#7c3aed", borderColor: (ROLE_COLORS[activeRequestUser.role] || "#7c3aed") + "44", background: (ROLE_COLORS[activeRequestUser.role] || "#7c3aed") + "15", display: "inline-block", width: "fit-content", fontSize: "0.8rem", padding: "2px 8px" }}>
                      {activeRequestUser.role}
                    </span>
                  </div>
                  <div className="meta-card">
                    <span className="meta-label">Workspace</span>
                    <span className="meta-value">{activeRequestUser.workspaceId || "Default"}</span>
                  </div>
                  <div className="meta-card">
                    <span className="meta-label">Submitted On</span>
                    <span className="meta-value">{new Date(activeRequestUser.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="meta-card">
                    <span className="meta-label">Current Status</span>
                    <span className={`status-pill status-${activeRequestUser.status}`}>
                      {activeRequestUser.status.charAt(0).toUpperCase() + activeRequestUser.status.slice(1)}
                    </span>
                  </div>
                </div>

                <div className="message-container">
                  <h4>Message to Admin</h4>
                  <p className="message-text">
                    {activeRequestUser.request_message || "No message provided."}
                  </p>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn-sec" onClick={() => setActiveRequestUser(null)}>
                  Close
                </button>
                {activeRequestUser.status === "pending" && (
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button
                      type="button"
                      className="action-btn action-reject"
                      onClick={async () => {
                        await rejectUser(activeRequestUser.id);
                        setActiveRequestUser(null);
                      }}
                    >
                      Reject
                    </button>
                    <button
                      type="button"
                      className="action-btn action-approve"
                      onClick={async () => {
                        await approveUser(activeRequestUser.id);
                        setActiveRequestUser(null);
                      }}
                    >
                      Approve
                    </button>
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
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
  const pageContent: Record<PageId, React.ReactNode> = {
    overview: <CommandCenter />,
    review: <ReviewQueue />,
    vendors: <VendorIntelligence />,
    documents: <DocumentControl />,
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