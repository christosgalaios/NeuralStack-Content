import Link from "next/link";
import { SITE_NAME, BASE_URL, AFFILIATES } from "@/lib/config";

export default function SiteFooter() {
  return (
    <footer className="border-t" style={{ borderColor: "var(--border)", background: "var(--bg-card)" }}>
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div>
            <p className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{SITE_NAME}</p>
            <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>
              AI-powered technical content, published daily. Independent guides for engineers who ship.
            </p>
          </div>

          {/* Navigation */}
          <div>
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Navigate</p>
            <div className="flex flex-col gap-2">
              <Link href="/" className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>Home</Link>
              <Link href="/tools" className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>Recommended Tools</Link>
              <Link href="/about" className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>About</Link>
            </div>
          </div>

          {/* Resources */}
          <div>
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Resources</p>
            <div className="flex flex-col gap-2">
              <a href={`${BASE_URL}/feed.xml`} className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>RSS Feed</a>
              <a href={`${BASE_URL}/sitemap.xml`} className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>Sitemap</a>
            </div>
          </div>

          {/* Tools */}
          <div>
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Tools We Recommend</p>
            <div className="flex flex-col gap-2">
              {AFFILIATES.map((aff) => (
                <a key={aff.name} href={aff.url} target="_blank" rel="noopener sponsored" className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>
                  {aff.name}
                </a>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-10 border-t pt-6" style={{ borderColor: "var(--border)" }}>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            {SITE_NAME} contains affiliate links. We may earn a commission when you purchase through our links, at no extra cost to you. This helps support our independent content.
          </p>
        </div>
      </div>
    </footer>
  );
}
