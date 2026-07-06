import { useState } from "react";
import { useApp, type PageId } from "../context/AppContext";

export default function Topbar() {
  const { signOut, page, workspace, currentUser } = useApp();
  const [open, setOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  const titles: Record<PageId, [string, string]> = {
    overview:   ["Portfolio intelligence", "Procurement command center"],
    review:     ["Auditor workspace",      "Human review queue"],
    vendors:    ["Risk & performance",     "Vendor intelligence"],
    documents:  ["Gatekeeper workspace",   "Document control"],
    operations: ["Reliability & observability", "AI operations"],
  };
  const [eyebrow, title] = titles[page] ?? ["", ""];

  const handleSignOut = async () => {
    setLoggingOut(true);
    // Simulate the database/network delay for Postgres on Neon
    await new Promise(resolve => setTimeout(resolve, 800));
    signOut();
  };

  return (
    <header className="topbar">
      <div className="page-heading">
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <div className="workspace-chip">
          <span>{workspace.name}</span>
          <small>{workspace.project}</small>
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div className="profile-control" style={{ position: "relative" }}>
          <button 
            type="button" 
            className="profile-btn"
            onClick={() => setOpen(!open)} 
            aria-expanded={open}
            style={{ 
              display: "flex", alignItems: "center", gap: "8px", 
              background: "rgba(14, 23, 41, 0.5)", border: "1px solid rgba(145,169,204,0.2)", 
              padding: "6px 12px 6px 6px", borderRadius: "99px", cursor: "pointer", color: "#f9fbff" 
            }}
          >
            <div style={{ 
              width: "28px", height: "28px", borderRadius: "50%", background: "var(--accent)", 
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.85rem", fontWeight: "bold" 
            }}>
              {currentUser?.name?.charAt(0) ?? "U"}
            </div>
            <span style={{ fontSize: "0.9rem", fontWeight: 500 }}>{currentUser?.name?.split(' ')[0] ?? "User"}</span>
          </button>

          {open && (
            <div className="role-menu" style={{ 
              position: "absolute", top: "100%", right: 0, marginTop: "8px", 
              background: "var(--panel)", border: "1px solid var(--line)", 
              borderRadius: "12px", width: "240px", boxShadow: "var(--shadow)", zIndex: 100 
            }}>
              <div style={{ padding: "16px", borderBottom: "1px solid var(--line)" }}>
                <strong style={{ display: "block", color: "var(--text-strong)", fontSize: "0.95rem" }}>
                  {currentUser?.name ?? "User"}
                </strong>
                <small style={{ color: "var(--muted)", fontSize: "0.85rem" }}>{currentUser?.email}</small>
              </div>
              <div style={{ padding: "8px" }}>
                <button type="button" className="menu-item" style={{ width: "100%", textAlign: "left", padding: "10px 12px", background: "transparent", border: "none", color: "var(--text)", fontSize: "0.9rem", cursor: "pointer", borderRadius: "6px" }}>
                  Profile
                </button>
                <button type="button" className="menu-item" style={{ width: "100%", textAlign: "left", padding: "10px 12px", background: "transparent", border: "none", color: "var(--text)", fontSize: "0.9rem", cursor: "pointer", borderRadius: "6px" }}>
                  Settings
                </button>
              </div>
              <div style={{ padding: "8px", borderTop: "1px solid var(--line)" }}>
                <button
                  type="button"
                  onClick={handleSignOut}
                  disabled={loggingOut}
                  style={{ 
                    width: "100%", textAlign: "left", padding: "10px 12px", background: "transparent", 
                    border: "none", color: "var(--danger)", fontSize: "0.9rem", fontWeight: 600, cursor: "pointer", 
                    borderRadius: "6px", display: "flex", alignItems: "center", gap: "8px" 
                  }}
                >
                  {loggingOut ? <span className="auth-spinner" style={{ width: "14px", height: "14px", borderTopColor: "var(--danger)" }} /> : null}
                  {loggingOut ? "Signing out..." : "Sign out"}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}