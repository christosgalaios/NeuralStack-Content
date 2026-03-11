// Centralized brand & site configuration — change brand name here only
export const SITE_NAME = process.env.NEXT_PUBLIC_SITE_NAME || "Dev Guide";
export const SITE_TAGLINE = "AI-Powered Developer Intelligence";
export const SITE_DESCRIPTION =
  "In-depth technical guides on developer tooling, AI code editors, cloud platforms, and engineering workflows — updated daily.";

export const BASE_URL =
  process.env.NEXT_PUBLIC_BASE_URL || "https://devguide.co.uk";

export const ADSENSE_ID = process.env.NEXT_PUBLIC_ADSENSE_ID || "";

export const GOOGLE_VERIFICATION =
  process.env.NEXT_PUBLIC_GOOGLE_VERIFICATION ||
  "i27IVb0fNqCp511fOfQTd08teAnHKX23tp8d-TPuHO0";

export const AFFILIATES = [
  {
    name: process.env.NEXT_PUBLIC_AFF1_NAME || "Cursor IDE",
    url: process.env.NEXT_PUBLIC_AFF1_URL || "https://www.cursor.com",
    description:
      "AI-first code editor that accelerates your workflow with intelligent completions and inline chat.",
    tagline: "Write code 10x faster",
  },
  {
    name: process.env.NEXT_PUBLIC_AFF2_NAME || "Datadog",
    url: process.env.NEXT_PUBLIC_AFF2_URL || "https://www.datadoghq.com",
    description:
      "Full-stack observability platform for monitoring your cloud infrastructure and applications.",
    tagline: "See everything in production",
  },
  {
    name: process.env.NEXT_PUBLIC_AFF3_NAME || "Railway",
    url: process.env.NEXT_PUBLIC_AFF3_URL || "https://railway.app",
    description:
      "Deploy code from GitHub in seconds — simple, powerful cloud hosting for developers.",
    tagline: "Ship faster, scale easier",
  },
];

export const CATEGORY_META: Record<
  string,
  { display: string; description: string; color: string }
> = {
  comparison: {
    display: "Comparison",
    description: "Head-to-head tool comparisons with honest trade-offs.",
    color: "blue",
  },
  compatibility: {
    display: "Compatibility",
    description: "Version matrices, known issues, and environment guides.",
    color: "purple",
  },
  tutorial: {
    display: "Tutorial",
    description: "Step-by-step guides for modern developer workflows.",
    color: "green",
  },
  review: {
    display: "Review",
    description: "Hands-on reviews of developer tools and platforms.",
    color: "amber",
  },
  news: {
    display: "News",
    description: "Technical news and analysis for global engineers.",
    color: "red",
  },
  guide: {
    display: "Guide",
    description: "Practical engineering guides and best practices.",
    color: "slate",
  },
};
