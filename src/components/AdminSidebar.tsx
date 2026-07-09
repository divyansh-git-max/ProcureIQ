
import { Users, BarChart } from "lucide-react";

export type AdminPageId = "users" | "stats";

interface AdminSidebarProps {
  page: AdminPageId;
  setPage: (page: AdminPageId) => void;
}

const NAV_ITEMS: Array<{ id: AdminPageId; label: string; icon: React.ReactNode }> = [
  { id: "users", label: "Users", icon: <Users size={18} /> },
  { id: "stats", label: "Stats", icon: <BarChart size={18} /> },
];

export default function AdminSidebar({ page, setPage }: AdminSidebarProps) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <strong>ProcureIQ</strong>
        <small>Admin Console</small>
      </div>

      <nav style={{ marginTop: "24px" }}>
        <p className="nav-label">Management</p>
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`nav-item ${page === item.id ? "active" : ""}`}
            onClick={() => setPage(item.id)}
            style={{ display: "flex", alignItems: "center", gap: "12px" }}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-status">
        <div className="status-head">
          <span>Admin mode active</span>
        </div>
      </div>
    </aside>
  );
}
