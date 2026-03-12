"use client";

import { useEffect, useRef, useState, useCallback } from "react";

export default function FloatingCompass() {
  const [visible, setVisible] = useState(false);
  const btnRef = useRef<HTMLButtonElement>(null);
  const needleRef = useRef<SVGGElement>(null);
  const rotationRef = useRef(0);
  const targetRef = useRef(0);
  const isTrackingRef = useRef(false);
  const idleTimeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  // Visibility: watch hero compass or scroll position
  useEffect(() => {
    const heroEl = document.querySelector(".hero-compass");
    if (!heroEl) {
      const handleScroll = () => setVisible(window.scrollY > 400);
      window.addEventListener("scroll", handleScroll, { passive: true });
      handleScroll();
      return () => window.removeEventListener("scroll", handleScroll);
    }

    const observer = new IntersectionObserver(
      ([entry]) => setVisible(!entry.isIntersecting),
      { threshold: 0 }
    );
    observer.observe(heroEl);
    return () => observer.disconnect();
  }, []);

  // Compute angle from a point to the compass center
  const updateTarget = useCallback((clientX: number, clientY: number) => {
    if (!btnRef.current) return;
    const rect = btnRef.current.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    targetRef.current =
      Math.atan2(clientX - cx, -(clientY - cy)) * (180 / Math.PI);
    isTrackingRef.current = true;

    clearTimeout(idleTimeoutRef.current);
    idleTimeoutRef.current = setTimeout(() => {
      isTrackingRef.current = false;
    }, 3000);
  }, []);

  // Animation loop: mouse-tracking + idle sway
  useEffect(() => {
    if (!visible) return;
    let animFrame: number;

    const animate = () => {
      if (!needleRef.current) return;
      if (isTrackingRef.current) {
        let delta = targetRef.current - rotationRef.current;
        while (delta > 180) delta -= 360;
        while (delta < -180) delta += 360;
        rotationRef.current += delta * 0.1;
      } else {
        const t = performance.now() / 1000;
        const swayTarget = Math.sin(t * 0.6) * 10 + Math.cos(t * 0.35) * 5;
        rotationRef.current += (swayTarget - rotationRef.current) * 0.03;
      }
      needleRef.current.style.transform = `rotate(${rotationRef.current}deg)`;
      animFrame = requestAnimationFrame(animate);
    };

    // Mouse tracking
    const handleMouseMove = (e: MouseEvent) => updateTarget(e.clientX, e.clientY);

    // Touch tracking — responds to taps, drags, and swipes anywhere on page
    const handleTouchMove = (e: TouchEvent) => {
      const touch = e.touches[0];
      if (touch) updateTarget(touch.clientX, touch.clientY);
    };
    const handleTouchStart = (e: TouchEvent) => {
      const touch = e.touches[0];
      if (touch) updateTarget(touch.clientX, touch.clientY);
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("touchmove", handleTouchMove, { passive: true });
    window.addEventListener("touchstart", handleTouchStart, { passive: true });
    animFrame = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("touchmove", handleTouchMove);
      window.removeEventListener("touchstart", handleTouchStart);
      cancelAnimationFrame(animFrame);
      clearTimeout(idleTimeoutRef.current);
    };
  }, [visible, updateTarget]);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <button
      ref={btnRef}
      onClick={scrollToTop}
      className="floating-compass"
      style={{ opacity: visible ? 1 : 0, pointerEvents: visible ? "auto" : "none" }}
      aria-label="Scroll to top"
      title="Back to top"
    >
      <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-full w-full">
        <defs>
          <linearGradient id="fc-n" x1="0.3" y1="0" x2="0.7" y2="1">
            <stop offset="0%" stopColor="#0d4a5a" />
            <stop offset="100%" stopColor="#1a8a9a" />
          </linearGradient>
          <linearGradient id="fc-s" x1="0.5" y1="0" x2="0.5" y2="1">
            <stop offset="0%" stopColor="#2da0b0" />
            <stop offset="100%" stopColor="#4cc0d0" />
          </linearGradient>
        </defs>

        {/* Outer ring */}
        <circle cx="20" cy="20" r="17" fill="none" stroke="#7a8494" strokeWidth="1.2" opacity="0.35" />

        {/* Inner ring */}
        <circle cx="20" cy="20" r="13.5" fill="none" stroke="#7a8494" strokeWidth="0.5" opacity="0.15" />

        {/* Needle group — tracks mouse/touch */}
        <g ref={needleRef} style={{ transformOrigin: "20px 20px" }}>
          <path d="M20,3 L17,12 L14.5,17.5 L18,20 L20,17 L22,20 L25.5,17.5 L23,12 Z" fill="url(#fc-n)" />
          <path d="M20,37 L23,28 L25.5,22.5 L22,20 L20,23 L18,20 L14.5,22.5 L17,28 Z" fill="url(#fc-s)" opacity="0.3" />
          <circle cx="20" cy="20" r="2" fill="#e2e8f0" />
          <circle cx="20" cy="20" r="1" fill="#0d4a5a" />
        </g>
      </svg>
    </button>
  );
}
