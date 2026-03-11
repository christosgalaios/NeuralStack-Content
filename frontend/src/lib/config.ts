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

export interface Affiliate {
  name: string;
  url: string;
  description: string;
  tagline: string;
}

export const AFFILIATES = [
  {
    name: process.env.NEXT_PUBLIC_AFF1_NAME || "Vultr",
    url: process.env.NEXT_PUBLIC_AFF1_URL || "https://www.vultr.com/?ref=9880243-9J",
    description:
      "High-performance cloud compute, bare metal, and GPU instances — get $300 free credit and deploy worldwide in seconds.",
    tagline: "Cloud compute, simplified",
  },
  {
    name: process.env.NEXT_PUBLIC_AFF2_NAME || "Railway",
    url: process.env.NEXT_PUBLIC_AFF2_URL || "https://railway.app?referralCode=2zaRHx",
    description:
      "Deploy code from GitHub in seconds — simple, powerful cloud hosting for developers.",
    tagline: "Ship faster, scale easier",
  },
];

export const AFFILIATE_RELEVANCE: Record<string, string[]> = {
  "Cursor IDE": ["code-editor", "ai-coding", "ide", "developer-tools", "copilot", "vscode", "cursor", "ai editor"],
  "Datadog": ["monitoring", "observability", "logging", "debugging", "apm", "production", "datadog", "grafana"],
  "Railway": ["deployment", "hosting", "cloud", "ci-cd", "infrastructure", "paas", "railway", "heroku", "render"],
};

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
