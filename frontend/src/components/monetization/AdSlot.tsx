"use client";

import { ADSENSE_ID } from "@/lib/config";

interface AdSlotProps {
  position: string;
  className?: string;
}

export default function AdSlot({ position, className = "" }: AdSlotProps) {
  if (!ADSENSE_ID) return null;

  return (
    <div
      className={`flex items-center justify-center ${className}`}
      aria-label="Advertisement"
      data-ad-position={position}
      style={{ minHeight: "90px" }}
    >
      {/* Google AdSense auto-ads handle placement when ADSENSE_ID is set */}
    </div>
  );
}
