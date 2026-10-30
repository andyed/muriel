// muriel.line_ends — the in-page half of the line-end check.
//
// Every open end of every checked stroke must land: within `tolerance`
// (viewBox px) of another stroke, a shape's outline, a dot, a text label,
// or the canvas edge; or under a fill painted after it; or on an implied
// edge that at least `fence` other ends line up on. A short straight mark
// (a tick, up to `mark` px) needs only one end rooted. An end marked
// data-free="start" | "end" | "both" (or bare data-free) is meant to stop.
//
// Ported from anatomy's scripts/line-ends.mjs
// (github.com/wheresryan22/anatomy, MIT, Copyright (c) 2026 Ryan; the
// license is reproduced in THIRD_PARTY_NOTICES.md). The path parser, the
// spatial grid, the under-a-fill test and the short-mark rule are
// anatomy's. What muriel changed, and why:
//   - Lines are chosen by geometry, not by a kit class: any stroked,
//     unfilled path/line/polyline, or whatever `lines` selects.
//   - Filled shapes count as landing targets through their outline, not
//     only through their stroke. muriel diagrams use flat fills with no
//     outline, and a connector touching a flat node is landed.
//   - Text labels are targets, with their own `textGap`, because a leader
//     that stops short of its label by a few px of padding is the
//     convention, not a fault.
//   - An end with an arrowhead marker gets the marker's reach, because a
//     generator may stop the path where the arrow's base sits.
//   - Aligned ends form an implied edge: gridlines that all stop at an
//     unstroked plot boundary read as one contour, so `fence` or more ends
//     arriving square-on to one vertical or horizontal line pass each other.
//     A near miss (anything within `nearMiss` px) is never fenced: that is
//     the defect itself, and a generator that repeats it at every node
//     would otherwise fence its own bug.
//   - The canvas edge is a target, so a rule that bleeds off the frame
//     lands.
//   - Works in a standalone SVG document as well as HTML, and returns
//     client coordinates for the caller to ring instead of drawing an
//     overlay into the page.
(options = {}) => {
  const {
    root: rootSelector = null,
    lines: lineSelector = null,
    tolerance = 1,
    rooted: rootSlack = 2,
    mark = 7,
    least = 0.3,
    cover = 0.5,
    textGap = 4,
    fence = 3,
    nearMiss = 6,
  } = options;

  const SVG_NS = "http://www.w3.org/2000/svg";
  const isSvgDoc = document.documentElement instanceof SVGSVGElement;
  const root = rootSelector
    ? document.querySelector(rootSelector)
    : (isSvgDoc ? document.documentElement : document.body || document.documentElement);
  if (!root) throw new Error(`line-ends root not found: ${rootSelector}`);

  // elementsFromPoint only reports what is hittable. Make every SVG shape
  // hittable and everything else (HTML overlays, captions) transparent to
  // the probe, so "is a fill painted over this end" asks the drawing.
  const style = isSvgDoc ? document.createElementNS(SVG_NS, "style") : document.createElement("style");
  style.textContent = isSvgDoc
    ? "svg, svg * { pointer-events: visiblePainted !important; }"
    : "body * { pointer-events: none !important; } svg, svg * { pointer-events: visiblePainted !important; }";
  (isSvgDoc ? document.documentElement : document.head || document.documentElement).append(style);

  const svgs = [...(root instanceof SVGSVGElement ? [root] : []), ...root.querySelectorAll("svg")];
  const offstage = "defs, clipPath, mask, pattern, marker, symbol";
  const shapes = svgs
    .flatMap((svg) => [...svg.querySelectorAll("path, line, polyline, polygon, circle, ellipse, rect")])
    .filter((el) => !el.closest(offstage));
  const texts = svgs
    .flatMap((svg) => [...svg.querySelectorAll("text")])
    .filter((el) => !el.closest(offstage) && el.textContent.trim());
  const chosen = lineSelector ? new Set(root.querySelectorAll(lineSelector)) : null;

  const opacityOf = (el) => {
    let alpha = 1;
    for (let node = el; node && node.nodeType === 1; node = node.parentElement) {
      const cs = getComputedStyle(node);
      if (cs.display === "none") return 0;
      alpha *= Number(cs.opacity);
      if (node === root) break;
    }
    return getComputedStyle(el).visibility === "hidden" ? 0 : alpha;
  };

  const numbers = (text) => (text.match(/-?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?/gi) || []).map(Number);

  // Flatten a path's d into subpaths of points. Curves are subdivided until
  // each piece is within curveTolerance of its chord, so an end is located
  // on the curve the browser draws, not on a control polygon.
  const subpathsOf = (d, curveTolerance) => {
    const out = [];
    let current = null;
    let x = 0;
    let y = 0;
    let sx = 0;
    let sy = 0;
    let control = null;
    const push = (px, py) => {
      current.points.push([px, py]);
      x = px;
      y = py;
    };
    const start = (px, py) => {
      current = { points: [[px, py]], closed: false };
      out.push(current);
      x = sx = px;
      y = sy = py;
    };
    let curveBudget = 16384;
    const chordDistance = (point, first, last) => {
      const dx = last[0] - first[0];
      const dy = last[1] - first[1];
      const span = dx * dx + dy * dy;
      const along = span > 0 ? Math.max(0, Math.min(1, ((point[0] - first[0]) * dx + (point[1] - first[1]) * dy) / span)) : 0;
      return Math.hypot(point[0] - first[0] - along * dx, point[1] - first[1] - along * dy);
    };
    const curve = (points) => {
      const pending = [points];
      while (pending.length) {
        if (--curveBudget < 0) throw new Error("line-ends could not bound its curve sampling");
        const controlPoints = pending.pop();
        const first = controlPoints[0];
        const last = controlPoints[controlPoints.length - 1];
        if (controlPoints.slice(1, -1).every((point) => chordDistance(point, first, last) <= curveTolerance)) {
          push(...last);
          continue;
        }
        // de Casteljau split at t = 0.5.
        const left = [first];
        const right = [last];
        let level = controlPoints;
        while (level.length > 1) {
          level = level.slice(1).map((point, index) => [(level[index][0] + point[0]) / 2, (level[index][1] + point[1]) / 2]);
          left.push(level[0]);
          right.push(level[level.length - 1]);
        }
        pending.push(right.reverse(), left);
      }
    };
    const cubic = (x1, y1, x2, y2, px, py) => {
      curve([[x, y], [x1, y1], [x2, y2], [px, py]]);
      control = { kind: "cubic", point: [x2, y2] };
    };
    const quad = (x1, y1, px, py) => {
      curve([[x, y], [x1, y1], [px, py]]);
      control = { kind: "quadratic", point: [x1, y1] };
    };
    for (const [, command, args] of d.matchAll(/([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)/g)) {
      const v = numbers(args);
      const rel = command === command.toLowerCase();
      const C = command.toUpperCase();
      const ox = () => (rel ? x : 0);
      const oy = () => (rel ? y : 0);
      if (C === "Z") {
        if (current) {
          current.closed = true;
          push(sx, sy);
        }
        current = null;
        continue;
      }
      if (C === "M") {
        for (let i = 0; i + 1 < v.length; i += 2) {
          if (i === 0) start(v[0] + ox(), v[1] + oy());
          else push(v[i] + ox(), v[i + 1] + oy());
        }
        control = null;
        continue;
      }
      if (!current) start(x, y);
      if (C === "L") for (let i = 0; i + 1 < v.length; i += 2) push(v[i] + ox(), v[i + 1] + oy());
      else if (C === "H") for (const value of v) push(value + ox(), y);
      else if (C === "V") for (const value of v) push(x, value + oy());
      else if (C === "C") for (let i = 0; i + 5 < v.length; i += 6) cubic(v[i] + ox(), v[i + 1] + oy(), v[i + 2] + ox(), v[i + 3] + oy(), v[i + 4] + ox(), v[i + 5] + oy());
      else if (C === "S")
        for (let i = 0; i + 3 < v.length; i += 4) {
          const reflected = control?.kind === "cubic" ? [2 * x - control.point[0], 2 * y - control.point[1]] : [x, y];
          cubic(reflected[0], reflected[1], v[i] + ox(), v[i + 1] + oy(), v[i + 2] + ox(), v[i + 3] + oy());
        }
      else if (C === "Q") for (let i = 0; i + 3 < v.length; i += 4) quad(v[i] + ox(), v[i + 1] + oy(), v[i + 2] + ox(), v[i + 3] + oy());
      else if (C === "T")
        for (let i = 0; i + 1 < v.length; i += 2) {
          const reflected = control?.kind === "quadratic" ? [2 * x - control.point[0], 2 * y - control.point[1]] : [x, y];
          quad(reflected[0], reflected[1], v[i] + ox(), v[i + 1] + oy());
        }
      else if (C === "A") {
        // Arcs are sampled through the browser's own geometry rather than
        // re-deriving the endpoint parameterization here.
        const arc = document.createElementNS(SVG_NS, "path");
        arc.setAttribute("d", `M${x} ${y}${command}${args}`);
        const length = arc.getTotalLength();
        const count = Math.max(8, Math.ceil(length / 2));
        for (let index = 1; index <= count; index++) {
          const point = arc.getPointAtLength(length * index / count);
          push(point.x, point.y);
        }
      }
      if (C !== "C" && C !== "S" && C !== "Q" && C !== "T") control = null;
    }
    return out;
  };

  const geometryOf = (el, curveTolerance) => {
    const tag = el.tagName.toLowerCase();
    const num = (name) => Number(el.getAttribute(name) || 0);
    if (tag === "path") return subpathsOf(el.getAttribute("d") || "", curveTolerance);
    if (tag === "line") return [{ points: [[num("x1"), num("y1")], [num("x2"), num("y2")]], closed: false }];
    if (tag === "polyline" || tag === "polygon") {
      const v = numbers(el.getAttribute("points") || "");
      const points = [];
      for (let i = 0; i + 1 < v.length; i += 2) points.push([v[i], v[i + 1]]);
      if (tag === "polygon" && points.length) points.push(points[0]);
      return [{ points, closed: tag === "polygon" }];
    }
    if (tag === "rect") {
      const [x, y, w, h] = [num("x"), num("y"), num("width"), num("height")];
      const rx = Math.min(w / 2, Math.max(0, el.hasAttribute("rx") ? num("rx") : num("ry")));
      const ry = Math.min(h / 2, Math.max(0, el.hasAttribute("ry") ? num("ry") : num("rx")));
      if (!rx || !ry) return [{ points: [[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]], closed: true }];
      const points = [];
      for (const [cx, cy, begin] of [[x + w - rx, y + ry, -Math.PI / 2], [x + w - rx, y + h - ry, 0], [x + rx, y + h - ry, Math.PI / 2], [x + rx, y + ry, Math.PI]]) {
        for (let index = 0; index <= 32; index++) {
          const angle = begin + index * Math.PI / 64;
          points.push([cx + rx * Math.cos(angle), cy + ry * Math.sin(angle)]);
        }
      }
      points.push(points[0]);
      return [{ points, closed: true }];
    }
    return [];
  };

  // A 6 px spatial grid over client space keeps each end's search local.
  const cell = 6;
  const grid = new Map();
  const add = (gx, gy, entry) => {
    const id = `${gx},${gy}`;
    if (!grid.has(id)) grid.set(id, []);
    grid.get(id).push(entry);
  };
  const addBox = (entry, points) => {
    const xs = points.map(([px]) => px);
    const ys = points.map(([, py]) => py);
    for (let gx = Math.floor(Math.min(...xs) / cell); gx <= Math.floor(Math.max(...xs) / cell); gx++)
      for (let gy = Math.floor(Math.min(...ys) / cell); gy <= Math.floor(Math.max(...ys) / cell); gy++) add(gx, gy, entry);
  };

  const strokeWidthOf = (cs) => parseFloat(cs.strokeWidth) || 0;
  const markerReach = (el, cs, which) => {
    // How far an arrowhead extends past the path end, in user units. With
    // orient="auto" the marker's x axis runs along the path, so at the end
    // it reaches markerWidth − refX forward; at the start it reaches refX
    // backward, or markerWidth − refX when orient="auto-start-reverse".
    // A marker whose tip sits at refX adds nothing, so a tip that stops
    // short of its node still fails.
    const value = which === "start" ? cs.markerStart : cs.markerEnd;
    const match = value && value !== "none" && value.match(/#([^"')]+)/);
    if (!match) return 0;
    const marker = document.getElementById(match[1]);
    if (!marker) return 0;
    const w = Number(marker.getAttribute("markerWidth") || 3);
    const refX = Number(marker.getAttribute("refX") || 0);
    const reversed = marker.getAttribute("orient") === "auto-start-reverse";
    const units = marker.getAttribute("markerUnits") || "strokeWidth";
    const along = which === "end" || reversed ? w - refX : refX;
    return Math.max(0, along) * (units === "strokeWidth" ? strokeWidthOf(cs) : 1);
  };

  const lines = [];
  let scale = 1;
  const canvases = [];
  for (const svg of svgs) {
    const r = svg.getBoundingClientRect();
    if (r.width && r.height) canvases.push(r);
  }
  for (const el of shapes) {
    const cs = getComputedStyle(el);
    const alpha = opacityOf(el);
    if (alpha < 0.1) continue;
    const ctm = el.getScreenCTM();
    if (!ctm) continue;
    const map = ([px, py]) => [ctm.a * px + ctm.c * py + ctm.e, ctm.b * px + ctm.d * py + ctm.f];
    const tag = el.tagName.toLowerCase();
    const stroked = cs.stroke !== "none" && strokeWidthOf(cs) > 0 && Number(cs.strokeOpacity) > 0.05;
    const filled = cs.fill !== "none" && Number(cs.fillOpacity) > 0.05;
    if (!stroked && !filled) continue;
    if (tag === "circle" || tag === "ellipse") {
      const cx = Number(el.getAttribute("cx") || 0);
      const cy = Number(el.getAttribute("cy") || 0);
      const rx = Number(el.getAttribute(tag === "circle" ? "r" : "rx") || 0);
      const ry = Number(el.getAttribute(tag === "circle" ? "r" : "ry") || 0);
      if (rx <= 0 || ry <= 0) continue;
      const points = Array.from({ length: 128 }, (_, index) => {
        const angle = index * Math.PI * 2 / 128;
        return map([cx + rx * Math.cos(angle), cy + ry * Math.sin(angle)]);
      });
      addBox({ el, kind: "round", points, cx, cy, rx, ry, filled }, points);
      continue;
    }
    const owner = el.closest("svg");
    const viewCtm = owner && owner.getScreenCTM();
    if (viewCtm) scale = Math.hypot(viewCtm.a, viewCtm.b) || scale;
    const curveTolerance = 0.15 / Math.max(1, Math.hypot(ctm.a, ctm.b, ctm.c, ctm.d));
    const subpaths = geometryOf(el, curveTolerance).map((sub, index) => ({ ...sub, index, flat: sub.points.map(map) }));
    // Every painted edge is a target: the stroke of a stroked shape, the
    // outline of a filled one. A filled open path is closed for its fill.
    subpaths.forEach((sub) => {
      const flat = filled && !sub.closed && sub.flat.length > 2 ? [...sub.flat, sub.flat[0]] : sub.flat;
      for (let i = 0; i < flat.length - 1; i++) {
        const a = flat[i];
        const b = flat[i + 1];
        addBox({ el, kind: "segment", a, b, sub: sub.index, i }, [a, b]);
      }
    });
    const checked = chosen
      ? chosen.has(el)
      : stroked && !filled && (tag === "path" || tag === "line" || tag === "polyline");
    if (checked && alpha >= least) {
      lines.push({ el, cs, subpaths, alpha, free: el.getAttribute("data-free") });
    }
  }
  for (const el of texts) {
    const ctm = el.getScreenCTM();
    if (!ctm || opacityOf(el) < 0.1) continue;
    let box;
    try {
      box = el.getBBox();
    } catch {
      continue;
    }
    if (!box.width || !box.height) continue;
    const map = ([px, py]) => [ctm.a * px + ctm.c * py + ctm.e, ctm.b * px + ctm.d * py + ctm.f];
    const points = [[box.x, box.y], [box.x + box.width, box.y], [box.x + box.width, box.y + box.height], [box.x, box.y + box.height]].map(map);
    addBox({ el, kind: "text", points }, points);
  }

  const near = (p, reach) => {
    const out = new Set();
    for (let gx = Math.floor((p[0] - reach) / cell); gx <= Math.floor((p[0] + reach) / cell); gx++)
      for (let gy = Math.floor((p[1] - reach) / cell); gy <= Math.floor((p[1] + reach) / cell); gy++)
        for (const entry of grid.get(`${gx},${gy}`) || []) out.add(entry);
    return out;
  };
  const segmentDistance = (p, a, b) => {
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    const span = dx * dx + dy * dy;
    const t = span > 0 ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / span)) : 0;
    return Math.hypot(p[0] - a[0] - dx * t, p[1] - a[1] - dy * t);
  };
  const inPolygon = (p, points) => {
    let inside = false;
    for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
      const [xi, yi] = points[i];
      const [xj, yj] = points[j];
      if ((yi > p[1]) !== (yj > p[1]) && p[0] < ((xj - xi) * (p[1] - yi)) / (yj - yi) + xi) inside = !inside;
    }
    return inside;
  };
  const lengthOf = (flat) => flat.reduce((sum, p, i) => (i ? sum + Math.hypot(p[0] - flat[i - 1][0], p[1] - flat[i - 1][1]) : 0), 0);
  const inverse = (node, p) => {
    const m = node.getScreenCTM().inverse();
    return [m.a * p[0] + m.c * p[1] + m.e, m.b * p[0] + m.d * p[1] + m.f];
  };
  // An end that a fill painted later covers is hidden, which is landed.
  const hidden = (el, p) => {
    const stack = document.elementsFromPoint(p[0], p[1]);
    const at = stack.indexOf(el);
    const above = at < 0 ? stack : stack.slice(0, at);
    return above.some((node) => {
      if (!(node instanceof SVGGeometryElement) || node.contains(el)) return false;
      const cs = getComputedStyle(node);
      return cs.fill !== "none" && Number(cs.fillOpacity) * opacityOf(node) >= cover && node.isPointInFill(new DOMPoint(...inverse(node, p)));
    });
  };
  const onCanvasEdge = (p, slack) => canvases.some((r) =>
    p[0] >= r.left - slack && p[0] <= r.right + slack && p[1] >= r.top - slack && p[1] <= r.bottom + slack &&
    (Math.abs(p[0] - r.left) <= slack || Math.abs(p[0] - r.right) <= slack || Math.abs(p[1] - r.top) <= slack || Math.abs(p[1] - r.bottom) <= slack));

  // Distance from an end to the nearest thing it could land on. The line's
  // own segments near that end are skipped, or every end would land on
  // itself.
  const clearance = (line, sub, end, p, reach, textReach) => {
    let best = Infinity;
    const own = sub.flat;
    const skipNear = 2 * reach;
    const along = [0];
    for (let i = 1; i < own.length; i++) along.push(along[i - 1] + Math.hypot(own[i][0] - own[i - 1][0], own[i][1] - own[i - 1][1]));
    const total = along[along.length - 1];
    for (const entry of near(p, Math.max(reach, textReach) * 4)) {
      if (entry.kind === "round") {
        const local = inverse(entry.el, p);
        const inside = ((local[0] - entry.cx) / entry.rx) ** 2 + ((local[1] - entry.cy) / entry.ry) ** 2 <= 1;
        // A dot is a terminal: an end inside a filled round lands on it.
        if (entry.filled && inside) best = 0;
        else for (let index = 0; index < entry.points.length; index++) best = Math.min(best, segmentDistance(p, entry.points[index], entry.points[(index + 1) % entry.points.length]));
        continue;
      }
      if (entry.kind === "text") {
        // Leaders keep a little padding from their label; scale the
        // distance so textGap counts as tolerance.
        let d = inPolygon(p, entry.points) ? 0 : Infinity;
        for (let index = 0; index < entry.points.length; index++) d = Math.min(d, segmentDistance(p, entry.points[index], entry.points[(index + 1) % entry.points.length]));
        best = Math.min(best, d <= textReach ? 0 : d);
        continue;
      }
      if (entry.el === line.el && entry.sub === sub.index) {
        const from = along[entry.i] ?? total;
        const to = along[entry.i + 1] ?? total;
        const gapFrom = end === "start" ? from : total - to;
        if (gapFrom < skipNear) continue;
      }
      best = Math.min(best, segmentDistance(p, entry.a, entry.b));
    }
    return best;
  };

  const describe = (el) => {
    const owner = el.closest("[id], [data-name], [data-part], [aria-label]");
    const self = el.id ? `#${el.id}` : (el.getAttribute("class") ? `.${el.getAttribute("class").trim().split(/\s+/).join(".")}` : "");
    const ownerName = owner && owner !== el
      ? (owner.getAttribute("data-name") || owner.getAttribute("data-part") || owner.getAttribute("aria-label") || `#${owner.id}`)
      : "";
    return `${el.tagName.toLowerCase()}${self}${ownerName ? ` in ${ownerName}` : ""}`;
  };
  const userPoint = (el, p) => {
    const svg = el.ownerSVGElement || el.closest("svg");
    const m = svg && svg.getScreenCTM();
    if (!m) return p;
    const inv = m.inverse();
    return [inv.a * p[0] + inv.c * p[1] + inv.e, inv.b * p[0] + inv.d * p[1] + inv.f];
  };

  // Unit vector of the line's last step at this end, pointing outward.
  const direction = (flat, end) => {
    const [a, b] = end === "start" ? [flat[1], flat[0]] : [flat[flat.length - 2], flat[flat.length - 1]];
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
    return [(b[0] - a[0]) / len, (b[1] - a[1]) / len];
  };
  const slack = tolerance * scale;
  const rooted = rootSlack * scale;
  const textReach = textGap * scale;
  const candidates = [];
  const allEnds = [];
  let ends = 0;
  for (const line of lines) {
    for (const sub of line.subpaths) {
      if (sub.closed || sub.flat.length < 2) continue;
      const first = sub.flat[0];
      const last = sub.flat[sub.flat.length - 1];
      if (Math.hypot(first[0] - last[0], first[1] - last[1]) < 0.05 * scale) continue;
      const length = lengthOf(sub.flat);
      if (length < 0.2 * scale) continue;
      const result = {};
      for (const [end, p] of [["start", first], ["end", last]]) {
        if (line.free === "" || line.free === "both" || line.free === end) {
          result[end] = 0;
          continue;
        }
        ends++;
        allEnds.push({ line, p, dir: direction(sub.flat, end) });
        const reach = Math.max(slack, rooted) + markerReach(line.el, line.cs, end) * scale;
        let gap = hidden(line.el, p) || onCanvasEdge(p, slack) ? 0 : clearance(line, sub, end, p, reach, textReach);
        // A marker's reach widens what counts as landed at that end only.
        const markerSlack = markerReach(line.el, line.cs, end) * scale;
        if (markerSlack && gap <= slack + markerSlack) gap = 0;
        result[end] = gap;
      }
      const straight = sub.flat.length === 2 || sub.flat.every((q) => segmentDistance(q, first, last) < 0.15 * scale);
      const isMark = straight && length <= mark * scale;
      let bad = [];
      if (isMark) {
        const best = Math.min(result.start ?? Infinity, result.end ?? Infinity);
        if (!(best <= rooted)) bad = ["start", "end"].filter((end) => result[end] !== undefined && result[end] > 0);
      } else bad = ["start", "end"].filter((end) => result[end] !== undefined && result[end] > slack);
      for (const end of bad) {
        const p = end === "start" ? first : last;
        candidates.push({ line, end, p, isMark, gap: result[end], length, dir: direction(sub.flat, end) });
      }
    }
  }

  // Implied edges: `fence` or more ends sharing one vertical or horizontal
  // line read as a contour, the way gridlines stopping at an unstroked plot
  // boundary do. Only ends from other lines count toward the fence.
  const square = 0.9;  // |cos| of the angle to the edge's normal
  const fenced = (candidate) => {
    if (Number.isFinite(candidate.gap) && candidate.gap <= nearMiss * scale) return false;
    // axis 0: ends share x, a vertical edge, so lines must arrive along x.
    for (const axis of [0, 1]) {
      if (Math.abs(candidate.dir[axis]) < square) continue;
      let count = 1;
      for (const other of allEnds) {
        if (other.line === candidate.line) continue;
        if (Math.abs(other.dir[axis]) < square) continue;
        if (Math.abs(other.p[axis] - candidate.p[axis]) <= slack) count++;
      }
      if (count >= fence) return true;
    }
    return false;
  };

  const problems = [];
  let implied = 0;
  for (const c of candidates) {
    if (fence > 0 && fenced(c)) {
      implied++;
      continue;
    }
    const at = userPoint(c.line.el, c.p);
    problems.push({
      what: describe(c.line.el),
      d: (c.line.el.getAttribute("d") || "").slice(0, 48),
      end: c.end,
      mark: c.isMark,
      // null: nothing at all within reach, the worst case.
      gap: Number.isFinite(c.gap) ? Math.round((c.gap / scale) * 100) / 100 : null,
      at: [Math.round(at[0] * 10) / 10, Math.round(at[1] * 10) / 10],
      client: [Math.round(c.p[0] * 10) / 10, Math.round(c.p[1] * 10) / 10],
      opacity: Math.round(c.line.alpha * 100) / 100,
      length: Math.round((c.length / scale) * 10) / 10,
    });
  }
  style.remove();
  problems.sort((a, b) => (b.gap ?? Infinity) - (a.gap ?? Infinity));
  return { ends, lines: lines.length, implied, problems };
}
