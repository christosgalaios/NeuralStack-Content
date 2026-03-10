"use client";

import Link from "next/link";
import { useState } from "react";
import { SITE_NAME, AFFILIATES } from "@/lib/config";

export default function SiteHeader() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b backdrop-blur-xl" style={{ borderColor: "var(--border)", background: "rgba(10,10,11,0.85)" }}>
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 text-lg font-bold tracking-tight" style={{ color: "var(--text-primary)" }}>
          <span className="flex h-8 w-8 items-center justify-center rounded-lg text-sm font-black" style={{ background: "var(--accent)", color: "#fff" }}>
            {SITE_NAME[0]}
          </span>
          {SITE_NAME}
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden items-center gap-6 md:flex">
          <Link href="/" className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>Home</Link>
          <Link href="/tools" className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>Tools</Link>
          <Link href="/about" className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>About</Link>
          <a
            href={AFFILIATES[0].url}
            target="_blank"
            rel="noopener sponsored"
            className="rounded-lg px-4 py-2 text-sm font-medium text-white transition-colors"
            style={{ background: "var(--accent-cta)" }}
          >
            Try {AFFILIATES[0].name}
          </a>
        </nav>

        {/* Mobile toggle */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="flex h-10 w-10 items-center justify-center rounded-lg md:hidden"
          style={{ color: "var(--text-secondary)" }}
          aria-label="Toggle menu"
        >
          <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            {mobileOpen ? (
              <path d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <nav className="border-t px-4 pb-4 pt-2 md:hidden" style={{ borderColor: "var(--border)", background: "var(--bg-primary)" }}>
          <Link href="/" className="block py-2 text-sm" style={{ color: "var(--text-secondary)" }} onClick={() => setMobileOpen(false)}>Home</Link>
          <Link href="/tools" className="block py-2 text-sm" style={{ color: "var(--text-secondary)" }} onClick={() => setMobileOpen(false)}>Tools</Link>
          <Link href="/about" className="block py-2 text-sm" style={{ color: "var(--text-secondary)" }} onClick={() => setMobileOpen(false)}>About</Link>
        </nav>
      )}
    </header>
  );
}
