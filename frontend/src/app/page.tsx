import { getAllArticles, getAllCategories, getAllTags } from "@/lib/articles";
import { SITE_NAME, SITE_DESCRIPTION, BASE_URL, CATEGORY_META, AFFILIATES } from "@/lib/config";
import ArticleCard from "@/components/cards/ArticleCard";
import AdSlot from "@/components/monetization/AdSlot";
import HeroCompass from "@/components/layout/HeroCompass";
import Link from "next/link";

export default function HomePage() {
  const articles = getAllArticles();
  const categories = getAllCategories();
  const tags = getAllTags().slice(0, 20);
  const featured = articles.slice(0, 6);
  const recent = articles.slice(6, 18);

  return (
    <div className="animate-in">
      {/* Hero */}
      <section className="flex flex-col items-center gap-6 py-8 sm:flex-row sm:gap-8 sm:py-12">
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl" style={{ color: "var(--text-primary)" }}>
            Pick the right dev tools &mdash; skip the research rabbit hole
          </h1>
          <p className="mt-2 text-base" style={{ color: "var(--text-muted)" }}>
            Honest comparisons, compatibility guides, and hands-on reviews of the tools engineers actually use.
          </p>
          <div className="mt-4">
            <Link
              href="/tools"
              className="inline-block rounded-lg px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:opacity-90"
              style={{ background: "var(--accent-cta)" }}
            >
              See Recommended Tools &rarr;
            </Link>
          </div>
        </div>
        <HeroCompass />
      </section>

      {/* Main content + sidebar layout */}
      <div className="lg:grid lg:grid-cols-[1fr_280px] lg:gap-10">
        {/* Main column */}
        <div>
          {/* Featured Articles Grid */}
          {featured.length > 0 && (
            <div className="grid gap-5 sm:grid-cols-2">
              {featured.map((article) => (
                <ArticleCard key={article.slug} article={article} />
              ))}
            </div>
          )}

          {/* Tools promotion */}
          <section className="my-8 grid gap-4 sm:grid-cols-2">
            {AFFILIATES.map((aff) => (
              <div
                key={aff.name}
                className="rounded-xl border p-5"
                style={{ background: "var(--bg-card)", borderColor: "var(--border)" }}
              >
                <p className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>{aff.name}</p>
                <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>{aff.tagline}</p>
                <a
                  href={aff.url}
                  target="_blank"
                  rel="noopener sponsored"
                  className="mt-3 inline-block rounded-lg px-4 py-2 text-xs font-semibold text-white transition-colors hover:opacity-90"
                  style={{ background: "var(--accent-cta)" }}
                >
                  {aff.name === "Vultr" ? "Get $300 Free Credit \u2192" : "Deploy for Free \u2192"}
                </a>
              </div>
            ))}
          </section>

          <AdSlot position="in-feed" className="my-8" />

          {/* Recent Articles List */}
          {recent.length > 0 && (
            <section className="mt-8">
              <h2 className="mb-4 text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                More Articles
              </h2>
              <div className="flex flex-col gap-1">
                {recent.map((article) => {
                  const catMeta = CATEGORY_META[article.category];
                  return (
                    <Link
                      key={article.slug}
                      href={`/articles/${article.slug}`}
                      className="group flex items-center gap-3 rounded-lg px-3 py-3 transition-colors"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      <span
                        className="shrink-0 text-xs font-medium"
                        style={{ color: "var(--text-muted)", minWidth: "5rem" }}
                      >
                        {article.date_published}
                      </span>
                      <span
                        className="font-medium transition-colors group-hover:underline"
                        style={{ color: "var(--text-primary)" }}
                      >
                        {article.title}
                      </span>
                    </Link>
                  );
                })}
              </div>
            </section>
          )}
        </div>

        {/* Sidebar */}
        <aside className="mt-10 lg:mt-0">
          <div className="sticky top-20 flex flex-col gap-6">
            {/* Categories */}
            {categories.length > 0 && (
              <div
                className="rounded-xl border p-5"
                style={{ background: "var(--bg-card)", borderColor: "var(--border)" }}
              >
                <h3 className="mb-3 text-sm font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                  Categories
                </h3>
                <div className="flex flex-col gap-1">
                  {categories.map((cat) => {
                    const meta = CATEGORY_META[cat];
                    return (
                      <Link
                        key={cat}
                        href={`/category/${cat}`}
                        className="rounded px-2 py-1.5 text-sm transition-colors hover:underline"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {meta?.display || cat}
                      </Link>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Trending Tags */}
            {tags.length > 0 && (
              <div
                className="rounded-xl border p-5"
                style={{ background: "var(--bg-card)", borderColor: "var(--border)" }}
              >
                <h3 className="mb-3 text-sm font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                  Trending Tags
                </h3>
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag) => (
                    <Link
                      key={tag}
                      href={`/tag/${tag}`}
                      className="rounded-full border px-2.5 py-1 text-xs transition-colors hover:border-[#1a9aaa]/40"
                      style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}
                    >
                      {tag}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            <AdSlot position="sidebar" />
          </div>
        </aside>
      </div>

      {articles.length === 0 && (
        <p className="py-16 text-center" style={{ color: "var(--text-muted)" }}>
          No articles have been published yet. Check back tomorrow.
        </p>
      )}

      <AdSlot position="footer" className="mt-8" />

      {/* Homepage Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "WebSite",
            name: SITE_NAME,
            url: BASE_URL,
            description: SITE_DESCRIPTION,
            potentialAction: {
              "@type": "SearchAction",
              target: `${BASE_URL}/?q={search_term_string}`,
              "query-input": "required name=search_term_string",
            },
          }),
        }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Organization",
            name: SITE_NAME,
            url: BASE_URL,
            description: SITE_DESCRIPTION,
            logo: `${BASE_URL}/icon.svg`,
          }),
        }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "ItemList",
            itemListElement: articles.slice(0, 10).map((a, i) => ({
              "@type": "ListItem",
              position: i + 1,
              url: `${BASE_URL}/articles/${a.slug}`,
              name: a.title,
            })),
          }),
        }}
      />
    </div>
  );
}
