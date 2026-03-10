import type { Metadata } from "next";
import { SITE_NAME, BASE_URL, SITE_DESCRIPTION } from "@/lib/config";
import Link from "next/link";

export const metadata: Metadata = {
  title: "About",
  description: `About ${SITE_NAME} — independent, AI-powered technical content for developers.`,
  alternates: { canonical: `${BASE_URL}/about` },
};

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-2xl animate-in">
      <nav className="mb-6 flex items-center gap-2 text-sm" style={{ color: "var(--text-muted)" }}>
        <Link href="/" className="transition-colors hover:opacity-80" style={{ color: "var(--accent)" }}>Home</Link>
        <span>/</span>
        <span style={{ color: "var(--text-secondary)" }}>About</span>
      </nav>

      <h1 className="text-2xl font-extrabold sm:text-3xl" style={{ color: "var(--text-primary)" }}>
        About {SITE_NAME}
      </h1>

      <div className="mt-6 flex flex-col gap-6 text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
        <p>
          {SITE_NAME} publishes in-depth technical guides on developer tooling,
          cloud platforms, AI code editors, and engineering workflows. Our content
          is updated daily and designed to help engineers make informed decisions
          about the tools they use.
        </p>

        <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
          Our Approach
        </h2>
        <p>
          Every article includes practical trade-offs, real-world implementation
          patterns, and honest recommendations. We focus on comparison guides,
          compatibility reports, and hands-on reviews — the content engineers
          actually need when evaluating tools.
        </p>

        <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
          Editorial Independence
        </h2>
        <p>
          While {SITE_NAME} uses affiliate links to support operations, our
          recommendations are based on genuine technical evaluation. We only
          recommend tools we believe deliver real value to developers.
        </p>

        <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
          Affiliate Disclosure
        </h2>
        <p>
          Some links on this site are affiliate links. When you purchase through
          these links, we may earn a commission at no additional cost to you.
          This helps us continue producing free, high-quality technical content.
        </p>
      </div>

      {/* Organization schema for E-E-A-T */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Organization",
            name: SITE_NAME,
            url: BASE_URL,
            description: SITE_DESCRIPTION,
          }),
        }}
      />
    </div>
  );
}
