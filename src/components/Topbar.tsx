import { useState } from "react";
import { useApp, type PageId, type RoleName } from "../context/AppContext";
import { ROLES } from "../mockData";

export default function Topbar() {
  const { role, setRole, page, workspace } = useApp();
  const [open, setOpen] = useState(false);

  const titles: Record<PageId, [string, string]> = {
    overview: ["Portfolio intelligence", "Procurement command center"],
    review: ["Auditor workspace", "Human review queue"],
    vendors: ["Risk & performance", "Vendor intelligence"],
    documents: ["Gatekeeper workspace", "Document control"],
    operations: ["Reliability & observability", "AI operations"],
  };
  const roleEntries = Object.entries(ROLES) as Array<[RoleName, (typeof ROLES)[RoleName]]>;
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

      <div className="role-control">
        <button type="button" aria-expanded={open} onClick={() => setOpen(!open)}>
          {role} view · {ROLES[role].description}
        </button>
        {open && (
          <div className="role-menu">
            {roleEntries.map(([name, info]) => (
              <button
                key={name}
                type="button"
                onClick={() => {
                  setRole(name);
                  setOpen(false);
                }}
              >
                <strong>{name}</strong>
                <small>{info.description}</small>
              </button>
            ))}
          </div>
        )}
      </div>
    </header>
  );
}