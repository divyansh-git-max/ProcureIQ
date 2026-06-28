import { useEffect, useState, type CSSProperties } from "react";
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import { fetchVendors } from "../api/client";
import PanelHeader from "./shared/PanelHeader";
import type { Vendor } from "../types";

export default function VendorIntelligence() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [selected, setSelected] = useState<Vendor | null>(null);

  useEffect(() => {
    fetchVendors().then((data) => {
      setVendors(data);
      setSelected(data[0]);
    });
  }, []);

  if (!selected) return <div className="loading">Loading vendor intelligence…</div>;

  const riskLabel = selected.risk >= 75 ? "High risk" : selected.risk >= 50 ? "Elevated risk" : "Low risk";
  const scoreStyle = { "--score": selected.risk } as CSSProperties;

  return (
    <div className="vendor-layout">
      <section className="panel vendor-list-panel">
        <div className="vendor-table-head">
          <span>Vendor</span><span>Risk</span><span>On time</span><span>Exposure</span>
        </div>
        {vendors.map((v) => (
          <button
            key={v.id}
            className={`vendor-row ${selected.id === v.id ? "active" : ""}`}
            onClick={() => setSelected(v)}
          >
            <span className="vendor-name">
              <span className="vendor-logo">{v.name.split(" ").map((w) => w[0]).slice(0, 2).join("")}</span>
              <span>
                <strong>{v.name}</strong>
                <small>{v.category}</small>
              </span>
            </span>
            <span className={`risk-number ${v.risk >= 75 ? "critical" : v.risk >= 50 ? "elevated" : "low"}`}>{v.risk}</span>
            <span>{v.onTime}%</span>
            <span>{v.exposure}</span>
          </button>
        ))}
      </section>

      <section className="panel vendor-profile">
        <div className="vendor-profile-head">
          <div className="vendor-logo vendor-logo--large">
            {selected.name.split(" ").map((w) => w[0]).slice(0, 2).join("")}
          </div>
          <div>
            <span>Vendor risk profile</span>
            <h2>{selected.name}</h2>
            <p>{selected.category}</p>
          </div>
        </div>

        <div className="risk-score-hero">
          <div className="score-ring" style={scoreStyle}>
            <div><strong>{selected.risk}</strong><span>/ 100</span></div>
          </div>
          <div>
            <span>Composite vendor risk</span>
            <h3>{riskLabel}</h3>
          </div>
        </div>

        <div className="risk-formula">
          <span>Risk score</span>
          <code>0.35D + 0.30A + 0.20C + 0.15R - δ</code>
        </div>

        <div className="risk-parts">
          {selected.riskParts.map((part) => (
            <div key={part.label}>
              <div>
                <span>{part.label} <small>{part.weight} weight</small></span>
                <strong>{part.value}</strong>
              </div>
              <div className="risk-bar-track"><span style={{ width: `${part.value}%` }} /></div>
            </div>
          ))}
        </div>
      </section>

      <section className="panel span-full">
        <PanelHeader eyebrow="Predictive signal" title="Expected delivery delay" action="Model: XGBoost v2.4" />
        <div className="forecast-content">
          <div className="forecast-copy">
            <span>Next 30 days</span>
            <strong>{selected.expectedDelayDays} days</strong>
            <p>Predicted average delay. Confidence interval: {selected.confidenceInterval}.</p>
            <span className="forecast-flag">{selected.posAtRisk} purchase orders at risk</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={selected.forecast}>
              <CartesianGrid stroke="var(--color-border-tertiary)" vertical={false} />
              <XAxis dataKey="week" axisLine={false} tickLine={false} tick={{ fontSize: 11 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Line type="monotone" dataKey="actual" stroke="#888780" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="predicted" stroke="#EF9F27" strokeWidth={2} strokeDasharray="5 4" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}