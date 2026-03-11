import { getAllArticles, getArticle } from "@/lib/articles";
import { SITE_NAME, SITE_DESCRIPTION, BASE_URL } from "@/lib/config";

export const dynamic = "force-static";

function escapeXml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export function GET() {
  const articles = getAllArticles();

  const items = articles
    .slice(0, 50)
    .map((meta) => {
      const full = getArticle(meta.slug);
      const desc = full?.description || meta.description;
      return `    <item>
      <title>${escapeXml(meta.title)}</title>
      <link>${BASE_URL}/articles/${meta.slug}</link>
      <guid isPermaLink="true">${BASE_URL}/articles/${meta.slug}</guid>
      <pubDate>${new Date(meta.date_published).toUTCString()}</pubDate>
      <description>${escapeXml(desc)}</description>
      <category>${escapeXml(meta.category_display)}</category>
    </item>`;
    })
    .join("\n");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>${escapeXml(SITE_NAME)}</title>
    <link>${BASE_URL}</link>
    <description>${escapeXml(SITE_DESCRIPTION)}</description>
    <language>en</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link href="${BASE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
${items}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: {
      "Content-Type": "application/rss+xml; charset=utf-8",
    },
  });
}
