import Link from "next/link";
import type { ArticleMeta } from "@/lib/articles";
import CategoryBadge from "./CategoryBadge";

export default function ArticleCard({ article }: { article: ArticleMeta }) {
  return (
    <Link
      href={`/articles/${article.slug}`}
      className="card-hover group flex flex-col rounded-xl border p-5 hover:-translate-y-0.5"
      style={{
        background: "var(--bg-card)",
        borderColor: "var(--border)",
      }}
    >
      <div className="flex items-center gap-2">
        <CategoryBadge category={article.category} />
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>
          {article.date_published}
        </span>
      </div>

      <h3
        className="mt-3 text-base font-semibold leading-snug transition-colors group-hover:underline"
        style={{ color: "var(--text-primary)" }}
      >
        {article.title}
      </h3>

      <p className="mt-2 line-clamp-2 flex-1 text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
        {article.description?.slice(0, 160)}
      </p>

      <div className="mt-4 text-xs" style={{ color: "var(--text-muted)" }}>
        {article.reading_time_minutes} min read
      </div>
    </Link>
  );
}
