"use client";

import { useEffect, useRef, useState } from "react";

export default function GyroCompass() {
  const needleRef = useRef<SVGGElement>(null);
  const [rotation, setRotation] = useState(0);
  const [hasGyro, setHasGyro] = useState(false);
  const animFrame = useRef<number>(0);
  const targetRotation = useRef(0);

  useEffect(() => {
    let active = true;

    function handleOrientation(e: DeviceOrientationEvent) {
      if (e.alpha != null) {
        setHasGyro(true);
        targetRotation.current = e.alpha;
      }
    }

    // Smooth animation loop — lerp toward target
    function animate() {
      if (!active) return;
      setRotation((prev) => {
        const target = targetRotation.current;
        let diff = target - prev;
        if (diff > 180) diff -= 360;
        if (diff < -180) diff += 360;
        return prev + diff * 0.1;
      });
      animFrame.current = requestAnimationFrame(animate);
    }

    if (
      typeof DeviceOrientationEvent !== "undefined" &&
      typeof (DeviceOrientationEvent as any).requestPermission === "function"
    ) {
      window.addEventListener("deviceorientation", handleOrientation);
    } else if (typeof window !== "undefined" && "DeviceOrientationEvent" in window) {
      window.addEventListener("deviceorientation", handleOrientation);
    }

    animFrame.current = requestAnimationFrame(animate);

    return () => {
      active = false;
      cancelAnimationFrame(animFrame.current);
      window.removeEventListener("deviceorientation", handleOrientation);
    };
  }, []);

  async function requestPermission() {
    if (
      typeof DeviceOrientationEvent !== "undefined" &&
      typeof (DeviceOrientationEvent as any).requestPermission === "function"
    ) {
      try {
        const perm = await (DeviceOrientationEvent as any).requestPermission();
        if (perm === "granted") {
          setHasGyro(true);
        }
      } catch {
        // User denied
      }
    }
  }

  // On desktop: needle follows mouse cursor
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (hasGyro) return;

    function handleMouseMove(e: MouseEvent) {
      const svg = svgRef.current;
      if (!svg) return;
      const rect = svg.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const angle = Math.atan2(e.clientX - cx, -(e.clientY - cy)) * (180 / Math.PI);
      targetRotation.current = angle;
    }

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [hasGyro]);

  return (
    <div
      className="relative select-none"
      onClick={requestPermission}
      role="img"
      aria-label="Interactive compass"
    >
      <svg
        ref={svgRef}
        viewBox="0 0 200 200"
        className="h-28 w-28 sm:h-36 sm:w-36 drop-shadow-lg"
        style={{ filter: "drop-shadow(0 0 12px rgba(77,184,201,0.3))" }}
      >
        <defs>
          <linearGradient id="gyro-needle-dark" x1="0.2" y1="0" x2="0.8" y2="1">
            <stop offset="0%" stopColor="#0a3d47" />
            <stop offset="50%" stopColor="#126068" />
            <stop offset="100%" stopColor="#1a7a8a" />
          </linearGradient>
          <linearGradient id="gyro-needle-mid" x1="0.2" y1="0" x2="0.8" y2="1">
            <stop offset="0%" stopColor="#16636f" />
            <stop offset="100%" stopColor="#3aafbf" />
          </linearGradient>
          <linearGradient id="gyro-needle-lo-dark" x1="0.8" y1="1" x2="0.2" y2="0">
            <stop offset="0%" stopColor="#0e4e58" />
            <stop offset="100%" stopColor="#1a7a8a" />
          </linearGradient>
          <linearGradient id="gyro-needle-lo-light" x1="0.8" y1="1" x2="0.2" y2="0">
            <stop offset="0%" stopColor="#2a8a96" />
            <stop offset="100%" stopColor="#5bc4d4" />
          </linearGradient>
          <linearGradient id="gyro-ring" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#c0c4cc" />
            <stop offset="50%" stopColor="#a0a6b0" />
            <stop offset="100%" stopColor="#c0c4cc" />
          </linearGradient>
          <linearGradient id="gyro-rose" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#1a7a8a" />
            <stop offset="100%" stopColor="#2a9aaa" />
          </linearGradient>
        </defs>

        {/* Static outer ring */}
        <circle cx="100" cy="100" r="90" fill="none" stroke="url(#gyro-ring)" strokeWidth="10" opacity="0.55" />
        {/* Static inner ring */}
        <circle cx="100" cy="100" r="70" fill="none" stroke="url(#gyro-ring)" strokeWidth="6" opacity="0.35" />

        {/* Rotating group: compass rose + needle */}
        <g ref={needleRef} transform={`rotate(${rotation}, 100, 100)`}>
          {/* Compass rose — 4 pointed star arms */}
          <polygon points="100,8 80,68 100,54 120,68" fill="url(#gyro-rose)" opacity="0.9" />
          <polygon points="100,192 120,132 100,146 80,132" fill="url(#gyro-rose)" opacity="0.9" />
          <polygon points="192,100 132,80 146,100 132,120" fill="url(#gyro-rose)" opacity="0.9" />
          <polygon points="8,100 68,120 54,100 68,80" fill="url(#gyro-rose)" opacity="0.9" />

          {/* Wide blade needle — top-right to bottom-left */}
          <polygon points="156,16 100,100 72,80" fill="url(#gyro-needle-dark)" />
          <polygon points="156,16 100,100 120,128" fill="url(#gyro-needle-mid)" opacity="0.9" />
          <polygon points="44,184 100,100 128,120" fill="url(#gyro-needle-lo-dark)" opacity="0.6" />
          <polygon points="44,184 100,100 80,72" fill="url(#gyro-needle-lo-light)" opacity="0.75" />
        </g>

        {/* Center dot (stays fixed) */}
        <circle cx="100" cy="100" r="9" fill="white" />
        <circle cx="100" cy="100" r="5.5" fill="#e8eaed" />
      </svg>

      {!hasGyro && (
        <p
          className="absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px] sm:hidden"
          style={{ color: "var(--text-muted)" }}
        >
          Tap to enable compass
        </p>
      )}
    </div>
  );
}
