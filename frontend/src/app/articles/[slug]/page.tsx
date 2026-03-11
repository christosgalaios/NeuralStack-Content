import { notFound } from "next/navigation";
import Link from "next/link";
import type { Metadata } from "next";
import { getAllSlugs, getArticle, getRelatedArticles, getRelevantAffiliate } from "@/lib/articles";
import { SITE_NAME, BASE_URL, CATEGORY_META } from "@/lib/config";
import ReadingProgress from "@/components/article/ReadingProgress";
import TableOfContents from "@/components/article/TableOfContents";
import CategoryBadge from "@/components/cards/CategoryBadge";
import ArticleCard from "@/components/cards/ArticleCard";
import ToolCallout from "@/components/monetization/ToolCallout";
import AdSlot from "@/components/monetization/AdSlot";
import ArticleJsonLd from "@/components/seo/ArticleJsonLd";
import CategoryIllustration from "@/components/cards/CategoryIllustration";

export async function generateStaticParams() {
  return getAllSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const article = getArticle(slug);
  if (!article) return {};

  const canonical = `${BASE_URL}/articles/${slug}`;
  const ogImage = `${BASE_URL}/og/${article.category}.svg`;
  return {
    title: article.title,
    description: article.description,
    openGraph: {
      type: "article",
      title: article.title,
      description: article.description,
      url: canonical,
      publishedTime: article.date_published,
      modifiedTime: article.date_modified,
      section: article.category_display,
      images: [{ url: ogImage, width: 1200, height: 630, alt: article.title }],
    },
    twitter: {
      card: "summary_large_image",
      title: article.title,
      description: article.description,
      images: [ogImage],
    },
    alternates: { canonical },
    robots: { index: true, follow: true },
  };
}

export default async function ArticlePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const article = getArticle(slug);
  if (!article) notFound();

  const related = getRelatedArticles(article.related_slugs);
  const catMeta = CATEGORY_META[article.category];

  return (
    <>
      <ArticleJsonLd article={article} />
      <ReadingProgress />

      <div className="animate-in">
        {/* Breadcrumb */}
        <nav className="mb-6 flex items-center gap-2 text-sm" style={{ color: "var(--text-muted)" }}>
          <Link href="/" className="transition-colors hover:opacity-80" style={{ color: "var(--accent)" }}>Home</Link>
          <span>/</span>
          <Link href={`/category/${article.category}`} className="transition-colors hover:opacity-80" style={{ color: "var(--accent)" }}>
            {article.category_display}
          </Link>
          <span>/</span>
          <span className="truncate" style={{ color: "var(--text-secondary)" }}>{article.title}</span>
        </nav>

        {/* Hero illustration */}
        <div
          className="mb-6 overflow-hidden rounded-xl border"
          style={{ background: "var(--bg-elevated)", borderColor: "var(--border)" }}
        >
          <CategoryIllustration
            category={article.category}
            className="h-36 sm:h-44"
          />
        </div>

        <AdSlot position="above-title" className="mb-6" />

        {/* Article Header */}
        <header className="mb-8">
          <CategoryBadge category={article.category} />
          <h1 className="mt-4 text-2xl font-extrabold leading-tight sm:text-3xl lg:text-4xl" style={{ color: "var(--text-primary)" }}>
            {article.title}
          </h1>
          <div className="mt-4 flex items-center gap-3 text-sm" style={{ color: "var(--text-muted)" }}>
            <span>{SITE_NAME}</span>
            <span>&bull;</span>
            <span>{article.date_published}</span>
            <span>&bull;</span>
            <span>{article.reading_time_minutes} min read</span>
            <span>&bull;</span>
            <span>{article.word_count.toLocaleString()} words</span>
          </div>
        </header>

        {/* Two-column layout */}
        <div className="lg:grid lg:grid-cols-[1fr_280px] lg:gap-8">
          {/* Main content */}
          <div>
            <div
              className="article-content"
              dangerouslySetInnerHTML={{ __html: article.content_html }}
            />

            {/* In-article affiliate callout — only if relevant */}
            {(() => {
              const aff = getRelevantAffiliate(article);
              return aff ? (
                <ToolCallout
                  name={aff.name}
                  url={aff.url}
                  description={aff.description}
                />
              ) : null;
            })()}

            {/* FAQ section */}
            {article.faq && article.faq.length > 0 && (
              <section className="mt-10 rounded-xl border p-6" style={{ background: "var(--bg-card)", borderColor: "var(--border)" }}>
                <h2 className="mb-4 text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                  Frequently Asked Questions
                </h2>
                {article.faq.map((f, i) => (
                  <div key={i} className="border-b py-4 last:border-0" style={{ borderColor: "var(--border)" }}>
                    <p className="font-medium" style={{ color: "var(--text-primary)" }}>{f.question}</p>
                    <p className="mt-2 text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>{f.answer}</p>
                  </div>
                ))}
              </section>
            )}

            <AdSlot position="below-article" className="mt-8" />
          </div>

          {/* Sidebar */}
          <aside className="hidden lg:block">
            <div className="sticky top-20 flex flex-col gap-6">
              <TableOfContents items={article.toc} />
              <AdSlot position="sidebar" />
            </div>
          </aside>
        </div>

        {/* Related Articles */}
        {related.length > 0 && (
          <section className="mt-12">
            <h2 className="mb-5 text-xl font-bold" style={{ color: "var(--text-primary)" }}>
              Related Articles
            </h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {related.map((r) => (
                <ArticleCard key={r.slug} article={r} />
              ))}
            </div>
          </section>
        )}
      </div>
    </>
  );
}
