import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import { AnimatePresence, motion } from "framer-motion";
import { fetchVendors } from "../api/client";
import PanelHeader from "./shared/PanelHeader";
import type { Vendor } from "../types";
import { vendors as fallbackVendors } from "../mockData";

export default function VendorIntelligence() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [selected, setSelected] = useState<Vendor | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadVendors() {
      try {
        const data = await fetchVendors();
        const resolved = data.length > 0 ? data : fallbackVendors;

        if (!active) return;

        setVendors(resolved as Vendor[]);
        setSelected(resolved[0] as Vendor);
        setError(data.length > 0 ? "" : "Backend returned no vendor rows, using local demo data.");
      } catch (err) {
        if (!active) return;

        setVendors(fallbackVendors as Vendor[]);
        setSelected(fallbackVendors[0] as Vendor);
        setError(err instanceof Error ? err.message : "Failed to load vendors. Showing local demo data.");
      } finally {
        if (active) setLoading(false);
      }
    }

    loadVendors();

    return () => {
      active = false;
    };
  }, []);

  const riskLabel = useMemo(() => {
    if (!selected) return "";
    return selected.risk >= 75 ? "High risk" : selected.risk >= 50 ? "Elevated risk" : "Low risk";
  }, [selected]);

  const summary = useMemo(() => {
    if (vendors.length === 0) return { avgRisk: 0, avgOnTime: 0, totalExposure: "₹0" };

    const avgRisk = Math.round(vendors.reduce((sum, vendor) => sum + vendor.risk, 0) / vendors.length);
    const avgOnTime = Math.round(vendors.reduce((sum, vendor) => sum + vendor.onTime, 0) / vendors.length);
    const totalExposure = `₹${vendors
      .reduce((sum, vendor) => sum + Number.parseFloat(vendor.exposure.replace(/[^0-9.]/g, "")), 0)
      .toFixed(1)}L`;

    return { avgRisk, avgOnTime, totalExposure };
  }, [vendors]);

  if (loading) return <div className="loading">Loading vendor intelligence…</div>;
  if (!selected) return <div className="loading">Vendor intelligence is unavailable.</div>;
  const scoreStyle = { "--score": selected.risk } as CSSProperties;

  return (
    <div className="vendor-layout">
      {error ? <section className="panel vendor-alert">{error}</section> : null}
      <section className="panel vendor-list-panel">
        <PanelHeader eyebrow="Portfolio watchlist" title="Vendor intelligence" action={`${vendors.length} active vendors`} />
        <div className="vendor-summary-strip">
          <div>
            <span>Average risk</span>
            <strong>{summary.avgRisk}</strong>
          </div>
          <div>
            <span>On-time delivery</span>
            <strong>{summary.avgOnTime}%</strong>
          </div>
          <div>
            <span>Total exposure</span>
            <strong>{summary.totalExposure}</strong>
          </div>
        </div>
        {vendors.map((v) => (
          <button
            key={v.id}
            className={`vendor-row ${selected.id === v.id ? "active" : ""}`}
            onClick={() => setSelected(v)}
          >
            <span className="vendor-name">
              <span className="vendor-logo">{v.name.split(" ").map((w) => w[0]).slice(0, 2).join("")}</span>
              <span className="vendor-name-copy">
                <strong>{v.name}</strong>
                <small>{v.category}</small>
              </span>
            </span>
            <span className="vendor-stat-block">
              <small>Risk</small>
              <span className={`risk-number ${v.risk >= 75 ? "critical" : v.risk >= 50 ? "elevated" : "low"}`}>{v.risk}</span>
            </span>
            <span className="vendor-stat-block">
              <small>On time</small>
              <strong>{v.onTime}%</strong>
            </span>
            <span className="vendor-stat-block">
              <small>Exposure</small>
              <strong>{v.exposure}</strong>
            </span>
          </button>
        ))}
      </section>

      <section className="panel vendor-profile">
        <AnimatePresence mode="wait">
          <motion.div
            key={selected.id}
            className="vendor-profile-inner"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
          >
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

            <div className="vendor-metrics">
              <div className="vendor-metric">
                <span>Risk trend</span>
                <strong className={selected.trend >= 0 ? "metric-up" : "metric-down"}>{selected.trend >= 0 ? "+" : ""}{selected.trend}</strong>
                <small>week over week</small>
              </div>
              <div className="vendor-metric">
                <span>On-time</span>
                <strong>{selected.onTime}%</strong>
                <small>delivery reliability</small>
              </div>
              <div className="vendor-metric">
                <span>Anomalies</span>
                <strong>{selected.anomalies}</strong>
                <small>historical flags</small>
              </div>
              <div className="vendor-metric">
                <span>Exposure</span>
                <strong>{selected.exposure}</strong>
                <small>open risk value</small>
              </div>
            </div>

            <div className="risk-score-hero">
              <div className="score-ring" style={scoreStyle}>
                <div><strong>{selected.risk}</strong><span>/ 100</span></div>
              </div>
              <div>
                <span>Composite vendor risk</span>
                <h3>{riskLabel}</h3>
                <p>Derived from delivery delays, invoice anomalies, contract compliance, and reputation signals.</p>
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
          </motion.div>
        </AnimatePresence>
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
              <CartesianGrid stroke="var(--line)" vertical={false} />
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