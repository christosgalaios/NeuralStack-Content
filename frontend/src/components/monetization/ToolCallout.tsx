interface ToolCalloutProps {
  name: string;
  url: string;
  description: string;
}

export default function ToolCallout({ name, url, description }: ToolCalloutProps) {
  return (
    <aside
      className="my-8 rounded-xl border p-5"
      style={{
        background: "linear-gradient(135deg, var(--bg-card), var(--bg-elevated))",
        borderColor: "var(--border)",
        borderLeft: "3px solid var(--accent-cta)",
      }}
    >
      <div className="flex items-start gap-3">
        <div
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-xs font-bold text-white"
          style={{ background: "var(--accent-cta)" }}
        >
          {name[0]}
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-wider" style={{ color: "var(--accent-cta)" }}>
            Recommended
          </p>
          <p className="mt-1 font-semibold" style={{ color: "var(--text-primary)" }}>{name}</p>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>{description}</p>
          <a
            href={url}
            target="_blank"
            rel="noopener sponsored"
            className="mt-3 inline-flex items-center gap-1 text-sm font-medium"
            style={{ color: "var(--accent-cta)" }}
            data-affiliate={name}
            data-position="in-article-callout"
          >
            Try {name} free &rarr;
          </a>
        </div>
      </div>
    </aside>
  );
}
