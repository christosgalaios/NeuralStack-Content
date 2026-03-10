import { CATEGORY_META } from "@/lib/config";

const COLOR_MAP: Record<string, string> = {
  blue: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  purple: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  green: "bg-green-500/10 text-green-400 border-green-500/20",
  amber: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  red: "bg-red-500/10 text-red-400 border-red-500/20",
  slate: "bg-slate-500/10 text-slate-400 border-slate-500/20",
};

export default function CategoryBadge({ category }: { category: string }) {
  const meta = CATEGORY_META[category] || CATEGORY_META.guide;
  const colorClass = COLOR_MAP[meta.color] || COLOR_MAP.slate;

  return (
    <span className={`inline-block w-fit rounded-full border px-2.5 py-0.5 text-xs font-medium ${colorClass}`}>
      {meta.display}
    </span>
  );
}
