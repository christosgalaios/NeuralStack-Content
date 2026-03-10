import { getAllArticles, getAllCategories } from "@/lib/articles";
import { SITE_NAME, SITE_TAGLINE, AFFILIATES, CATEGORY_META } from "@/lib/config";
import ArticleCard from "@/components/cards/ArticleCard";
import ToolCard from "@/components/cards/ToolCard";
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
      <section className="py-8 text-center sm:py-12">
        <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl lg:text-5xl" style={{ color: "var(--text-primary)" }}>
          {SITE_NAME}
        </h1>
        <p className="mx-auto mt-3 max-w-xl text-lg" style={{ color: "var(--text-secondary)" }}>
          {SITE_TAGLINE}
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-6">
          <div className="text-center">
            <p className="text-2xl font-bold" style={{ color: "var(--accent)" }}>{articles.length}</p>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>Articles</p>
          </div>
          <div className="h-8 w-px" style={{ background: "var(--border)" }} />
          <div className="text-center">
            <p className="text-2xl font-bold" style={{ color: "var(--accent)" }}>{categories.length}</p>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>Categories</p>
          </div>
          <div className="h-8 w-px" style={{ background: "var(--border)" }} />
          <div className="text-center">
            <p className="text-2xl font-bold" style={{ color: "var(--accent-cta)" }}>Daily</p>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>Updates</p>
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

      {/* Tools Section */}
      <section className="my-12">
        <h2 className="mb-5 text-xl font-bold" style={{ color: "var(--text-primary)" }}>
          Recommended Developer Tools
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {AFFILIATES.map((aff) => (
            <ToolCard key={aff.name} {...aff} />
          ))}
        </div>
      </section>

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
    </div>
  );
}
