import { useApp, type PageId } from "../context/AppContext";

const NAV_ITEMS: Array<{ id: PageId; label: string; badge?: number }> = [
  { id: "overview", label: "Command center" },
  { id: "review", label: "Review queue", badge: 3 },
  { id: "vendors", label: "Vendor intelligence" },
  { id: "documents", label: "Documents" },
  { id: "operations", label: "Operations" },
];

export default function Sidebar() {
  const { page, setPage } = useApp();

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark" />
        <div>
          <strong>ProcureIQ</strong>
          <small>Decision intelligence</small>
        </div>
      </div>

      <div className="workspace-switcher">
        <div className="workspace-avatar">AR</div>
        <div>
          <span>Arcline Infra</span>
          <small>Metro Phase IV</small>
        </div>
      </div>

      <nav>
        <p className="nav-label">Workspace</p>
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
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
          <span>All systems nominal</span>
          <small>99.96%</small>
        </div>
      </div>
    </aside>
  );
}