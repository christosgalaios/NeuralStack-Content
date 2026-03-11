import { SITE_NAME, BASE_URL } from "@/lib/config";
import type { Article } from "@/lib/articles";

export default function ArticleJsonLd({ article }: { article: Article }) {
  const canonical = `${BASE_URL}/articles/${article.slug}`;
  const ogImage = `${BASE_URL}/og/${article.category || "default"}.svg`;

  const articleSchema = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: article.title,
    description: article.description,
    image: ogImage,
    datePublished: article.date_published,
    dateModified: article.date_modified,
    wordCount: article.word_count,
    articleSection: article.category_display,
    author: { "@type": "Organization", name: SITE_NAME, url: BASE_URL },
    publisher: {
      "@type": "Organization",
      name: SITE_NAME,
      url: BASE_URL,
      logo: {
        "@type": "ImageObject",
        url: `${BASE_URL}/icon.svg`,
      },
    },
    mainEntityOfPage: { "@type": "WebPage", "@id": canonical },
  };

  const breadcrumbSchema = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: BASE_URL },
      {
        "@type": "ListItem",
        position: 2,
        name: article.category_display,
        item: `${BASE_URL}/category/${article.category}`,
      },
      { "@type": "ListItem", position: 3, name: article.title },
    ],
  };

  // Strip citation markers like [1], [15] from FAQ answers for clean schema
  const stripCitations = (text: string) =>
    text.replace(/\[\d+\]/g, "").replace(/\s{2,}/g, " ").trim();

  const hasFaq = article.faq && article.faq.length > 0;
  const faqSchema = hasFaq
    ? {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        mainEntity: article.faq!.map((f) => ({
          "@type": "Question",
          name: stripCitations(f.question),
          acceptedAnswer: {
            "@type": "Answer",
            text: stripCitations(f.answer),
          },
        })),
      }
    : null;

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
      />
      {faqSchema && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
        />
      )}
    </>
  );
}
