import { useEffect, useState } from "react";
import { fetchFindings, decideFinding } from "../api/client";
import Severity from "./shared/Severity";
import AgentFlow from "./shared/AgentFlow";
import { useApp } from "../context/AppContext";
import type { Finding } from "../types";
import "../styles/ReviewQueue.css";


export default function ReviewQueue() {
  const { roleInfo } = useApp();
  const [findings, setFindings] = useState<Finding[]>([]);
  const [selected, setSelected] = useState<Finding | null>(null);
  const [statuses, setStatuses] = useState<Record<string, "approved" | "dismissed">>({});
  const [toast, setToast] = useState("");
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    fetchFindings()
      .then((data) => {
        setFindings(data);
        setSelected(data[0] ?? null);
      })
      .catch((err: Error) => showToast(`Could not load findings: ${err.message}`))
      .finally(() => setLoaded(true));
  }, []);

  function showToast(message: string) {
    setToast(message);
    setTimeout(() => setToast(""), 3000);
  }

  async function decide(id: string, status: "approved" | "dismissed") {
    if (!roleInfo.canApprove) return;
    try {
      await decideFinding(id, status);
    } catch (err) {
      showToast(`Decision not saved: ${(err as Error).message}`);
      return;
    }
    setStatuses((prev) => ({ ...prev, [id]: status }));
    showToast(status === "approved" ? "Approved and logged to audit trail" : "Dismissed and logged to audit trail");
  }

  if (!loaded) return <div className="loading">Loading review queue…</div>;
  if (!selected) {
    return (
      <div className="loading">
        No findings awaiting review.
        {toast && <div className="toast">{toast}</div>}
      </div>
    );
  }

  return (
    <div className="review-layout review-queue-layout">
      <section className="panel queue-panel">
        <div className="queue-list">
          {findings.map((f) => (
            <button
              key={f.id}
              className={`queue-item ${selected.id === f.id ? "selected" : ""}`}
              onClick={() => setSelected(f)}
            >
              <div className="queue-item-top">
                <Severity level={f.severity} />
                <span>{f.id}</span>
                {statuses[f.id] && <span className={`decision-tag ${statuses[f.id]}`}>{statuses[f.id]}</span>}
              </div>
              <strong>{f.title}</strong>
              <p>{f.vendor}</p>
              <div className="queue-item-foot">
                <span>{f.amount}</span>
                <span>{f.confidence}% confidence</span>
              </div>
            </button>
          ))}
        </div>
      </section>

      <section className="panel evidence-panel">
        <div className="evidence-head">
          <Severity level={selected.severity} />
          <h2>{selected.title}</h2>
          <p>{selected.vendor}</p>
        </div>

        <div className="confidence-block">
          <div className="confidence-row">
            <span>Judge confidence</span>
            <strong>{selected.confidence}%</strong>
          </div>
          <div className="confidence-track">
            <span style={{ width: `${selected.confidence}%` }} />
          </div>
        </div>

        <div className="evidence-section">
          <h3>Agent reasoning</h3>
          <p>{selected.detail}</p>
          <ol className="reason-steps">
            {selected.reasoningSteps.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </div>

        <div className="evidence-section">
          <h3>Agent path (trajectory)</h3>
          <AgentFlow path={selected.agentPath} />
        </div>

        <div className="evidence-section">
          <h3>Source evidence</h3>
          <div className="citation-card">
            <strong>{selected.source}</strong>
            <small>{selected.clause}</small>
            <span className="verified-pill">Verified</span>
          </div>
        </div>

        <div className="decision-bar">
          <div>
            <small>{roleInfo.canApprove ? "Human approval required" : `${roleInfo.description} — view only`}</small>
            <span>No action is sent without an Auditor's decision.</span>
          </div>
          <button className="dismiss-button" disabled={!roleInfo.canApprove} onClick={() => decide(selected.id, "dismissed")}>
            Dismiss
          </button>
          <button className="approve-button" disabled={!roleInfo.canApprove} onClick={() => decide(selected.id, "approved")}>
            Approve & dispatch
          </button>
        </div>
      </section>

      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}