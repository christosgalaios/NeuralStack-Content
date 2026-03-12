import Link from "next/link";
import { SITE_NAME, BASE_URL, AFFILIATES, CATEGORY_META } from "@/lib/config";
import { getAllCategories } from "@/lib/articles";

export default function SiteFooter() {
  return (
    <footer className="border-t" style={{ borderColor: "var(--border)", background: "var(--bg-card)" }}>
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
          <div>
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Navigate</p>
            <div className="flex flex-col gap-2">
              <Link href="/" className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>Home</Link>
              <Link href="/tools" className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>Recommended Tools</Link>
              <Link href="/about" className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>About</Link>
            </div>
          </div>

          {/* Categories */}
          <div>
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Categories</p>
            <div className="flex flex-col gap-2">
              {getAllCategories().map((cat) => {
                const meta = CATEGORY_META[cat];
                return (
                  <Link key={cat} href={`/category/${cat}`} className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>
                    {meta?.display || cat}
                  </Link>
                );
              })}
              <a href={`${BASE_URL}/feed.xml`} className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-muted)" }}>RSS Feed</a>
              <a href={`${BASE_URL}/sitemap.xml`} className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-muted)" }}>Sitemap</a>
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
          <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
            &copy; {new Date().getFullYear()} {SITE_NAME}. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
