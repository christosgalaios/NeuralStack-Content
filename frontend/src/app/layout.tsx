import type { Metadata } from "next";
import { SITE_NAME, SITE_DESCRIPTION, BASE_URL, ADSENSE_ID, GOOGLE_VERIFICATION } from "@/lib/config";
import SiteHeader from "@/components/layout/SiteHeader";
import SiteFooter from "@/components/layout/SiteFooter";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: {
    default: `${SITE_NAME} — AI & Developer Intelligence`,
    template: `%s | ${SITE_NAME}`,
  },
  description: SITE_DESCRIPTION,
  metadataBase: new URL(BASE_URL),
  openGraph: {
    type: "website",
    siteName: SITE_NAME,
    locale: "en_US",
  },
  robots: { index: true, follow: true },
  alternates: {
    types: { "application/rss+xml": `${BASE_URL}/feed.xml` },
  },
  verification: {
    google: GOOGLE_VERIFICATION,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
        <link
          rel="icon"
          href={`data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='16' fill='%233B82F6'/%3E%3Ctext x='50' y='68' font-family='system-ui' font-size='56' font-weight='800' fill='white' text-anchor='middle'%3E${SITE_NAME[0]}%3C/text%3E%3C/svg%3E`}
        />
        {ADSENSE_ID && (
          <script
            async
            src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${ADSENSE_ID}`}
            crossOrigin="anonymous"
          />
        )}
      </head>
      <body className="min-h-screen">
        <SiteHeader />
        <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
