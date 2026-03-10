interface ToolCardProps {
  name: string;
  url: string;
  description: string;
  tagline: string;
}

export default function ToolCard({ name, url, description, tagline }: ToolCardProps) {
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener sponsored"
      className="tool-card-hover group flex flex-col rounded-xl border p-6 hover:-translate-y-0.5"
      style={{ background: "var(--bg-card)", borderColor: "var(--border)" }}
      data-affiliate={name}
      data-position="tool-card"
    >
      <div className="flex items-center gap-3">
        <div
          className="flex h-10 w-10 items-center justify-center rounded-lg text-sm font-bold text-white"
          style={{ background: "var(--accent-cta)" }}
        >
          {name[0]}
        </div>
        <div>
          <p className="font-semibold" style={{ color: "var(--text-primary)" }}>{name}</p>
          <p className="text-xs" style={{ color: "var(--accent-cta)" }}>{tagline}</p>
        </div>
      </div>
      <p className="mt-3 flex-1 text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
        {description}
      </p>
      <div
        className="mt-4 inline-flex items-center gap-1 text-sm font-medium transition-colors"
        style={{ color: "var(--accent-cta)" }}
      >
        Try {name} free
        <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" className="transition-transform group-hover:translate-x-0.5">
          <path d="M5 12h14M12 5l7 7-7 7" />
        </svg>
      </div>
    </a>
  );
}
