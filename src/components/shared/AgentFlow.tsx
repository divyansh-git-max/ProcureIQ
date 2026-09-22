/**
 * AgentFlow — animated hub-and-spoke agent reasoning graph.
 *
 * Upgraded with:
 * 1. Gradient connector lines
 * 2. Constant-speed flowing particles based on path length
 * 3. Interactive hover states (dimming unrelated paths)
 * 4. Semantic verdict animations based on severity
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";

// ─── Agent definitions ────────────────────────────────────────────────────────

const SPECIALIST_AGENTS = [
  {
    id: "retrieval",
    label: "Retrieval",
    tag: "RAG · Pinecone",
    icon: "🔍",
    color: "#3b82f6",
    glow: "rgba(59,130,246,0.35)",
  },
  {
    id: "websearch",
    label: "Web Search",
    tag: "Live · Serper",
    icon: "🌐",
    color: "#06b6d4",
    glow: "rgba(6,182,212,0.35)",
  },
  {
    id: "analysis",
    label: "Analysis",
    tag: "LLM · Groq",
    icon: "📊",
    color: "#f59e0b",
    glow: "rgba(245,158,11,0.35)",
  },
  {
    id: "report",
    label: "Doc Intel",
    tag: "SLM · Qwen2.5",
    icon: "📄",
    color: "#a855f7",
    glow: "rgba(168,85,247,0.35)",
  },
] as const;

const SUPERVISOR_AGENT = {
  id: "supervisor",
  label: "Supervisor",
  tag: "Orchestrator · Judge",
  icon: "⚖️",
  color: "#10b981",
  glow: "rgba(16,185,129,0.45)",
};

// ─── Particle dot that travels along an SVG path via rAF ─────────────────────

function FlowingDot({
  pathRef,
  color,
  delay,
  duration,
}: {
  pathRef: React.RefObject<SVGPathElement | null>;
  color: string;
  delay: number;
  duration: number;
}) {
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null);
  const startRef = useRef<number | null>(null);
  const frameRef = useRef<number | null>(null);

  const tick = useCallback(
    (ts: number) => {
      const el = pathRef.current;
      if (!el) return;
      if (startRef.current === null) startRef.current = ts;
      const elapsed = ts - startRef.current;
      const cycle = duration * 1000;
      const t = ((elapsed / cycle + delay) % 1);
      const len = el.getTotalLength();
      const pt  = el.getPointAtLength(t * len);
      setPos({ x: pt.x, y: pt.y });
      frameRef.current = requestAnimationFrame(tick);
    },
    [pathRef, delay, duration]
  );

  useEffect(() => {
    frameRef.current = requestAnimationFrame(tick);
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  }, [tick]);

  if (!pos) return null;
  return (
    <circle
      cx={pos.x}
      cy={pos.y}
      r={3.2}
      fill={color}
      opacity={0.9}
      style={{ filter: `drop-shadow(0 0 5px ${color})` }}
    />
  );
}

// ─── One connector line: animated draw + flowing dots ────────────────────────

function ConnectorLine({
  fromX, fromY, toX, toY, color, agentId, active, drawDelay, isDimmed, isHighlighted
}: {
  fromX: number; fromY: number; toX: number; toY: number;
  color: string; agentId: string; active: boolean; drawDelay: number;
  isDimmed: boolean; isHighlighted: boolean;
}) {
  const pathRef = useRef<SVGPathElement | null>(null);
  const [drawn, setDrawn] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setDrawn(true), drawDelay);
    return () => clearTimeout(t);
  }, [drawDelay]);

  const bendAmount = Math.max(40, Math.abs(toY - fromY) * 0.45);
  const d = `M ${fromX} ${fromY} C ${fromX} ${fromY + bendAmount}, ${toX} ${toY - bendAmount}, ${toX} ${toY}`;

  // 1. Interactive styling based on hover state
  const lineOpacity = isHighlighted ? 0.95 : isDimmed ? 0.05 : (active ? 0.75 : 0.15);
  const strokeW     = isHighlighted ? 2.5 : (active ? 2 : 1.5);
  
  // 2. Constant speed particles: scale duration by path distance
  const dist = Math.hypot(toX - fromX, toY - fromY);
  const particleDur = Math.max(1.0, (dist / 140) * 1.5); // uniform speed

  return (
    <g style={{ transition: "opacity 0.3s ease" }}>
      {/* Ghost base line */}
      <path d={d} fill="none" stroke={`url(#grad-${agentId})`} strokeWidth={1.5} strokeOpacity={lineOpacity * 0.15} />

      {/* Draw-on animated line with gradient stroke */}
      {drawn && (
        <motion.path
          ref={pathRef}
          d={d}
          fill="none"
          stroke={`url(#grad-${agentId})`}
          strokeWidth={strokeW}
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: lineOpacity }}
          transition={{ pathLength: { duration: 0.65, ease: [0.22, 1, 0.36, 1] }, opacity: { duration: 0.3 } }}
        />
      )}

      {/* Flowing particles — hide them if the line is dimmed by hovering something else */}
      {active && drawn && !isDimmed && pathRef.current && (
        <>
          <FlowingDot pathRef={pathRef} color={color} delay={0}       duration={particleDur} />
          <FlowingDot pathRef={pathRef} color={color} delay={0.33}    duration={particleDur} />
          <FlowingDot pathRef={pathRef} color={color} delay={0.66}    duration={particleDur} />
        </>
      )}
    </g>
  );
}

// ─── Agent card ───────────────────────────────────────────────────────────────

const cardVariants = {
  hidden:  { opacity: 0, y: -24, scale: 0.72 },
  visible: (custom: { isDimmed: boolean; active: boolean; isSupervisor: boolean }) => ({
    opacity: custom.isDimmed ? 0.3 : (!custom.active && !custom.isSupervisor ? 0.35 : 1),
    y: 0,
    scale: 1, // Crucial: explicitly define scale so whileHover restores properly
    filter: custom.isDimmed || (!custom.active && !custom.isSupervisor) ? "grayscale(70%)" : "grayscale(0%)",
    transition: { type: "spring" as const, stiffness: 380, damping: 24 }
  }),
};

function AgentCard({
  agent, active, isSupervisor = false, supervisorPulsed = false,
  isDimmed = false,
  onHoverStart, onHoverEnd
}: {
  agent: typeof SPECIALIST_AGENTS[number] | typeof SUPERVISOR_AGENT;
  active: boolean; isSupervisor?: boolean; supervisorPulsed?: boolean;
  isDimmed?: boolean;
  onHoverStart?: () => void; onHoverEnd?: () => void;
}) {
  return (
    <motion.div
      className={["agf-card", active ? "agf-card--active" : "agf-card--idle", isSupervisor ? "agf-card--supervisor" : ""].join(" ")}
      custom={{ isDimmed, active, isSupervisor }}
      variants={cardVariants}
      whileHover={!isSupervisor ? { y: -4, scale: 1.03 } : undefined}
      onHoverStart={onHoverStart}
      onHoverEnd={onHoverEnd}
      animate={isSupervisor ? "visible" : undefined} // Supervisor needs explicit trigger, specialists inherit
      style={{
        "--agent-color": agent.color,
        "--agent-glow": agent.glow,
        cursor: !isSupervisor ? "pointer" : "default"
      } as React.CSSProperties}
    >
      {isSupervisor && supervisorPulsed && active && (
        <motion.div
          className="agf-supervisor-ring"
          style={{ "--agent-color": agent.color } as React.CSSProperties}
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: [1, 1.28, 1.55], opacity: [0.85, 0.4, 0] }}
          transition={{ duration: 1.2, ease: "easeOut", repeat: Infinity, repeatDelay: 1.8 }}
        />
      )}

      <div className="agf-card-icon">{agent.icon}</div>
      <div className="agf-card-text">
        <span className="agf-card-name">{agent.label}</span>
        <span className="agf-card-tag">{agent.tag}</span>
      </div>
      <div className={`agf-status-dot ${active ? "agf-status-dot--active" : ""}`} />
    </motion.div>
  );
}

// ─── Main exported component ─────────────────────────────────────────────────

type AgentFlowProps = { path?: string[] };

export default function AgentFlow({ path = [] }: AgentFlowProps) {
  const wrapperRef      = useRef<HTMLDivElement | null>(null);
  const specialistRefs  = useRef<Array<HTMLDivElement | null>>([null, null, null, null]);
  const supervisorRef   = useRef<HTMLDivElement | null>(null);

  const [linesReady,      setLinesReady]      = useState(false);
  const [lineCoords,      setLineCoords]      = useState<Array<{ fromX: number; fromY: number; toX: number; toY: number }>>([]);
  const [supervisorPulsed, setSupervisorPulsed] = useState(false);
  const [outputVisible,    setOutputVisible]    = useState(false);
  
  // Hover interactivity
  const [hoveredAgent, setHoveredAgent] = useState<string | null>(null);

  const activeIds = new Set(path);
  const supervisorActive = activeIds.has("supervisor") || path.length > 0;

  useEffect(() => {
    const t1 = setTimeout(() => setLinesReady(true),       1300);
    const t2 = setTimeout(() => setSupervisorPulsed(true), 2500);
    const t3 = setTimeout(() => setOutputVisible(true),    2900);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, []);

  useEffect(() => {
    if (!linesReady) return;
    const frame = requestAnimationFrame(() => {
      const wrapper = wrapperRef.current;
      const supEl   = supervisorRef.current;
      if (!wrapper || !supEl) return;

      const wRect = wrapper.getBoundingClientRect();
      const sRect = supEl.getBoundingClientRect();

      const toX = sRect.left + sRect.width  / 2 - wRect.left;
      const toY = sRect.top                      - wRect.top;

      const coords = specialistRefs.current.map((el) => {
        if (!el) return { fromX: 0, fromY: 0, toX, toY };
        const r = el.getBoundingClientRect();
        return {
          fromX: r.left + r.width / 2 - wRect.left,
          fromY: r.bottom             - wRect.top,
          toX, toY,
        };
      });
      setLineCoords(coords);
    });
    return () => cancelAnimationFrame(frame);
  }, [linesReady]);

  const verdict      = path.includes("supervisor") ? "HITL Gated" : path.length >= 3 ? "High Risk" : "Cleared";
  const verdictColor = verdict === "High Risk" ? "#ef4444" : verdict === "HITL Gated" ? "#f59e0b" : "#10b981";

  // Semantic output variants
  const verdictVariants = {
    "High Risk": {
      initial: { opacity: 0, scale: 0.8, y: -15 },
      animate: { opacity: 1, scale: 1, y: 0, transition: { type: "spring" as const, stiffness: 600, damping: 10 } }
    },
    "HITL Gated": {
      initial: { opacity: 0, scale: 0.9 },
      animate: { opacity: 1, scale: 1, transition: { type: "spring" as const, stiffness: 350, damping: 20 } }
    },
    "Cleared": {
      initial: { opacity: 0, y: 15 },
      animate: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } }
    }
  };

  return (
    <div
      className="agf-wrapper"
      ref={wrapperRef}
      style={{
        position: "relative", // CRITICAL: keeps absolute SVG contained
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        width: "100%",
        minHeight: "280px"
      }}
    >
      <svg
        aria-hidden="true"
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          overflow: "visible",
          pointerEvents: "none",
          zIndex: 1,
        }}
      >
        <defs>
          {SPECIALIST_AGENTS.map(agent => (
            <linearGradient id={`grad-${agent.id}`} key={agent.id} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={agent.color} />
              <stop offset="100%" stopColor={SUPERVISOR_AGENT.color} />
            </linearGradient>
          ))}
        </defs>

        {linesReady && lineCoords.length === 4 && lineCoords.map((c, i) => (
          <ConnectorLine
            key={i}
            fromX={c.fromX} fromY={c.fromY} toX={c.toX} toY={c.toY}
            agentId={SPECIALIST_AGENTS[i].id}
            color={SPECIALIST_AGENTS[i].color}
            active={activeIds.has(SPECIALIST_AGENTS[i].id) || path.length === 0}
            isHighlighted={hoveredAgent === SPECIALIST_AGENTS[i].id}
            isDimmed={hoveredAgent !== null && hoveredAgent !== SPECIALIST_AGENTS[i].id}
            drawDelay={i * 100}
          />
        ))}
      </svg>

      <motion.div
        className="agf-specialists"
        style={{ position: "relative", zIndex: 2 }}
        initial="hidden"
        animate="visible"
        variants={{ visible: { transition: { staggerChildren: 0.13, delayChildren: 0.08 } } }}
      >
        {SPECIALIST_AGENTS.map((agent, i) => (
          <div key={agent.id} ref={(el) => { specialistRefs.current[i] = el; }}>
            <AgentCard
              agent={agent}
              active={activeIds.has(agent.id) || path.length === 0}
              isDimmed={hoveredAgent !== null && hoveredAgent !== agent.id}
              onHoverStart={() => setHoveredAgent(agent.id)}
              onHoverEnd={() => setHoveredAgent(null)}
            />
          </div>
        ))}
      </motion.div>

      <div className="agf-gap" style={{ height: "80px", width: "100%" }} />

      <motion.div
        className="agf-supervisor-row"
        style={{ position: "relative", zIndex: 2 }}
        initial={{ opacity: 0, scale: 0.82, y: 16 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ delay: 0.75, duration: 0.55, type: "spring", stiffness: 320, damping: 22 }}
      >
        <div ref={supervisorRef}>
          <AgentCard
            agent={SUPERVISOR_AGENT}
            active={supervisorActive}
            isSupervisor
            supervisorPulsed={supervisorPulsed}
            isDimmed={hoveredAgent !== null} // slight dim when hovering a specialist
          />
        </div>
      </motion.div>

      <AnimatePresence>
        {outputVisible && (
          <motion.div
            className="agf-output-wrap"
            style={{ position: "relative", zIndex: 2 }}
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          >
            <motion.div
              className="agf-output-arrow"
              initial={{ scaleY: 0 }}
              animate={{ scaleY: 1 }}
              style={{ transformOrigin: "top" }}
              transition={{ duration: 0.28 }}
            />
            <motion.div
              className="agf-verdict"
              style={{ "--verdict-color": verdictColor } as React.CSSProperties}
              variants={verdictVariants[verdict as keyof typeof verdictVariants]}
              initial="initial"
              animate="animate"
            >
              <span className="agf-verdict-dot" />
              <span className="agf-verdict-label">{verdict}</span>
              <span className="agf-verdict-conf">
                {path.length > 0 ? `${Math.round(72 + path.length * 4)}% conf.` : "—"}
              </span>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
}