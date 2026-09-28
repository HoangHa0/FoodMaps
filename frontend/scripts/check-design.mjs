#!/usr/bin/env node
/**
 * Keeps visual decisions inside src/ui, so the look can be redesigned without touching features.
 * Scans src/features and src/app and fails on:
 *   - hard-coded colours: #fff, #e11d48, rgb(...), hsl(...), oklch(...)
 *   - Tailwind arbitrary values for colour/radius/shadow: bg-[#..], text-[..], rounded-[..], shadow-[..]
 * Layout utilities (flex, gap-4, p-6, w-full, max-w-md, ...) are fine: layout belongs to features.
 * Deliberate exception: add a `design-ok: <reason>` comment on the same line.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";

const ROOTS = ["src/features", "src/app"];
const ALLOW_FILES = [/src\/app\/globals\.css$/];
// Normalise Windows "\" separators before matching paths against regexes.
const posix = (p) => p.split(sep).join("/");
const RULES = [
  [/#[0-9a-fA-F]{3,8}\b(?![\w-])/, "hex colour: use a token class (bg-primary, text-fg-muted, ...)"],
  [/\b(rgb|rgba|hsl|hsla|oklch)\(/, "colour function: define colours in src/ui/themes/*.css"],
  [
    /\b(bg|text|border|ring|fill|stroke|from|to|via|shadow|rounded)-\[[^\]]+\]/,
    "arbitrary value: add a token or a component variant in src/ui",
  ],
];

const files = [];
const walk = (d) => {
  for (const f of readdirSync(d)) {
    const p = join(d, f);
    if (statSync(p).isDirectory()) walk(p);
    else if (/\.(tsx?|css)$/.test(f) && !ALLOW_FILES.some((r) => r.test(posix(p)))) files.push(p);
  }
};
ROOTS.forEach(walk);

let bad = 0;
for (const f of files) {
  readFileSync(f, "utf8")
    .split(/\r?\n/)
    .forEach((line, i) => {
      if (line.includes("design-ok")) return;
      for (const [re, msg] of RULES) {
        if (re.test(line)) {
          bad++;
          console.error(`${posix(relative(".", f))}:${i + 1}  ${msg}\n    ${line.trim()}`);
        }
      }
    });
}
if (bad) {
  console.error(`\n[ERROR] ${bad} style value(s) outside the design system.`);
  process.exit(1);
}
console.log(`[OK] check:design: ${files.length} files clean`);
