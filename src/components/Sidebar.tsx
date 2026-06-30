import { useApp, type PageId } from "../context/AppContext";
import { useMemo, useState } from "react";
import { workspaces } from "../mockData";

const NAV_ITEMS: Array<{ id: PageId; label: string; badge?: number }> = [
  { id: "overview", label: "Command center" },
  { id: "review", label: "Review queue", badge: 3 },
  { id: "vendors", label: "Vendor intelligence" },
  { id: "documents", label: "Documents" },
  { id: "operations", label: "Operations" },
];

export default function Sidebar() {
  const { page, setPage, role, workspace, setWorkspaceId } = useApp();
  const [workspaceOpen, setWorkspaceOpen] = useState(false);

  const visibleItems = useMemo(() => {
    if (role === "Gatekeeper") return NAV_ITEMS.filter((item) => item.id === "documents");
    if (role === "Strategist") return NAV_ITEMS.filter((item) => item.id !== "review" && item.id !== "documents");
    return NAV_ITEMS;
  }, [role]);

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark" />
        <div>
          <strong>ProcureIQ</strong>
          <small>Decision intelligence</small>
        </div>
      </div>

      <div className="workspace-switcher-wrap">
        <button type="button" className="workspace-switcher" onClick={() => setWorkspaceOpen((open) => !open)}>
          <div className="workspace-avatar">{workspace.initials}</div>
          <div>
            <span>{workspace.name}</span>
            <small>{workspace.project}</small>
          </div>
          <em>Switch</em>
        </button>
        {workspaceOpen && (
          <div className="workspace-menu">
            {workspaces.map((item) => (
              <button
                key={item.id}
                type="button"
                className={item.id === workspace.id ? "active" : ""}
                onClick={() => {
                  setWorkspaceId(item.id);
                  setWorkspaceOpen(false);
                }}
              >
                <strong>{item.name}</strong>
                <small>{item.project}</small>
                <span>{item.description}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      <nav>
        <p className="nav-label">Workspace</p>
        {visibleItems.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`nav-item ${page === item.id ? "active" : ""}`}
            onClick={() => setPage(item.id)}
          >
            <span>{item.label}</span>
            {item.badge ? <em>{item.badge}</em> : null}
          </button>
        ))}
      </nav>

      <div className="sidebar-status">
        <div className="status-head">
          <span>{role} mode active</span>
          <small>99.96%</small>
        </div>
      </div>
    </aside>
  );
}