"use client";

import Link from "next/link";
import { useState } from "react";
import { SITE_NAME, AFFILIATES } from "@/lib/config";
import { useTheme } from "@/lib/theme";

export default function SiteHeader() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { theme, toggle: toggleTheme } = useTheme();

  return (
    <header className="sticky top-0 z-50 border-b backdrop-blur-xl" style={{ borderColor: "var(--border)", background: "color-mix(in srgb, var(--bg-primary) 85%, transparent)" }}>
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
          <button
            onClick={toggleTheme}
            className="flex h-8 w-8 items-center justify-center rounded-lg transition-colors"
            style={{ color: "var(--text-secondary)", background: "var(--bg-elevated)" }}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            {theme === "dark" ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
          </button>
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
