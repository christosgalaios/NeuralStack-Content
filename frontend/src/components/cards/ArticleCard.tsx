import Link from "next/link";
import type { ArticleMeta } from "@/lib/articles";
import { CATEGORY_META } from "@/lib/config";
import CategoryBadge from "./CategoryBadge";

export default function ArticleCard({ article }: { article: ArticleMeta }) {
  const catMeta = CATEGORY_META[article.category];

  return (
    <Link
      href={`/articles/${article.slug}`}
      className="card-hover group flex flex-col rounded-xl border p-5 hover:-translate-y-0.5"
      style={{
        background: "var(--bg-card)",
        borderColor: "var(--border)",
      }}
    >
      <CategoryBadge category={article.category} />

      <h3
        className="mt-3 text-base font-semibold leading-snug transition-colors group-hover:text-blue-400"
        style={{ color: "var(--text-primary)" }}
      >
        {article.title}
      </h3>

      <p className="mt-2 line-clamp-2 flex-1 text-sm" style={{ color: "var(--text-muted)" }}>
        {article.description?.slice(0, 140)}
      </p>

      <div className="mt-4 flex items-center gap-3 text-xs" style={{ color: "var(--text-muted)" }}>
        <span>{article.date_published}</span>
        <span style={{ color: "var(--border)" }}>&bull;</span>
        <span>{article.reading_time_minutes} min read</span>
      </div>
    </Link>
  );
}
