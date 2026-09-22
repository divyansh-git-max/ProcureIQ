import { useEffect, useState } from "react";
import {
  AreaChart, Area, Line, PieChart, Pie, Cell,
  ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip,
} from "recharts";
import { fetchSummary, fetchFindings } from "../api/client";
import PanelHeader from "./shared/PanelHeader";
import Severity from "./shared/Severity";
import AgentFlow from "./shared/AgentFlow";
import { useApp } from "../context/AppContext";
import type { Finding, Summary } from "../types";

type ChartTooltipProps = {
  active?: boolean;
  label?: string;
  payload?: Array<{
    name?: string;
    value?: number;
    color?: string;
    dataKey?: string;
  }>;
};

function ChartTooltip({ active, label, payload }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;

  return (
    <div className="chart-tooltip">
      {label && <strong>{label}</strong>}
      {payload.map((item) => (
        <span key={item.dataKey ?? item.name}>
          <i style={{ background: item.color }} />
          {item.name ?? item.dataKey}: {item.value}
        </span>
      ))}
    </div>
  );
}

export default function CommandCenter() {
  const { setPage } = useApp();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [topFindings, setTopFindings] = useState<Finding[]>([]);
  // animKey increments whenever the primary finding changes → AgentFlow replays its intro
  const [animKey, setAnimKey] = useState(0);

  useEffect(() => {
    fetchSummary().then(setSummary);
    fetchFindings().then((data) => setTopFindings(data.slice(0, 3)));
  }, []);

  // replay animation whenever the primary finding changes
  useEffect(() => {
    setAnimKey((k) => k + 1);
  }, [topFindings]);

  if (!summary) return <div className="loading">Loading command center…</div>;

  const openFindingsTotal = summary.severityMix.reduce((total, item) => total + item.value, 0);
  const primaryFinding = topFindings[0];

  return (
    <div className="stack command-center">
      <section className="kpi-grid">
        {summary.kpis.map((kpi) => (
          <article key={kpi.id} className={`kpi-card command-kpi command-kpi--${kpi.tone}`}>
            <div className="command-kpi-flip">
              <div className="command-kpi-front">
                <div className="kpi-label">
                  <span>{kpi.label}</span>
                  <em>{kpi.delta}</em>
                </div>
                <strong>{kpi.value}</strong>
                <small>{kpi.foot}</small>
              </div>
              <div className="command-kpi-back">
                <span>{kpi.label}</span>
                <strong>{kpi.delta}</strong>
                <small>{kpi.foot}</small>
              </div>
            </div>
          </article>
        ))}
      </section>

      <section className="grid-2">
        <article className="panel command-chart-panel">
          <PanelHeader eyebrow="Portfolio signal" title="Risk exposure trend" action="Last 7 days" />
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={summary.weeklyRisk}>
              <defs>
                <linearGradient id="exposure-fill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.28} />
                  <stop offset="100%" stopColor="#f59e0b" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(145, 169, 204, 0.12)" vertical={false} />
              <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#8d9bb0" }} />
              <YAxis hide />
              <Tooltip content={<ChartTooltip />} cursor={{ stroke: "rgba(125, 211, 252, 0.2)" }} />
              <Area type="monotone" dataKey="exposure" name="Exposure" stroke="#f59e0b" strokeWidth={2} fill="url(#exposure-fill)" />
              <Line type="monotone" dataKey="resolved" name="Resolved" stroke="#4ade80" strokeWidth={2.5} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </article>

        <article className="panel command-chart-panel severity-panel">
          <PanelHeader eyebrow="Risk mix" title="Open findings" action="32 total" />
          <div className="severity-mix-wrap">
            <div className="severity-chart-shell">
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={summary.severityMix} dataKey="value" innerRadius={58} outerRadius={82} paddingAngle={4}>
                    {summary.severityMix.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<ChartTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              <div className="severity-total">
                <strong>{openFindingsTotal}</strong>
                <span>open</span>
              </div>
            </div>
            <div className="severity-legend">
              {summary.severityMix.map((item) => (
                <div key={item.name}>
                  <span><i style={{ background: item.color }} />{item.name}</span>
                  <strong>{item.value}</strong>
                </div>
              ))}
            </div>
          </div>
        </article>
      </section>

      <section className="grid-2 command-lower-grid">
        <article className="panel span-2">
          <PanelHeader eyebrow="Priority queue" title="Findings needing attention" action="View queue" />
          <div className="priority-cards-grid">
            {topFindings.map((f) => (
              <button key={f.id} className="priority-card" onClick={() => setPage("review")}>
                <div className="priority-card-header">
                  <Severity level={f.severity} />
                  <div className="confidence-pill">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    <span>{f.confidence}% Conf.</span>
                  </div>
                </div>
                
                <div className="priority-card-body">
                  <h3 className="finding-title">{f.title}</h3>
                  <p className="finding-meta">
                    <span className="vendor-tag">{f.vendor}</span>
                    <span className="dot">·</span>
                    <span className="source-tag">{f.source}</span>
                  </p>
                </div>
                
                <div className="priority-card-footer">
                  <span className="finding-amount">{f.amount}</span>
                  <div className="action-arrow">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </article>
      </section>

      {/* ── Full-width agent reasoning graph ─────────────────────── */}
      <section>
        <article className="panel command-agent-panel">
          <PanelHeader eyebrow="Agent activity" title="Live reasoning graph" action="Streaming" />

          {primaryFinding && (
            <div className="agent-focus-card">
              <Severity level={primaryFinding.severity} />
              <strong>{primaryFinding.title}</strong>
              <span>{primaryFinding.id} · {primaryFinding.confidence}% judge confidence</span>
            </div>
          )}

          {/* AgentFlow — key={animKey} forces full re-mount (replay intro) when finding changes */}
          <AgentFlow key={animKey} path={primaryFinding?.agentPath ?? []} />

          <div className="agent-health-strip">
            <span>4 agents active</span>
            <span>RAG verified</span>
            <span>HITL gated</span>
          </div>
        </article>
      </section>
    </div>
  );
}