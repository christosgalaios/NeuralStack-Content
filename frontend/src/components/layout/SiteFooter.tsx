import Link from "next/link";
import { SITE_NAME, BASE_URL, AFFILIATES, CATEGORY_META } from "@/lib/config";
import { getAllCategories } from "@/lib/articles";

export default function SiteFooter() {
  return (
    <footer className="border-t" style={{ borderColor: "var(--border)", background: "var(--bg-card)" }} role="contentinfo">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div>
            <p className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{SITE_NAME}</p>
            <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>
              Independent technical guides for engineers who ship. Updated daily.
            </p>
          </div>

          {/* Navigation */}
          <nav aria-label="Footer navigation">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Navigate</p>
            <ul className="flex flex-col gap-2 list-none p-0 m-0">
              <li><Link href="/" className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>Home</Link></li>
              <li><Link href="/tools" className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>Recommended Tools</Link></li>
              <li><Link href="/about" className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>About</Link></li>
            </ul>
          </nav>

          {/* Categories */}
          <nav aria-label="Categories">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Categories</p>
            <ul className="flex flex-col gap-2 list-none p-0 m-0">
              {getAllCategories().map((cat) => {
                const meta = CATEGORY_META[cat];
                return (
                  <li key={cat}><Link href={`/category/${cat}`} className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>
                    {meta?.display || cat}
                  </Link></li>
                );
              })}
              <li><a href={`${BASE_URL}/feed.xml`} className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-muted)" }}>RSS Feed</a></li>
              <li><a href={`${BASE_URL}/sitemap.xml`} className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-muted)" }}>Sitemap</a></li>
            </ul>
          </nav>

          {/* Tools */}
          <div>
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Tools We Recommend</p>
            <ul className="flex flex-col gap-2 list-none p-0 m-0">
              {AFFILIATES.map((aff) => (
                <li key={aff.name}><a href={aff.url} target="_blank" rel="noopener sponsored" className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>
                  {aff.name}
                </a></li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-10 border-t pt-6" style={{ borderColor: "var(--border)" }}>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            {SITE_NAME} contains affiliate links. We may earn a commission when you purchase through our links, at no extra cost to you. This helps support our independent content.
          </p>
          <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
            &copy; {new Date().getFullYear()} {SITE_NAME}. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
