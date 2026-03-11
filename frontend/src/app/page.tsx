import { getAllArticles, getAllCategories } from "@/lib/articles";
import { SITE_NAME, SITE_DESCRIPTION, BASE_URL, CATEGORY_META } from "@/lib/config";
import ArticleCard from "@/components/cards/ArticleCard";
import AdSlot from "@/components/monetization/AdSlot";
import Link from "next/link";

export default function HomePage() {
  const articles = getAllArticles();
  const categories = getAllCategories();
  const featured = articles.slice(0, 6);
  const archive = articles.slice(6);

  return (
    <div className="animate-in">
      {/* Hero */}
      <section className="py-10 text-center sm:py-14">
        <div className="mb-4 inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium" style={{ borderColor: "var(--border)", color: "var(--accent)" }}>
          Updated daily
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl lg:text-5xl" style={{ color: "var(--text-primary)" }}>
          Developer intelligence,<br className="hidden sm:block" /> distilled.
        </h1>
        <p className="mx-auto mt-4 max-w-lg text-base" style={{ color: "var(--text-muted)" }}>
          In-depth guides on frameworks, tools, databases, and engineering workflows. No fluff.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-6">
          <div className="text-center">
            <p className="text-2xl font-bold" style={{ color: "var(--accent)" }}>{articles.length}</p>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>Articles</p>
          </div>
          <div className="h-8 w-px" style={{ background: "var(--border)" }} />
          <div className="text-center">
            <p className="text-2xl font-bold" style={{ color: "var(--accent)" }}>{categories.length}</p>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>Categories</p>
          </div>
        </div>
      </section>

      {/* Category Pills */}
      {categories.length > 0 && (
        <div className="mb-8 flex flex-wrap gap-2">
          {categories.map((cat) => {
            const meta = CATEGORY_META[cat];
            return (
              <Link
                key={cat}
                href={`/category/${cat}`}
                className="rounded-full border px-3 py-1 text-sm transition-colors hover:border-blue-500/40"
                style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
              >
                {meta?.display || cat}
              </Link>
            );
          })}
        </div>
      )}

      {/* Featured Articles */}
      {featured.length > 0 && (
        <section>
          <h2 className="mb-5 text-xl font-bold" style={{ color: "var(--text-primary)" }}>
            Latest Articles
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {featured.map((article) => (
              <ArticleCard key={article.slug} article={article} />
            ))}
          </div>
        </section>
      )}

      <AdSlot position="in-feed" className="my-8" />

      {/* Archive */}
      {archive.length > 0 && (
        <section className="my-12">
          <h2 className="mb-5 text-xl font-bold" style={{ color: "var(--text-primary)" }}>
            All Articles
          </h2>
          <div className="flex flex-col gap-3">
            {archive.map((article) => (
              <Link
                key={article.slug}
                href={`/articles/${article.slug}`}
                className="archive-link-hover flex items-center justify-between rounded-lg border px-4 py-3 text-sm"
                style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
              >
                <span className="font-medium" style={{ color: "var(--text-primary)" }}>
                  {article.title}
                </span>
                <span className="shrink-0 text-xs" style={{ color: "var(--text-muted)" }}>
                  {article.date_published}
                </span>
              </Link>
            ))}
          </div>
        </section>
      )}

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
          __html: JSON.stringify([
            {
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
            },
            {
              "@context": "https://schema.org",
              "@type": "Organization",
              name: SITE_NAME,
              url: BASE_URL,
              description: SITE_DESCRIPTION,
            },
            {
              "@context": "https://schema.org",
              "@type": "ItemList",
              itemListElement: articles.slice(0, 10).map((a, i) => ({
                "@type": "ListItem",
                position: i + 1,
                url: `${BASE_URL}/articles/${a.slug}`,
                name: a.title,
              })),
            },
          ]),
        }}
      />
    </div>
  );
}
