import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { getAllCategories, getArticlesByCategory } from "@/lib/articles";
import { SITE_NAME, BASE_URL, CATEGORY_META } from "@/lib/config";
import ArticleCard from "@/components/cards/ArticleCard";
import AdSlot from "@/components/monetization/AdSlot";
import CategoryIllustration from "@/components/cards/CategoryIllustration";
import Link from "next/link";

export async function generateStaticParams() {
  return getAllCategories().map((cat) => ({ cat }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ cat: string }>;
}): Promise<Metadata> {
  const { cat } = await params;
  const meta = CATEGORY_META[cat];
  if (!meta) return {};

  const ogImage = `${BASE_URL}/og/${cat}-16x9.png`;
  return {
    title: `${meta.display} Articles`,
    description: meta.description,
    openGraph: {
      title: `${meta.display} Articles | ${SITE_NAME}`,
      description: meta.description,
      url: `${BASE_URL}/category/${cat}`,
      images: [{ url: ogImage, width: 1200, height: 675, alt: `${meta.display} Articles` }],
    },
    twitter: {
      card: "summary_large_image",
      title: `${meta.display} Articles | ${SITE_NAME}`,
      description: meta.description,
      images: [ogImage],
    },
    alternates: { canonical: `${BASE_URL}/category/${cat}` },
  };
}

export default async function CategoryPage({
  params,
}: {
  params: Promise<{ cat: string }>;
}) {
  const { cat } = await params;
  const meta = CATEGORY_META[cat];
  if (!meta) notFound();

  const articles = getArticlesByCategory(cat);

  return (
    <div className="animate-in">
      {/* Breadcrumb */}
      <nav className="mb-6 flex items-center gap-2 text-sm" style={{ color: "var(--text-muted)" }}>
        <Link href="/" className="transition-colors hover:opacity-80" style={{ color: "var(--accent)" }}>Home</Link>
        <span>/</span>
        <span style={{ color: "var(--text-secondary)" }}>{meta.display}</span>
      </nav>

      {/* Hero with illustration */}
      <div
        className="mb-8 overflow-hidden rounded-xl border"
        style={{ background: "var(--bg-elevated)", borderColor: "var(--border)" }}
      >
        <CategoryIllustration category={cat} className="h-32 sm:h-40" />
      </div>
      <header className="mb-8">
        <h1 className="text-2xl font-extrabold sm:text-3xl" style={{ color: "var(--text-primary)" }}>
          {meta.display}
        </h1>
        <p className="mt-2" style={{ color: "var(--text-secondary)" }}>
          {meta.description}
        </p>
        <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
          {articles.length} article{articles.length !== 1 ? "s" : ""}
        </p>
      </header>

      <AdSlot position="top" className="mb-6" />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {articles.map((article) => (
          <ArticleCard key={article.slug} article={article} />
        ))}
      </div>

      {articles.length === 0 && (
        <p className="py-16 text-center" style={{ color: "var(--text-muted)" }}>
          No articles in this category yet.
        </p>
      )}

      <AdSlot position="bottom" className="mt-8" />

      {/* Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            name: `${meta.display} Articles`,
            description: meta.description,
            url: `${BASE_URL}/category/${cat}`,
            numberOfItems: articles.length,
          }),
        }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            itemListElement: [
              { "@type": "ListItem", position: 1, name: "Home", item: BASE_URL },
              { "@type": "ListItem", position: 2, name: meta.display },
            ],
          }),
        }}
      />
    </div>
  );
}
