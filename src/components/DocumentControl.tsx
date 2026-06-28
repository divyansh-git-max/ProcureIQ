import { useEffect, useState } from "react";
import { fetchDocuments, uploadDocument } from "../api/client";
import { useApp } from "../context/AppContext";
import type { DocumentData } from "../types";

export default function DocumentControl() {
  const { roleInfo } = useApp();
  const [docs, setDocs] = useState<DocumentData["documents"]>([]);
  const [pipeline, setPipeline] = useState<DocumentData["pipeline"]>([]);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchDocuments().then((data) => {
      setDocs(data.documents);
      setPipeline(data.pipeline);
    });
  }, []);

  async function handleUpload() {
    setUploading(true);
    await uploadDocument(new File([""], "mock-file.pdf", { type: "application/pdf" }));
    setUploading(false);
  }

  return (
    <div className="documents-layout">
      <section className="upload-card">
        <div>
          <span>Secure ingestion</span>
          <h2>Drop procurement documents here</h2>
          <p>PDF, DOCX, PNG or JPG · Guardrails run before processing</p>
        </div>
        <button onClick={handleUpload} disabled={!roleInfo || roleInfo.scope === "aggregated"}>
          {uploading ? "Scanning guardrails…" : "Choose files"}
        </button>
        <div className="guardrail-row">
          <span>File validation</span>
          <span>PII detection (Presidio)</span>
          <span>Prompt injection scan</span>
        </div>
      </section>

      <section className="panel">
        <div className="document-table-head">
          <h2>Ingestion activity</h2>
          <p>{roleInfo.scope === "documents" ? "Gatekeeper controls enabled" : "Read-only activity view"}</p>
        </div>
        <div className="document-table">
          <div className="document-row header">
            <span>Document</span><span>Type</span><span>Status</span><span>Pipeline</span><span>Received</span>
          </div>
          {docs.map((d) => (
            <div className="document-row" key={d.name}>
              <span><strong>{d.name}</strong><small>{d.vendor}</small></span>
              <span>{d.type}</span>
              <span><span className={`doc-status doc-status--${d.status.toLowerCase()}`}>{d.status}</span></span>
              <span>{d.pipeline === "vlm" ? "VLM + LayoutLM" : d.pipeline === "ocr" ? "OCR" : "Blocked"}</span>
              <span>{d.time}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="pipeline-strip">
        {pipeline.map((step) => (
          <div key={step.id} className={`pipeline-step ${step.state}`}>
            <strong>{step.label}</strong>
            <small>{step.metric}</small>
          </div>
        ))}
      </section>
    </div>
  );
}