"use client";

import { useEffect, useRef } from "react";

export default function HeroCompass() {
  const compassRef = useRef<HTMLDivElement>(null);
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
        let delta = targetRef.current - rotationRef.current;
        while (delta > 180) delta -= 360;
        while (delta < -180) delta += 360;
        rotationRef.current += delta * 0.08;
      } else {
        const t = performance.now() / 1000;
        const swayTarget =
          Math.sin(t * 0.4) * 15 + Math.cos(t * 0.27) * 8;
        rotationRef.current +=
          (swayTarget - rotationRef.current) * 0.02;
      }
      needleRef.current.style.transform = `rotate(${rotationRef.current}deg)`;
      animFrame = requestAnimationFrame(applyRotation);
    };

    const handleMouseMove = (e: MouseEvent) => {
      if (!compassRef.current) return;
      const rect = compassRef.current.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
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
    <div ref={compassRef} className="hero-compass">
      <svg
        viewBox="0 0 200 200"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="h-full w-full"
      >
        <defs>
          <linearGradient id="hero-n" x1="0.3" y1="0" x2="0.7" y2="1">
            <stop offset="0%" stopColor="#0d4a5a" />
            <stop offset="100%" stopColor="#1a8a9a" />
          </linearGradient>
          <linearGradient id="hero-s" x1="0.5" y1="0" x2="0.5" y2="1">
            <stop offset="0%" stopColor="#2da0b0" />
            <stop offset="100%" stopColor="#4cc0d0" />
          </linearGradient>
          <radialGradient id="hero-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#0d4a5a" stopOpacity="0.08" />
            <stop offset="100%" stopColor="#0d4a5a" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Ambient glow */}
        <circle cx="100" cy="100" r="98" fill="url(#hero-glow)" />

        {/* Outer ring */}
        <circle
          className="hero-compass-ring"
          cx="100"
          cy="100"
          r="85"
          fill="none"
          stroke="#7a8494"
          strokeWidth="2"
          opacity="0.3"
        />

        {/* Inner structural ring */}
        <circle
          cx="100"
          cy="100"
          r="68"
          fill="none"
          stroke="#7a8494"
          strokeWidth="1"
          opacity="0.15"
        />

        {/* Subtle degree ticks (every 30°) */}
        {[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map(
          (deg) => {
            const isCardinal = deg % 90 === 0;
            const r1 = isCardinal ? 80 : 82;
            const r2 = 85;
            const rad = (deg * Math.PI) / 180;
            return (
              <line
                key={deg}
                x1={100 + r1 * Math.sin(rad)}
                y1={100 - r1 * Math.cos(rad)}
                x2={100 + r2 * Math.sin(rad)}
                y2={100 - r2 * Math.cos(rad)}
                stroke="#7a8494"
                strokeWidth={isCardinal ? 0 : 0.8}
                opacity="0.2"
              />
            );
          }
        )}

        {/* Cardinal markers: D-E-V-G */}
        {/* Top: E */}
        <polygon
          points="100,5 90,22 100,14 110,22"
          fill="#9aa4b4"
          opacity="0.5"
        />
        <text
          x="100"
          y="44"
          textAnchor="middle"
          fontSize="18"
          fontWeight="800"
          fontFamily="Inter, system-ui, sans-serif"
          fill="#b0bac8"
          opacity="0.8"
        >
          E
        </text>

        {/* Left: D */}
        <polygon
          points="5,100 22,110 14,100 22,90"
          fill="#9aa4b4"
          opacity="0.45"
        />
        <text
          x="38"
          y="106"
          textAnchor="middle"
          fontSize="18"
          fontWeight="800"
          fontFamily="Inter, system-ui, sans-serif"
          fill="#b0bac8"
          opacity="0.75"
        >
          D
        </text>

        {/* Right: V */}
        <polygon
          points="195,100 178,90 186,100 178,110"
          fill="#9aa4b4"
          opacity="0.45"
        />
        <text
          x="162"
          y="106"
          textAnchor="middle"
          fontSize="18"
          fontWeight="800"
          fontFamily="Inter, system-ui, sans-serif"
          fill="#b0bac8"
          opacity="0.75"
        >
          V
        </text>

        {/* Bottom: G (Guide) */}
        <polygon
          points="100,195 110,178 100,186 90,178"
          fill="#9aa4b4"
          opacity="0.45"
        />
        <text
          x="100"
          y="176"
          textAnchor="middle"
          fontSize="18"
          fontWeight="800"
          fontFamily="Inter, system-ui, sans-serif"
          fill="#b0bac8"
          opacity="0.75"
        >
          G
        </text>

        {/* Inner < / > code symbols */}
        <text
          x="62"
          y="105"
          textAnchor="middle"
          fontSize="18"
          fontWeight="700"
          fontFamily="JetBrains Mono, monospace"
          fill="#4cc0d0"
          opacity="0.3"
        >
          &lt;
        </text>
        <text
          x="100"
          y="105"
          textAnchor="middle"
          fontSize="18"
          fontWeight="700"
          fontFamily="JetBrains Mono, monospace"
          fill="#4cc0d0"
          opacity="0.3"
        >
          /
        </text>
        <text
          x="138"
          y="105"
          textAnchor="middle"
          fontSize="18"
          fontWeight="700"
          fontFamily="JetBrains Mono, monospace"
          fill="#4cc0d0"
          opacity="0.3"
        >
          &gt;
        </text>

        {/* Needle group — rotates to follow mouse */}
        <g
          ref={needleRef}
          style={{ transformOrigin: "100px 100px" }}
        >
          {/* North needle — angular barbed shape */}
          <path
            d="M100,16 L87,60 L76,88 L92,100 L100,86 L108,100 L124,88 L113,60 Z"
            fill="url(#hero-n)"
          />
          {/* South needle */}
          <path
            d="M100,184 L113,140 L124,112 L108,100 L100,114 L92,100 L76,112 L87,140 Z"
            fill="url(#hero-s)"
            opacity="0.3"
          />
          {/* Center pivot */}
          <circle cx="100" cy="100" r="8" fill="#e2e8f0" />
          <circle cx="100" cy="100" r="4" fill="#0d4a5a" />
        </g>
      </svg>
    </div>
  );
}
