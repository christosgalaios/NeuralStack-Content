import { readFileSync } from "fs";
import sharp from "sharp";

const svg = readFileSync("public/icon.svg");
const sizes = [
  { name: "favicon-16x16.png", size: 16 },
  { name: "favicon-32x32.png", size: 32 },
  { name: "apple-touch-icon.png", size: 180 },
  { name: "icon-192x192.png", size: 192 },
  { name: "icon-512x512.png", size: 512 },
];

for (const { name, size } of sizes) {
  await sharp(svg).resize(size, size).png().toFile(`public/${name}`);
  console.log(`Generated ${name} (${size}x${size})`);
}
