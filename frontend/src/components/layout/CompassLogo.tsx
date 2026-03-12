"use client";

import { useEffect, useRef } from "react";

export default function CompassLogo() {
  const compassRef = useRef<HTMLSpanElement>(null);
  const needleRef = useRef<SVGGElement>(null);
  const rotationRef = useRef(0);
  const targetRef = useRef(0);
  const isTrackingRef = useRef(false);
  const idleTimeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    let animFrame: number;

    const applyRotation = () => {
      if (!needleRef.current) return;
      if (isTrackingRef.current) {
        // Smooth spring-like interpolation toward mouse angle
        let delta = targetRef.current - rotationRef.current;
        // Normalize to [-180, 180] for shortest path
        while (delta > 180) delta -= 360;
        while (delta < -180) delta += 360;
        rotationRef.current += delta * 0.12;
      } else {
        // Gentle idle sway
        const t = performance.now() / 1000;
        const swayTarget = Math.sin(t * 0.5) * 12 + Math.cos(t * 0.33) * 6;
        rotationRef.current += (swayTarget - rotationRef.current) * 0.025;
      }
      needleRef.current.style.transform = `rotate(${rotationRef.current}deg)`;
      animFrame = requestAnimationFrame(applyRotation);
    };

    const handleMouseMove = (e: MouseEvent) => {
      if (!compassRef.current) return;
      const rect = compassRef.current.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      // atan2(dx, -dy) gives 0° = north, positive = clockwise
      targetRef.current =
        Math.atan2(e.clientX - cx, -(e.clientY - cy)) * (180 / Math.PI);
      isTrackingRef.current = true;

      clearTimeout(idleTimeoutRef.current);
      idleTimeoutRef.current = setTimeout(() => {
        isTrackingRef.current = false;
      }, 3000);
    };

    window.addEventListener("mousemove", handleMouseMove);
    animFrame = requestAnimationFrame(applyRotation);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      cancelAnimationFrame(animFrame);
      clearTimeout(idleTimeoutRef.current);
    };
  }, []);

  return (
    <span
      ref={compassRef}
      className="compass-logo flex h-9 w-9 items-center justify-center"
    >
      <svg
        width="36"
        height="36"
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="cmp-n" x1="0.3" y1="0" x2="0.7" y2="1">
            <stop offset="0%" stopColor="#0d4a5a" />
            <stop offset="100%" stopColor="#1a8a9a" />
          </linearGradient>
          <linearGradient id="cmp-s" x1="0.5" y1="0" x2="0.5" y2="1">
            <stop offset="0%" stopColor="#2da0b0" />
            <stop offset="100%" stopColor="#4cc0d0" />
          </linearGradient>
        </defs>

        {/* Outer ring */}
        <circle
          className="compass-ring"
          cx="20"
          cy="20"
          r="17"
          fill="none"
          stroke="#7a8494"
          strokeWidth="1.4"
          opacity="0.4"
        />

        {/* Inner structural ring */}
        <circle
          cx="20"
          cy="20"
          r="13.5"
          fill="none"
          stroke="#7a8494"
          strokeWidth="0.5"
          opacity="0.2"
        />

        {/* Cardinal markers: D-G-V-E */}
        {/* Top: G (Guide) — accent color to distinguish from D-E-V */}
        <polygon
          points="20,1 17,5 20,3 23,5"
          fill="#1a8a9a"
          opacity="0.7"
        />
        <text
          x="20"
          y="8.5"
          textAnchor="middle"
          fontSize="3.5"
          fontWeight="800"
          fontFamily="Inter, system-ui, sans-serif"
          fill="#1a9aaa"
          opacity="0.9"
        >
          G
        </text>
        {/* Left: D */}
        <polygon
          points="1,20 5,23 3,20 5,17"
          fill="#9aa4b4"
          opacity="0.45"
        />
        <text
          x="8"
          y="21.3"
          textAnchor="middle"
          fontSize="3.5"
          fontWeight="800"
          fontFamily="Inter, system-ui, sans-serif"
          fill="#b0bac8"
          opacity="0.65"
        >
          D
        </text>
        {/* Right: V */}
        <polygon
          points="39,20 35,17 37,20 35,23"
          fill="#9aa4b4"
          opacity="0.45"
        />
        <text
          x="32"
          y="21.3"
          textAnchor="middle"
          fontSize="3.5"
          fontWeight="800"
          fontFamily="Inter, system-ui, sans-serif"
          fill="#b0bac8"
          opacity="0.65"
        >
          V
        </text>
        {/* Bottom: E */}
        <polygon
          points="20,39 23,35 20,37 17,35"
          fill="#9aa4b4"
          opacity="0.4"
        />
        <text
          x="20"
          y="34"
          textAnchor="middle"
          fontSize="3.5"
          fontWeight="800"
          fontFamily="Inter, system-ui, sans-serif"
          fill="#b0bac8"
          opacity="0.65"
        >
          E
        </text>

        {/* Needle group — rotates to follow mouse */}
        <g
          ref={needleRef}
          className="compass-needle"
          style={{ transformOrigin: "20px 20px" }}
        >
          {/* North needle (dark teal) — angular barbed shape */}
          <path
            d="M20,3 L17,12 L14.5,17.5 L18,20 L20,17 L22,20 L25.5,17.5 L23,12 Z"
            fill="url(#cmp-n)"
          />
          {/* South needle (light teal) */}
          <path
            d="M20,37 L23,28 L25.5,22.5 L22,20 L20,23 L18,20 L14.5,22.5 L17,28 Z"
            fill="url(#cmp-s)"
            opacity="0.35"
          />
          {/* Center pivot */}
          <circle cx="20" cy="20" r="2" fill="#e2e8f0" />
          <circle cx="20" cy="20" r="1" fill="#0d4a5a" />
        </g>
      </svg>
    </span>
  );
}
