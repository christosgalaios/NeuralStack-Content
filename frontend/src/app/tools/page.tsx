import type { Metadata } from "next";
import { SITE_NAME, BASE_URL, AFFILIATES } from "@/lib/config";
import ToolCard from "@/components/cards/ToolCard";
import AdSlot from "@/components/monetization/AdSlot";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Recommended Developer Tools",
  description: `Hand-picked developer tools reviewed and recommended by ${SITE_NAME}. Cloud compute, hosting platforms, and deployment tools.`,
  openGraph: {
    title: `Recommended Developer Tools | ${SITE_NAME}`,
    url: `${BASE_URL}/tools`,
  },
  alternates: { canonical: `${BASE_URL}/tools` },
};

export default function ToolsPage() {
  return (
    <div className="animate-in">
      <nav className="mb-6 flex items-center gap-2 text-sm" style={{ color: "var(--text-muted)" }}>
        <Link href="/" className="transition-colors hover:opacity-80" style={{ color: "var(--accent)" }}>Home</Link>
        <span>/</span>
        <span style={{ color: "var(--text-secondary)" }}>Tools</span>
      </nav>

      <header className="mb-8">
        <h1 className="text-2xl font-extrabold sm:text-3xl" style={{ color: "var(--text-primary)" }}>
          Recommended Developer Tools
        </h1>
        <p className="mt-2 max-w-2xl" style={{ color: "var(--text-secondary)" }}>
          Hand-picked tools for developers who want to ship faster. We use these ourselves.
        </p>
      </header>

      <AdSlot position="top" className="mb-8" />

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {AFFILIATES.map((aff) => (
          <ToolCard key={aff.name} {...aff} />
        ))}
      </div>

      {/* Comparison table */}
      <section className="mt-12">
        <h2 className="mb-5 text-xl font-bold" style={{ color: "var(--text-primary)" }}>
          Quick Comparison
        </h2>
        <div className="overflow-x-auto rounded-xl border" style={{ borderColor: "var(--border)" }}>
          <table className="w-full text-sm" style={{ background: "var(--bg-card)" }}>
            <thead style={{ background: "var(--bg-elevated)" }}>
              <tr>
                <th className="px-4 py-3 text-left font-semibold" style={{ color: "var(--text-primary)" }}>Tool</th>
                <th className="px-4 py-3 text-left font-semibold" style={{ color: "var(--text-primary)" }}>Category</th>
                <th className="px-4 py-3 text-left font-semibold" style={{ color: "var(--text-primary)" }}>Best For</th>
                <th className="px-4 py-3 text-left font-semibold" style={{ color: "var(--text-primary)" }}>Free Tier</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t" style={{ borderColor: "var(--border)" }}>
                <td className="px-4 py-3 font-medium" style={{ color: "var(--text-primary)" }}>{AFFILIATES[0].name}</td>
                <td className="px-4 py-3" style={{ color: "var(--text-secondary)" }}>Cloud Compute</td>
                <td className="px-4 py-3" style={{ color: "var(--text-secondary)" }}>VPS, bare metal, and GPU workloads</td>
                <td className="px-4 py-3" style={{ color: "var(--accent-cta)" }}>$300 credit</td>
              </tr>
              <tr className="border-t" style={{ borderColor: "var(--border)" }}>
                <td className="px-4 py-3 font-medium" style={{ color: "var(--text-primary)" }}>{AFFILIATES[1].name}</td>
                <td className="px-4 py-3" style={{ color: "var(--text-secondary)" }}>Cloud Hosting</td>
                <td className="px-4 py-3" style={{ color: "var(--text-secondary)" }}>Deploying from GitHub in seconds</td>
                <td className="px-4 py-3" style={{ color: "var(--accent-cta)" }}>$5 credit</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <AdSlot position="bottom" className="mt-8" />

      {/* Product schema */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "ItemList",
            itemListElement: AFFILIATES.map((aff, i) => ({
              "@type": "ListItem",
              position: i + 1,
              item: {
                "@type": "Product",
                name: aff.name,
                description: aff.description,
                url: aff.url,
              },
            })),
          }),
        }}
      />
    </div>
  );
}
