import { SITE_NAME, BASE_URL } from "@/lib/config";
import type { Article } from "@/lib/articles";

export default function ArticleJsonLd({ article }: { article: Article }) {
  const canonical = `${BASE_URL}/articles/${article.slug}`;
  const cat = article.category || "default";

  const articleSchema = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: article.title,
    description: article.description,
    image: [
      `${BASE_URL}/og/${cat}-16x9.png`,
      `${BASE_URL}/og/${cat}-4x3.png`,
      `${BASE_URL}/og/${cat}-1x1.png`,
    ],
    datePublished: article.date_published,
    dateModified: article.date_modified,
    wordCount: article.word_count,
    articleSection: article.category_display,
    author: {
      "@type": "Person",
      name: `${SITE_NAME} Editorial`,
      url: `${BASE_URL}/about`,
    },
    publisher: {
      "@type": "Organization",
      name: SITE_NAME,
      url: BASE_URL,
      logo: {
        "@type": "ImageObject",
        url: `${BASE_URL}/icon.png`,
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
