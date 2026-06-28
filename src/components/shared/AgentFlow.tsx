const AGENT_LABELS: Record<string, string> = {
  supervisor: "Supervisor",
  retrieval: "Retrieval",
  analysis: "Analysis",
  websearch: "Web search",
  report: "Report (judge)",
};

type AgentFlowProps = {
  path?: string[];
};

export default function AgentFlow({ path = [] }: AgentFlowProps) {
  return (
    <div className="agent-flow">
      {path.map((step, i) => {
        const label = AGENT_LABELS[step as keyof typeof AGENT_LABELS] ?? step;
        return (
          <div key={step + i} className="agent-flow-step">
            <span className="agent-node">{label}</span>
            {i < path.length - 1 && <span className="agent-arrow">→</span>}
          </div>
        );
      })}
    </div>
  );
}