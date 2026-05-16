#!/usr/bin/env node
// muriel Mermaid → SVG / ASCII bridge (ESM).
//
// Reads  {"source": "...", "mode": "svg"|"ascii", "theme": "...", "colors": {...}, "options": {...}}
//       from stdin.
//
// Writes one of:
//   {"svg": "...", "width": <px>, "height": <px>}    on mode="svg"
//   {"ascii": "..."}                                  on mode="ascii"
//   {"error": "<message>"}                            on any failure
//
// beautiful-mermaid is shipped as an ESM-only package, so this bridge
// runs as .mjs. All renders are synchronous in the upstream package
// (no async, no DOM); we just shuttle stdin → stdout per invocation.

import { renderMermaidSVG, renderMermaidASCII, THEMES } from "beautiful-mermaid";

function read() {
  return new Promise((resolve, reject) => {
    let buf = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (c) => (buf += c));
    process.stdin.on("end", () => resolve(buf));
    process.stdin.on("error", reject);
  });
}

function emit(obj) {
  process.stdout.write(JSON.stringify(obj));
}

function buildRenderOpts(theme, colors, options) {
  const base = theme && THEMES && THEMES[theme] ? THEMES[theme] : {};
  // colors override theme; layout options stack on top
  return Object.assign({}, base, colors || {}, options || {});
}

function parseDimensions(svg) {
  // beautiful-mermaid emits width/height on the root <svg>.
  const wMatch = svg.match(/<svg[^>]*\swidth="([\d.]+)(?:px)?"/i);
  const hMatch = svg.match(/<svg[^>]*\sheight="([\d.]+)(?:px)?"/i);
  if (wMatch && hMatch) {
    return { width: parseFloat(wMatch[1]), height: parseFloat(hMatch[1]) };
  }
  // Fallback: derive from viewBox.
  const vb = svg.match(
    /viewBox="\s*([\d.\-]+)\s+([\d.\-]+)\s+([\d.]+)\s+([\d.]+)/
  );
  if (vb) {
    return { width: parseFloat(vb[3]), height: parseFloat(vb[4]) };
  }
  return { width: 0, height: 0 };
}

async function main() {
  let req;
  try {
    req = JSON.parse(await read());
  } catch (e) {
    emit({ error: `invalid input JSON: ${e.message}` });
    return;
  }

  const source = String(req.source || "");
  const mode = req.mode === "ascii" ? "ascii" : "svg";
  const opts = buildRenderOpts(req.theme, req.colors, req.options);

  if (mode === "ascii") {
    try {
      const text = renderMermaidASCII(source, opts);
      emit({ ascii: text });
    } catch (e) {
      emit({ error: String((e && e.message) || e) });
    }
    return;
  }

  let svg;
  try {
    svg = renderMermaidSVG(source, opts);
  } catch (e) {
    emit({ error: String((e && e.message) || e) });
    return;
  }

  if (!svg || typeof svg !== "string") {
    emit({ error: "renderMermaidSVG returned no output" });
    return;
  }

  const { width, height } = parseDimensions(svg);
  if (!width || !height) {
    emit({ error: `could not measure SVG dimensions: ${svg.slice(0, 200)}` });
    return;
  }

  // Surface the resolved bg/fg so Python-side flatteners can substitute
  // var() / color-mix() with concrete hex values when rasterizing.
  emit({
    svg,
    width,
    height,
    bg: opts.bg || "#FFFFFF",
    fg: opts.fg || "#27272A",
  });
}

main().catch((e) => {
  emit({ error: `unexpected: ${(e && (e.stack || e.message)) || e}` });
});
