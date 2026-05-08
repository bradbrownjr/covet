#!/usr/bin/env node
/**
 * check-icons.mjs
 *
 * Walks web/src/ and flags:
 *   1. Bare <svg  elements in .svelte files outside the canonical Icon.svelte
 *      and branding/ directories.
 *   2. Unicode characters that are being used as icon glyphs rather than
 *      real text content (arrows, carets, × marks, etc.).
 *   3. <Icon name="…"> calls that reference a name not registered in ICON_MAP
 *      (these render silently blank at runtime).
 *
 * Allowlisted:
 *   - $lib/Icon.svelte (the canonical icon wrapper — contains real <svg>)
 *   - static/branding/ and src/...branding/ directories
 *   - User-authored content placeholders (notes, captions, comments copy)
 *
 * Exit 0 = clean.  Exit 1 = violations found.
 *
 * Usage:  node scripts/check-icons.mjs
 */

import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SRC_DIR = path.resolve(__dirname, '../src');

// ── Known-good icon names (must match ICON_MAP keys in Icon.svelte) ───────────
const REGISTERED_ICONS = new Set([
  'arrow-down', 'arrow-up', 'bell', 'box', 'check',
  'chevron-left', 'chevron-right', 'circle-alert', 'corner-down-right',
  'database-backup', 'download',
  'file-archive', 'file-cog', 'file-spreadsheet',
  'folder', 'grid-2x2',
  'home', 'house', 'list',
  'map-pin', 'more-horizontal',
  'palette', 'pencil',
  'settings', 'settings-2', 'shield', 'shopping-cart', 'sliders-horizontal',
  'sparkles', 'star', 'store',
  'trash-2', 'triangle-alert',
  'upload', 'user', 'users',
  'wrench', 'x',
]);

// ── Allowlisted paths (substring match against the resolved file path) ────────
const PATH_ALLOWLIST = [
  path.join('lib', 'Icon.svelte'),        // canonical icon wrapper
  path.join('static', 'branding'),        // static brand SVGs
  path.sep + 'branding' + path.sep,       // any branding/ directory
];

// ── Emoji / Unicode glyphs that should be replaced with <Icon> ───────────────
// Each entry: [regex, description].
// We deliberately do NOT flag punctuation like …, —, ·, ›, ×, &, etc. that
// appear in real prose.  We only flag characters that appear naked in
// button/label context as icon substitutes.
const GLYPH_PATTERNS = [
  // Arrow glyphs used for navigation/sorting
  [/[↑↓←→↗↘↙↖⇑⇓⇐⇒]/, 'directional arrow glyph — use <Icon name="arrow-*" />'],
  // Triangle carets used for open/close toggles
  [/[▴▾▲▼▸◂]/, 'triangle caret glyph — use <Icon name="chevron-*" />'],
  // Heavy ×/✕ close marks
  [/[✕✗✖]/, 'heavy cross glyph — use <Icon name="x" />'],
  // Check/tick marks used as status icons
  [/[✓✔✅]/, 'check mark glyph — use <Icon name="check" />'],
  // Emoji that appear as UI icons (not in prose)
  [/[\u{1F4E6}\u{1F50D}\u{1F5D1}\u{26A0}\u{1F3F7}]/u, 'emoji used as UI icon — use <Icon>'],
];

// Lines whose content is clearly prose/copy (not a button/element), skip glyph check.
// We skip lines that look like comments, aria-labels or placeholder text.
const GLYPH_LINE_ALLOWLIST = [
  /placeholder=/,
  /aria-label=/,
  /\/\/.*glyph/i,  // developer comments noting intentional usage
  /<!-- /, // HTML comments
  /^\s*\/\//, // single-line JS/TS comment
  /^\s*\*/, // inside /* … */ or /** … */ block comment
  /^\s*\/\*/, // opening of block comment
  /content:\s*['"]/, // CSS content: '…' pseudo-element property
];

// ── File walker ───────────────────────────────────────────────────────────────
async function* walkSvelte(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === 'node_modules' || entry.name === '.svelte-kit') continue;
      yield* walkSvelte(full);
    } else if (entry.isFile() && entry.name.endsWith('.svelte')) {
      yield full;
    }
  }
}

function isAllowlisted(filePath) {
  return PATH_ALLOWLIST.some((al) => filePath.includes(al));
}

// ── Main ──────────────────────────────────────────────────────────────────────
let violations = 0;

for await (const filePath of walkSvelte(SRC_DIR)) {
  if (isAllowlisted(filePath)) continue;

  const rel = path.relative(path.resolve(__dirname, '..'), filePath);
  const text = await readFile(filePath, 'utf8');
  const lines = text.split('\n');

  lines.forEach((line, i) => {
    const lineNo = i + 1;

    // 1. Bare <svg element
    if (/<svg\s/.test(line)) {
      console.error(`${rel}:${lineNo}: bare <svg> — use <Icon name="…" /> instead`);
      violations++;
    }

    // 2. Unicode glyph icons (skip allowlisted line patterns)
    if (GLYPH_LINE_ALLOWLIST.some((re) => re.test(line))) return;
    for (const [pattern, message] of GLYPH_PATTERNS) {
      if (pattern.test(line)) {
        console.error(`${rel}:${lineNo}: ${message}`);
        console.error(`  > ${line.trim()}`);
        violations++;
        break; // one violation per line
      }
    }

    // 3. <Icon name="..."> referencing an unregistered icon name
    const iconMatches = line.matchAll(/Icon[^>]+name=["']([^"']+)["']/g);
    for (const m of iconMatches) {
      const iconName = m[1];
      if (!REGISTERED_ICONS.has(iconName)) {
        console.error(`${rel}:${lineNo}: <Icon name="${iconName}"> is not registered in ICON_MAP — add it to Icon.svelte and REGISTERED_ICONS`);
        console.error(`  > ${line.trim()}`);
        violations++;
      }
    }
  });
}

if (violations > 0) {
  console.error(`\ncheck-icons: ${violations} violation(s) found.`);
  process.exit(1);
} else {
  console.log('check-icons: OK — no stray SVGs or glyph icons found.');
}
