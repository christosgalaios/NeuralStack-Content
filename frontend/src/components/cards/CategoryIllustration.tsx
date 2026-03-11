// Abstract geometric SVG illustrations per category
// Designed for dark tech aesthetic — transparent bg, works in both themes

const COLORS: Record<string, { primary: string; secondary: string; glow: string }> = {
  guide:         { primary: "#64748b", secondary: "#94a3b8", glow: "rgba(100,116,139,0.15)" },
  review:        { primary: "#f59e0b", secondary: "#fbbf24", glow: "rgba(245,158,11,0.15)" },
  comparison:    { primary: "#3b82f6", secondary: "#60a5fa", glow: "rgba(59,130,246,0.15)" },
  compatibility: { primary: "#8b5cf6", secondary: "#a78bfa", glow: "rgba(139,92,246,0.15)" },
  tutorial:      { primary: "#22c55e", secondary: "#4ade80", glow: "rgba(34,197,94,0.15)" },
  news:          { primary: "#ef4444", secondary: "#f87171", glow: "rgba(239,68,68,0.15)" },
};

function GuideSVG({ p, s }: { p: string; s: string }) {
  return (
    <svg viewBox="0 0 400 200" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-full w-full">
      {/* Roadmap/path with circuit nodes */}
      <line x1="40" y1="100" x2="360" y2="100" stroke={p} strokeWidth="2" opacity="0.3" strokeDasharray="8 4" />
      {/* Nodes along the path */}
      <circle cx="80" cy="100" r="12" stroke={p} strokeWidth="2" fill="none" opacity="0.5" />
      <circle cx="80" cy="100" r="5" fill={p} opacity="0.6" />
      <circle cx="170" cy="100" r="16" stroke={s} strokeWidth="2" fill="none" opacity="0.4" />
      <circle cx="170" cy="100" r="7" fill={s} opacity="0.5" />
      <circle cx="270" cy="100" r="12" stroke={p} strokeWidth="2" fill="none" opacity="0.5" />
      <circle cx="270" cy="100" r="5" fill={p} opacity="0.6" />
      <circle cx="350" cy="100" r="18" stroke={s} strokeWidth="2.5" fill="none" opacity="0.6" />
      <polygon points="343,95 358,100 343,105" fill={s} opacity="0.7" />
      {/* Branch lines */}
      <line x1="80" y1="88" x2="80" y2="55" stroke={p} strokeWidth="1.5" opacity="0.3" />
      <circle cx="80" cy="50" r="6" stroke={p} strokeWidth="1.5" fill="none" opacity="0.3" />
      <line x1="170" y1="84" x2="170" y2="45" stroke={s} strokeWidth="1.5" opacity="0.25" />
      <rect x="160" y="35" width="20" height="12" rx="3" stroke={s} strokeWidth="1.5" fill="none" opacity="0.3" />
      <line x1="270" y1="112" x2="270" y2="150" stroke={p} strokeWidth="1.5" opacity="0.3" />
      <circle cx="270" cy="156" r="6" stroke={p} strokeWidth="1.5" fill="none" opacity="0.3" />
      {/* Decorative dots */}
      <circle cx="125" cy="100" r="2" fill={p} opacity="0.3" />
      <circle cx="220" cy="100" r="2" fill={s} opacity="0.3" />
      <circle cx="310" cy="100" r="2" fill={p} opacity="0.3" />
    </svg>
  );
}

function ReviewSVG({ p, s }: { p: string; s: string }) {
  return (
    <svg viewBox="0 0 400 200" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-full w-full">
      {/* Magnifying glass */}
      <circle cx="160" cy="95" r="45" stroke={p} strokeWidth="2.5" fill="none" opacity="0.4" />
      <circle cx="160" cy="95" r="35" stroke={s} strokeWidth="1.5" fill="none" opacity="0.2" />
      <line x1="193" y1="128" x2="225" y2="160" stroke={p} strokeWidth="3" strokeLinecap="round" opacity="0.5" />
      {/* Data points inside lens */}
      <rect x="138" y="78" width="44" height="6" rx="3" fill={s} opacity="0.4" />
      <rect x="138" y="90" width="32" height="6" rx="3" fill={p} opacity="0.3" />
      <rect x="138" y="102" width="38" height="6" rx="3" fill={s} opacity="0.35" />
      {/* Star rating */}
      <g opacity="0.5" transform="translate(260, 70)">
        {[0, 1, 2, 3, 4].map((i) => (
          <polygon
            key={i}
            points="12,2 15,10 23,10 17,15 19,23 12,18 5,23 7,15 1,10 9,10"
            fill={i < 4 ? p : "none"}
            stroke={i < 4 ? p : s}
            strokeWidth="1"
            opacity={i < 4 ? 0.6 : 0.3}
            transform={`translate(${i * 26}, 0) scale(0.8)`}
          />
        ))}
      </g>
      {/* Score bar */}
      <rect x="260" y="110" width="100" height="8" rx="4" stroke={p} strokeWidth="1" fill="none" opacity="0.3" />
      <rect x="260" y="110" width="78" height="8" rx="4" fill={p} opacity="0.4" />
      <rect x="260" y="128" width="100" height="8" rx="4" stroke={s} strokeWidth="1" fill="none" opacity="0.25" />
      <rect x="260" y="128" width="62" height="8" rx="4" fill={s} opacity="0.3" />
    </svg>
  );
}

function ComparisonSVG({ p, s }: { p: string; s: string }) {
  return (
    <svg viewBox="0 0 400 200" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-full w-full">
      {/* Left panel */}
      <rect x="40" y="30" width="140" height="140" rx="8" stroke={p} strokeWidth="2" fill="none" opacity="0.3" />
      <rect x="55" y="50" width="60" height="8" rx="4" fill={p} opacity="0.4" />
      <rect x="55" y="68" width="110" height="5" rx="2.5" fill={s} opacity="0.2" />
      <rect x="55" y="80" width="95" height="5" rx="2.5" fill={s} opacity="0.15" />
      <rect x="55" y="92" width="105" height="5" rx="2.5" fill={s} opacity="0.2" />
      <circle cx="75" cy="130" r="20" stroke={p} strokeWidth="2" fill="none" opacity="0.3" />
      <text x="68" y="136" fontSize="16" fontWeight="700" fill={p} opacity="0.5" fontFamily="Inter, sans-serif">A</text>
      {/* VS divider */}
      <line x1="200" y1="40" x2="200" y2="160" stroke={s} strokeWidth="1" opacity="0.2" strokeDasharray="4 4" />
      <circle cx="200" cy="100" r="16" stroke={s} strokeWidth="1.5" fill="none" opacity="0.3" />
      <text x="189" y="106" fontSize="12" fontWeight="600" fill={s} opacity="0.5" fontFamily="Inter, sans-serif">VS</text>
      {/* Right panel */}
      <rect x="220" y="30" width="140" height="140" rx="8" stroke={s} strokeWidth="2" fill="none" opacity="0.3" />
      <rect x="235" y="50" width="55" height="8" rx="4" fill={s} opacity="0.4" />
      <rect x="235" y="68" width="100" height="5" rx="2.5" fill={p} opacity="0.2" />
      <rect x="235" y="80" width="110" height="5" rx="2.5" fill={p} opacity="0.15" />
      <rect x="235" y="92" width="90" height="5" rx="2.5" fill={p} opacity="0.2" />
      <circle cx="325" cy="130" r="20" stroke={s} strokeWidth="2" fill="none" opacity="0.3" />
      <text x="318" y="136" fontSize="16" fontWeight="700" fill={s} opacity="0.5" fontFamily="Inter, sans-serif">B</text>
    </svg>
  );
}

function CompatibilitySVG({ p, s }: { p: string; s: string }) {
  return (
    <svg viewBox="0 0 400 200" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-full w-full">
      {/* Interlocking gears */}
      <g opacity="0.45">
        {/* Large gear */}
        <circle cx="150" cy="100" r="40" stroke={p} strokeWidth="2" fill="none" />
        <circle cx="150" cy="100" r="30" stroke={p} strokeWidth="1" fill="none" opacity="0.5" />
        <circle cx="150" cy="100" r="8" fill={p} opacity="0.4" />
        {/* Gear teeth */}
        {[0, 45, 90, 135, 180, 225, 270, 315].map((angle) => {
          const rad = (angle * Math.PI) / 180;
          const x1 = 150 + 38 * Math.cos(rad);
          const y1 = 100 + 38 * Math.sin(rad);
          const x2 = 150 + 48 * Math.cos(rad);
          const y2 = 100 + 48 * Math.sin(rad);
          return <line key={angle} x1={x1} y1={y1} x2={x2} y2={y2} stroke={p} strokeWidth="6" strokeLinecap="round" />;
        })}
      </g>
      <g opacity="0.35">
        {/* Small gear — interlocked */}
        <circle cx="250" cy="90" r="28" stroke={s} strokeWidth="2" fill="none" />
        <circle cx="250" cy="90" r="20" stroke={s} strokeWidth="1" fill="none" opacity="0.5" />
        <circle cx="250" cy="90" r="6" fill={s} opacity="0.4" />
        {[0, 60, 120, 180, 240, 300].map((angle) => {
          const rad = (angle * Math.PI) / 180;
          const x1 = 250 + 26 * Math.cos(rad);
          const y1 = 90 + 26 * Math.sin(rad);
          const x2 = 250 + 35 * Math.cos(rad);
          const y2 = 90 + 35 * Math.sin(rad);
          return <line key={angle} x1={x1} y1={y1} x2={x2} y2={y2} stroke={s} strokeWidth="5" strokeLinecap="round" />;
        })}
      </g>
      {/* Connection lines */}
      <line x1="290" y1="90" x2="340" y2="90" stroke={s} strokeWidth="1.5" opacity="0.25" strokeDasharray="6 3" />
      <circle cx="350" cy="90" r="10" stroke={s} strokeWidth="1.5" fill="none" opacity="0.25" />
      {/* Checkmarks */}
      <path d="M345 90 L349 94 L356 85" stroke={s} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity="0.4" />
    </svg>
  );
}

function TutorialSVG({ p, s }: { p: string; s: string }) {
  return (
    <svg viewBox="0 0 400 200" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-full w-full">
      {/* Terminal window */}
      <rect x="60" y="25" width="280" height="150" rx="8" stroke={p} strokeWidth="2" fill="none" opacity="0.35" />
      {/* Title bar */}
      <line x1="60" y1="50" x2="340" y2="50" stroke={p} strokeWidth="1" opacity="0.2" />
      <circle cx="80" cy="38" r="4" fill="#ef4444" opacity="0.4" />
      <circle cx="95" cy="38" r="4" fill="#f59e0b" opacity="0.4" />
      <circle cx="110" cy="38" r="4" fill={p} opacity="0.4" />
      {/* Terminal lines */}
      <text x="80" y="75" fontSize="11" fill={s} opacity="0.5" fontFamily="JetBrains Mono, monospace">$</text>
      <rect x="95" y="65" width="90" height="12" rx="2" fill={p} opacity="0.25" />
      <text x="80" y="97" fontSize="11" fill={s} opacity="0.5" fontFamily="JetBrains Mono, monospace">$</text>
      <rect x="95" y="87" width="140" height="12" rx="2" fill={s} opacity="0.15" />
      <text x="80" y="119" fontSize="11" fill={p} opacity="0.4" fontFamily="JetBrains Mono, monospace">&gt;</text>
      <rect x="95" y="109" width="70" height="12" rx="2" fill={p} opacity="0.3" />
      {/* Cursor blink */}
      <rect x="170" y="109" width="8" height="12" fill={s} opacity="0.5" />
      {/* Step indicators on the right */}
      <g transform="translate(355, 55)">
        {[0, 1, 2].map((i) => (
          <g key={i} transform={`translate(0, ${i * 38})`}>
            <circle cx="0" cy="10" r="8" stroke={i < 2 ? p : s} strokeWidth="1.5" fill={i < 2 ? p : "none"} opacity={i < 2 ? 0.4 : 0.2} />
            <text x="-3" y="14" fontSize="10" fill={i < 2 ? "#fff" : s} opacity={i < 2 ? 0.8 : 0.3} fontFamily="Inter, sans-serif">{i + 1}</text>
            {i < 2 && <line x1="0" y1="20" x2="0" y2="32" stroke={p} strokeWidth="1" opacity="0.2" />}
          </g>
        ))}
      </g>
    </svg>
  );
}

function NewsSVG({ p, s }: { p: string; s: string }) {
  return (
    <svg viewBox="0 0 400 200" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-full w-full">
      {/* Broadcast tower */}
      <polygon points="200,30 185,170 215,170" stroke={p} strokeWidth="2" fill="none" opacity="0.35" />
      <line x1="190" y1="110" x2="210" y2="110" stroke={p} strokeWidth="1.5" opacity="0.3" />
      <line x1="193" y1="80" x2="207" y2="80" stroke={p} strokeWidth="1.5" opacity="0.3" />
      <circle cx="200" cy="45" r="5" fill={p} opacity="0.5" />
      {/* Signal waves */}
      {[30, 50, 70].map((r, i) => (
        <path
          key={r}
          d={`M ${200 - r} ${45 - r * 0.3} A ${r} ${r} 0 0 1 ${200 + r} ${45 - r * 0.3}`}
          stroke={s}
          strokeWidth="1.5"
          fill="none"
          opacity={0.4 - i * 0.1}
        />
      ))}
      {/* Left signal */}
      {[25, 40, 55].map((r, i) => (
        <path
          key={r}
          d={`M ${200 - r * 0.3} ${45 + r * 0.2} A ${r} ${r} 0 0 0 ${200 - r} ${45 - r * 0.5}`}
          stroke={p}
          strokeWidth="1.5"
          fill="none"
          opacity={0.35 - i * 0.08}
        />
      ))}
      {/* Floating data fragments */}
      <rect x="60" y="60" width="50" height="6" rx="3" fill={s} opacity="0.2" />
      <rect x="55" y="75" width="35" height="6" rx="3" fill={p} opacity="0.15" />
      <rect x="290" y="55" width="45" height="6" rx="3" fill={s} opacity="0.2" />
      <rect x="300" y="70" width="40" height="6" rx="3" fill={p} opacity="0.15" />
      {/* Pulse dots */}
      <circle cx="100" cy="50" r="3" fill={p} opacity="0.3" />
      <circle cx="310" cy="45" r="3" fill={s} opacity="0.3" />
      <circle cx="80" cy="95" r="2" fill={s} opacity="0.2" />
      <circle cx="330" cy="90" r="2" fill={p} opacity="0.2" />
    </svg>
  );
}

export default function CategoryIllustration({
  category,
  className = "",
}: {
  category: string;
  className?: string;
}) {
  const colors = COLORS[category] || COLORS.guide;
  const { primary: p, secondary: s } = colors;

  return (
    <div className={className} aria-hidden="true">
      {category === "guide" && <GuideSVG p={p} s={s} />}
      {category === "review" && <ReviewSVG p={p} s={s} />}
      {category === "comparison" && <ComparisonSVG p={p} s={s} />}
      {category === "compatibility" && <CompatibilitySVG p={p} s={s} />}
      {category === "tutorial" && <TutorialSVG p={p} s={s} />}
      {category === "news" && <NewsSVG p={p} s={s} />}
      {/* Fallback — use guide illustration for unknown categories */}
      {!COLORS[category] && <GuideSVG p={p} s={s} />}
    </div>
  );
}

export { COLORS as CATEGORY_COLORS };
