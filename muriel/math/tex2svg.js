#!/usr/bin/env node
// muriel TeX → SVG bridge.
//
// Reads  {"tex": "...", "display": false, "ex": 6.5}  from stdin.
// Writes {"svg": "...", "width": <px>, "height": <px>}  to stdout.
// On any failure, writes {"error": "<message>"} to stdout and exits 0
// (Python side decides whether that's fatal).
//
// Output SVG is self-contained: fontCache:"none" inlines every glyph
// as <path> data with no <defs> sharing, so the fragment drops into
// any container without an external dependency.

const { mathjax } = require("mathjax-full/js/mathjax.js");
const { TeX } = require("mathjax-full/js/input/tex.js");
const { SVG } = require("mathjax-full/js/output/svg.js");
const { liteAdaptor } = require("mathjax-full/js/adaptors/liteAdaptor.js");
const { RegisterHTMLHandler } = require("mathjax-full/js/handlers/html.js");
const { AllPackages } = require("mathjax-full/js/input/tex/AllPackages.js");

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

async function main() {
  let req;
  try {
    req = JSON.parse(await read());
  } catch (e) {
    emit({ error: `invalid input JSON: ${e.message}` });
    return;
  }

  const tex = String(req.tex || "");
  const isDisplay = !!req.display;
  const ex = Number.isFinite(req.ex) && req.ex > 0 ? req.ex : 6.5;
  // em = ex * 2 — MathJax's internal convention.
  const em = ex * 2;

  // Drop the "noundefined" extension so unknown macros throw a real
  // exception (which we catch below) instead of rendering as red text.
  // Bad TeX must fail loud — silent garbage in figures is what the
  // muriel layout discipline exists to prevent.
  const packages = AllPackages.filter((p) => p !== "noundefined");

  const adaptor = liteAdaptor();
  RegisterHTMLHandler(adaptor);
  const input = new TeX({ packages });
  const output = new SVG({ fontCache: "none" });
  const doc = mathjax.document("", { InputJax: input, OutputJax: output });

  let node;
  try {
    node = doc.convert(tex, {
      display: isDisplay,
      em,
      ex,
      containerWidth: 1280,
    });
  } catch (e) {
    emit({ error: String((e && e.message) || e) });
    return;
  }

  // mjx-container wraps the <svg>; we want just the inner SVG element.
  const inner = adaptor.firstChild(node);
  if (!inner) {
    emit({ error: "no SVG produced (likely empty TeX)" });
    return;
  }
  const svg = adaptor.outerHTML(inner);

  // MathJax inserts a <g data-mml-node="merror"> for unknown macros and
  // malformed TeX instead of throwing. Surface that as an explicit error
  // so callers can fail loudly rather than embed a red glyph.
  if (svg.indexOf('data-mml-node="merror"') !== -1) {
    const reason = svg.match(/<title>([^<]+)<\/title>/);
    emit({
      error: `TeX parse error${reason ? `: ${reason[1]}` : ""}`,
    });
    return;
  }

  // MathJax writes the SVG with width/height in ex units. Convert to px
  // using the caller's ex value so the bbox lines up with surrounding
  // text at the same font-size.
  const m = svg.match(/width="([\d.]+)ex"[^>]*height="([\d.]+)ex"/);
  if (!m) {
    emit({
      error: `could not parse SVG dimensions in: ${svg.slice(0, 200)}`,
    });
    return;
  }
  const widthPx = parseFloat(m[1]) * ex;
  const heightPx = parseFloat(m[2]) * ex;

  emit({ svg, width: widthPx, height: heightPx });
}

main().catch((e) => {
  emit({ error: `unexpected: ${(e && (e.stack || e.message)) || e}` });
});
