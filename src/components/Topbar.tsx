import { useState } from "react";
import { useApp, type PageId } from "../context/AppContext";
import { ROLES } from "../mockData";

export default function Topbar() {
  const { role, signOut, page, workspace, currentUser } = useApp();
  const [open, setOpen] = useState(false);

  const titles: Record<PageId, [string, string]> = {
    overview:   ["Portfolio intelligence", "Procurement command center"],
    review:     ["Auditor workspace",      "Human review queue"],
    vendors:    ["Risk & performance",     "Vendor intelligence"],
    documents:  ["Gatekeeper workspace",   "Document control"],
    operations: ["Reliability & observability", "AI operations"],
  };
  const [eyebrow, title] = titles[page] ?? ["", ""];

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
        {/* Role badge — read-only now (role is set at login) */}
        <div className="role-control">
          <button type="button" onClick={() => setOpen(!open)} aria-expanded={open}>
            {role} view · {ROLES[role].description}
          </button>
          {open && (
            <div className="role-menu">
              <div style={{ padding: "10px 12px 6px", fontSize: "0.76rem", color: "#8d9bb0", textTransform: "uppercase", letterSpacing: "0.1em" }}>
                Signed in as
              </div>
              <div style={{ padding: "8px 12px 12px" }}>
                <strong style={{ display: "block", color: "#f9fbff", fontSize: "0.92rem" }}>
                  {currentUser?.name ?? "User"}
                </strong>
                <small style={{ color: "#8d9bb0" }}>{currentUser?.email}</small>
              </div>
              <hr style={{ margin: "0 8px", border: "none", borderTop: "1px solid rgba(145,169,204,0.14)" }} />
              <button
                type="button"
                onClick={() => { signOut(); setOpen(false); }}
                style={{ width: "100%", color: "#fb7185", marginTop: 4 }}
              >
                <strong>Sign out</strong>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}