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

export default function CommandCenter() {
  const { setPage } = useApp();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [topFindings, setTopFindings] = useState<Finding[]>([]);

  useEffect(() => {
    fetchSummary().then(setSummary);
    fetchFindings().then((data) => setTopFindings(data.slice(0, 3)));
  }, []);

  if (!summary) return <div className="loading">Loading command center…</div>;

  return (
    <div className="stack">
      <section className="kpi-grid">
        {summary.kpis.map((kpi) => (
          <article key={kpi.id} className="kpi-card">
            <div className="kpi-label">
              {kpi.label}
              <span className={kpi.delta.includes("-") ? "good" : "bad"}>{kpi.delta}</span>
            </div>
            <strong>{kpi.value}</strong>
            <small>{kpi.foot}</small>
          </article>
        ))}
      </section>

      <section className="grid-2">
        <article className="panel">
          <PanelHeader eyebrow="Portfolio signal" title="Risk exposure trend" action="Last 7 days" />
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={summary.weeklyRisk}>
              <CartesianGrid stroke="var(--color-border-tertiary)" vertical={false} />
              <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fontSize: 11 }} />
              <YAxis hide />
              <Tooltip />
              <Area type="monotone" dataKey="exposure" stroke="#378ADD" fill="#378ADD" fillOpacity={0.15} />
              <Line type="monotone" dataKey="resolved" stroke="#639922" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </article>

        <article className="panel">
          <PanelHeader eyebrow="Risk mix" title="Open findings" action="32 total" />
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={summary.severityMix} dataKey="value" innerRadius={55} outerRadius={75} paddingAngle={3}>
                {summary.severityMix.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </article>
      </section>

      <section className="grid-2">
        <article className="panel span-2">
          <PanelHeader eyebrow="Priority queue" title="Findings needing attention" action="View queue" />
          <div className="finding-list">
            {topFindings.map((f) => (
              <button key={f.id} className="finding-row" onClick={() => setPage("review")}>
                <Severity level={f.severity} />
                <span className="finding-main">
                  <strong>{f.title}</strong>
                  <small>{f.vendor} · {f.source}</small>
                </span>
                <span className="finding-value">
                  <strong>{f.amount}</strong>
                  <small>{f.confidence}% confidence</small>
                </span>
              </button>
            ))}
          </div>
        </article>

        <article className="panel">
          <PanelHeader eyebrow="Agent activity" title="Live reasoning graph" />
          {topFindings[0] && <AgentFlow path={topFindings[0].agentPath} />}
        </article>
      </section>
    </div>
  );
}