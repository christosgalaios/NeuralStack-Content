import { SITE_NAME, BASE_URL } from "@/lib/config";
import type { Article } from "@/lib/articles";

export default function ArticleJsonLd({ article }: { article: Article }) {
  const canonical = `${BASE_URL}/articles/${article.slug}`;

  const schemas = [
    {
      "@context": "https://schema.org",
      "@type": "TechArticle",
      headline: article.title,
      description: article.description,
      datePublished: article.date_published,
      dateModified: article.date_modified,
      wordCount: article.word_count,
      articleSection: article.category_display,
      author: { "@type": "Organization", name: SITE_NAME },
      publisher: {
        "@type": "Organization",
        name: SITE_NAME,
        url: BASE_URL,
      },
      mainEntityOfPage: { "@type": "WebPage", "@id": canonical },
    },
    {
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
    },
  ];

  // Add FAQ schema if FAQ items exist
  if (article.faq && article.faq.length > 0) {
    schemas.push({
      "@context": "https://schema.org",
      "@type": "FAQPage",
      mainEntity: article.faq.map((f) => ({
        "@type": "Question",
        name: f.question,
        acceptedAnswer: { "@type": "Answer", text: f.answer },
      })),
    } as any);
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schemas) }}
    />
  );
}
