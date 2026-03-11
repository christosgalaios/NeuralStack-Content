import fs from "fs";
import path from "path";
import { AFFILIATES, AFFILIATE_RELEVANCE, type Affiliate } from "./config";

export interface ArticleMeta {
  slug: string;
  title: string;
  description: string;
  category: string;
  category_display: string;
  date_published: string;
  reading_time_minutes: number;
  tags: string[];
}

export interface Article extends ArticleMeta {
  content_html: string;
  date_modified: string;
  word_count: number;
  toc: { id: string; text: string }[];
  related_slugs: string[];
  affiliate: { name: string; url: string; description: string };
  faq: { question: string; answer: string }[];
}

const DATA_DIR = path.join(process.cwd(), "..", "data", "articles");

export function getAllArticles(): ArticleMeta[] {
  const indexPath = path.join(DATA_DIR, "_index.json");
  if (!fs.existsSync(indexPath)) return [];
  const raw = fs.readFileSync(indexPath, "utf-8");
  return JSON.parse(raw) as ArticleMeta[];
}

export function getArticle(slug: string): Article | null {
  const filePath = path.join(DATA_DIR, `${slug}.json`);
  if (!fs.existsSync(filePath)) return null;
  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw) as Article;
}

export function getAllSlugs(): string[] {
  if (!fs.existsSync(DATA_DIR)) return [];
  return fs
    .readdirSync(DATA_DIR)
    .filter((f) => f.endsWith(".json") && !f.startsWith("_"))
    .map((f) => f.replace(".json", ""));
}

export function getArticlesByCategory(category: string): ArticleMeta[] {
  return getAllArticles().filter((a) => a.category === category);
}

export function getAllCategories(): string[] {
  const articles = getAllArticles();
  return [...new Set(articles.map((a) => a.category))];
}

export function getAllTags(): string[] {
  const articles = getAllArticles();
  const tags = new Set<string>();
  articles.forEach((a) => a.tags?.forEach((t) => tags.add(t)));
  return [...tags].sort();
}

export function getArticlesByTag(tag: string): ArticleMeta[] {
  return getAllArticles().filter((a) => a.tags?.includes(tag));
}

export function getRelatedArticles(slugs: string[]): ArticleMeta[] {
  const all = getAllArticles();
  return slugs
    .map((s) => all.find((a) => a.slug === s))
    .filter((a): a is ArticleMeta => a !== undefined);
}

export function getRelevantAffiliate(article: { title: string; description: string; category: string }): Affiliate | null {
  const text = `${article.title} ${article.description} ${article.category}`.toLowerCase();
  for (const aff of AFFILIATES) {
    const keywords = AFFILIATE_RELEVANCE[aff.name] || [];
    if (keywords.some((kw) => text.includes(kw))) return aff;
  }
  return null;
}
