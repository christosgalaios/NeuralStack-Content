"use client";

import { useEffect, useState } from "react";

interface TocItem {
  id: string;
  text: string;
}

export default function TableOfContents({ items }: { items: TocItem[] }) {
  const [activeId, setActiveId] = useState("");

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
          }
        }
      },
      { rootMargin: "-80px 0px -70% 0px" }
    );
    items.forEach((item) => {
      const el = document.getElementById(item.id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, [items]);

  if (items.length < 2) return null;

  return (
    <nav className="rounded-xl border p-4" style={{ background: "var(--bg-card)", borderColor: "var(--border)" }}>
      <p className="mb-3 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
        In this article
      </p>
      <ol className="flex flex-col gap-1">
        {items.map((item, i) => (
          <li key={item.id}>
            <a
              href={`#${item.id}`}
              className="block rounded-md px-2 py-1.5 text-sm leading-snug transition-colors"
              style={{
                color: activeId === item.id ? "var(--accent)" : "var(--text-secondary)",
                background: activeId === item.id ? "var(--accent-glow)" : "transparent",
              }}
            >
              <span style={{ color: "var(--text-muted)" }}>{i + 1}.</span>{" "}
              {item.text}
            </a>
          </li>
        ))}
      </ol>
    </nav>
  );
}
