import Link from "next/link";
import type { ArticleMeta } from "@/lib/articles";
import CategoryBadge from "./CategoryBadge";
import CategoryIllustration from "./CategoryIllustration";

export default function ArticleCard({ article }: { article: ArticleMeta }) {
  return (
    <Link
      href={`/articles/${article.slug}`}
      className="card-hover group flex flex-col overflow-hidden rounded-xl border hover:-translate-y-0.5"
      style={{
        background: "var(--bg-card)",
        borderColor: "var(--border)",
      }}
    >
      {/* Illustration banner */}
      <div
        className="relative h-32 overflow-hidden"
        style={{ background: "var(--bg-elevated)" }}
      >
        <CategoryIllustration
          category={article.category}
          className="absolute inset-0 opacity-80 transition-transform duration-500 group-hover:scale-105"
        />
        {/* Gradient fade to card background */}
        <div
          className="absolute inset-x-0 bottom-0 h-8"
          style={{
            background: "linear-gradient(to top, var(--bg-card), transparent)",
          }}
        />
      </div>

      <div className="flex flex-1 flex-col p-5 pt-3">
        <CategoryBadge category={article.category} />

        <h3
          className="mt-3 text-base font-semibold leading-snug transition-colors group-hover:underline"
          style={{ color: "var(--text-primary)" }}
        >
          {article.title}
        </h3>

        <p className="mt-2 line-clamp-2 flex-1 text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
          {article.description?.slice(0, 160)}
        </p>

        <div className="mt-4 flex items-center gap-3 text-xs" style={{ color: "var(--text-muted)" }}>
          <span>{article.date_published}</span>
          <span style={{ color: "var(--border)" }}>&bull;</span>
          <span>{article.reading_time_minutes} min read</span>
        </div>
      </div>
    </Link>
  );
}
