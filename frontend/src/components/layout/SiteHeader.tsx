"use client";

import Link from "next/link";
import { useState } from "react";
import { SITE_NAME, BASE_URL } from "@/lib/config";
import { useTheme } from "@/lib/theme";

export default function SiteHeader() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { theme, toggle: toggleTheme } = useTheme();

  return (
    <header className="sticky top-0 z-50 border-b backdrop-blur-xl" style={{ borderColor: "var(--border)", background: "color-mix(in srgb, var(--bg-primary) 85%, transparent)" }}>
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        {/* Logo */}
        <Link href="/" className="group flex items-center gap-2.5 text-lg font-bold tracking-tight" style={{ color: "var(--text-primary)" }}>
          <span className="compass-logo flex h-9 w-9 items-center justify-center">
            <svg width="36" height="36" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="hdr-needle" x1="0.5" y1="0" x2="0.5" y2="1">
                  <stop offset="0%" stopColor="#1a6b7a"/>
                  <stop offset="100%" stopColor="#4db8c9"/>
                </linearGradient>
                <linearGradient id="hdr-needle-lt" x1="0.5" y1="0" x2="0.5" y2="1">
                  <stop offset="0%" stopColor="#4db8c9"/>
                  <stop offset="100%" stopColor="#7dd3e1"/>
                </linearGradient>
              </defs>
              {/* Outer ring */}
              <circle className="compass-ring" cx="20" cy="20" r="17.5" fill="none" stroke="currentColor" strokeWidth="1.2" opacity="0.35"/>
              {/* Inner ring */}
              <circle cx="20" cy="20" r="14" fill="none" stroke="currentColor" strokeWidth="0.6" opacity="0.2"/>
              {/* Cardinal ticks */}
              <g className="compass-ticks" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" opacity="0.45">
                <line x1="20" y1="1" x2="20" y2="5.5"/>
                <line x1="39" y1="20" x2="34.5" y2="20"/>
                <line x1="20" y1="39" x2="20" y2="34.5"/>
                <line x1="1" y1="20" x2="5.5" y2="20"/>
              </g>
              {/* Needle group — this rotates on hover */}
              <g className="compass-needle">
                <polygon points="20,5.5 17,20 20,17.5 23,20" fill="url(#hdr-needle)"/>
                <polygon points="20,34.5 23,20 20,22.5 17,20" fill="url(#hdr-needle-lt)" opacity="0.45"/>
                <circle cx="20" cy="20" r="1.8" fill="#4db8c9"/>
                <circle cx="20" cy="20" r="0.9" fill="#1a6b7a"/>
              </g>
            </svg>
          </span>
          {SITE_NAME}
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden items-center gap-6 md:flex">
          <Link href="/" className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-secondary)" }}>Articles</Link>
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
          <div className="h-4 w-px" style={{ background: "var(--border)" }} />
          <a href={`${BASE_URL}/feed.xml`} className="text-sm transition-colors hover:opacity-80" style={{ color: "var(--text-muted)" }} title="RSS Feed">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 11a9 9 0 0 1 9 9" /><path d="M4 4a16 16 0 0 1 16 16" /><circle cx="5" cy="19" r="1" />
            </svg>
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
          <Link href="/" className="block py-2 text-sm" style={{ color: "var(--text-secondary)" }} onClick={() => setMobileOpen(false)}>Articles</Link>
          <Link href="/tools" className="block py-2 text-sm" style={{ color: "var(--text-secondary)" }} onClick={() => setMobileOpen(false)}>Tools</Link>
          <Link href="/about" className="block py-2 text-sm" style={{ color: "var(--text-secondary)" }} onClick={() => setMobileOpen(false)}>About</Link>
        </nav>
      )}
    </header>
  );
}
