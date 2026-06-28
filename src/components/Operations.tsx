import { useEffect, useState } from "react";
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import { fetchOperations } from "../api/client";
import PanelHeader from "./shared/PanelHeader";
import type { OperationsData } from "../types";

export default function Operations() {
  const [data, setData] = useState<OperationsData | null>(null);

  useEffect(() => {
    fetchOperations().then(setData);
  }, []);

  if (!data) return <div className="loading">Loading operations…</div>;

  return (
    <div className="stack">
      <section className="health-banner">
        <h2>All critical services operational</h2>
        <p>Last incident 11 days ago</p>
      </section>

      <section className="kpi-grid">
        {data.slos.map((slo) => (
          <article key={slo.label} className="kpi-card">
            <div className="kpi-label">{slo.label}</div>
            <strong>{slo.value}</strong>
            <small>SLO target {slo.target}</small>
          </article>
        ))}
      </section>

      <section className="grid-2">
        <article className="panel span-2">
          <PanelHeader eyebrow="Performance" title="End-to-end latency" action="Last 6 hours" />
          <ResponsiveContainer width="100%" height={210}>
            <LineChart data={data.latencyData}>
              <CartesianGrid stroke="var(--color-border-tertiary)" vertical={false} />
              <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 11 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Line type="monotone" dataKey="p50" stroke="#378ADD" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="p95" stroke="#7F77DD" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </article>
      </section>

      <section className="grid-2">
        <article className="panel">
          <PanelHeader eyebrow="Layer 1 — output quality" title="Ragas evaluation" action="30 test cases" />
          <div className="quality-grid">
            {data.ragasMetrics.map((m) => (
              <div className="quality-metric" key={m.label}>
                <div><span>{m.label}</span><strong>{m.value}%</strong></div>
                <div className="quality-track"><span style={{ width: `${m.value}%` }} /></div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <PanelHeader eyebrow="Layer 3 — trajectory" title="Agent routing correctness" action="Per intent type" />
          <div className="trajectory-table">
            {data.trajectoryEval.map((t) => (
              <div key={t.intent} className="trajectory-row">
                <div>
                  <strong>{t.intent}</strong>
                  <small>{t.actual.join(" → ")}</small>
                </div>
                <span className={t.correctRoute ? "trace-status success" : "trace-status retried"}>
                  {t.correctRoute ? "Correct route" : "Route deviation"}
                </span>
                <small>{t.efficiency}% efficient</small>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="panel">
        <PanelHeader eyebrow="OpenTelemetry-style traces" title="Recent agent runs" action="LangSmith" />
        <div className="trace-list">
          {data.traces.map((t) => (
            <div className="trace-row" key={t.id}>
              <code>{t.id}</code>
              <span><strong>{t.action}</strong></span>
              <span>{t.duration}</span>
              <span className={`trace-status ${t.status.toLowerCase()}`}>{t.status}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="panel">
        <PanelHeader eyebrow="Structured logs" title="Live event stream" />
        <div className="log-stream">
          {data.guardrailLog.map((log, i) => (
            <code key={i}>
              <span>{log.time}</span>
              <b className={log.level.toLowerCase()}>{log.level}</b>
              <em>{log.source}</em>
              {log.message}
            </code>
          ))}
        </div>
      </section>
    </div>
  );
}