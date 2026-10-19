import { DOMAIN, HABITATS, records } from './data.mjs';

const ids = new Set(records.map(record => record.id));
const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi, n));
const finite = n => Number.isFinite(n);
const sameViewport = (a, b) => a.every((value, i) => Math.abs(value - b[i]) < 1e-10);
const pair = value => Array.isArray(value) && value.length === 2 && value.every(finite);
const validRecord = record => record && finite(record.x) && finite(record.detections) &&
  record.x >= DOMAIN.x[0] && record.x <= DOMAIN.x[1] &&
  record.detections >= DOMAIN.y[0] && record.detections <= DOMAIN.y[1];
const copySet = set => set === null ? null : new Set(set);
const snapshot = state => ({
  viewport: [...state.viewport], selection: copySet(state.selection),
  filter: state.filter, pin: state.pin, lastBrush: state.lastBrush,
});

export function createState() {
  return { viewport: [...DOMAIN.x], selection: null, filter: 'All', pin: null,
    preview: null, pending: null, lastBrush: null, mode: 'brush', operation: 'replace', history: [] };
}

/** Continuous day coordinates; the selection predicate includes both boundaries. */
export function normalizeExtent(extent) {
  if (!extent || !pair(extent.x) ||
      (extent.y !== undefined && !pair(extent.y))) return null;
  return { x: [...extent.x].sort((a, b) => a - b).map(x => clamp(x, ...DOMAIN.x)),
    y: extent.y ? [...extent.y].sort((a, b) => a - b).map(y => clamp(y, ...DOMAIN.y)) : [...DOMAIN.y] };
}
export function inside(record, extent) {
  return Boolean(validRecord(record)) && record.x >= extent.x[0] && record.x <= extent.x[1] &&
    record.detections >= extent.y[0] && record.detections <= extent.y[1];
}
export function brushIds(extent, filter = 'All') {
  const normalized = normalizeExtent(extent);
  return new Set(normalized ? records.filter(r => (filter === 'All' || r.habitat === filter) && inside(r, normalized)).map(r => r.id) : []);
}
export function setOperation(current, incoming, operation) {
  const base = current ?? new Set();
  if (operation === 'replace') return new Set(incoming);
  if (operation === 'add') return new Set([...base, ...incoming]);
  if (operation === 'subtract') return new Set([...base].filter(id => !incoming.has(id)));
  if (operation === 'intersect') return new Set([...base].filter(id => incoming.has(id)));
  throw new Error(`Unknown selection operation: ${operation}`);
}
export function normalizeViewport(viewport) {
  if (!pair(viewport)) return [...DOMAIN.x];
  const width = clamp(Math.abs(viewport[1] - viewport[0]), .75, 32);
  const start = clamp(Math.min(...viewport), 0, 32 - width);
  return [start, start + width];
}
/** Preserve the data coordinate beneath anchorFraction unless a domain edge clamps it. */
export function zoomViewport(viewport, factor, anchorFraction = .5) {
  if (!finite(factor) || factor <= 0 || !finite(anchorFraction)) return [...viewport];
  const fraction = clamp(anchorFraction, 0, 1);
  const oldWidth = viewport[1] - viewport[0];
  const newWidth = clamp(oldWidth * factor, .75, 32);
  // At a limit, avoid recomputing an unchanged camera through floating-point anchor math.
  if (Math.abs(newWidth - oldWidth) < 1e-10) return [...viewport];
  const anchor = viewport[0] + oldWidth * fraction;
  return normalizeViewport([anchor - newWidth * fraction, anchor + newWidth * (1 - fraction)]);
}
export function pixelToData(pixel, pixelRange, dataRange) {
  if (![pixel, ...pixelRange, ...dataRange].every(finite) || pixelRange[1] === pixelRange[0]) return dataRange[0];
  return dataRange[0] + (pixel - pixelRange[0]) / (pixelRange[1] - pixelRange[0]) * (dataRange[1] - dataRange[0]);
}
export function dataToPixel(value, dataRange, pixelRange) {
  return pixelToData(value, dataRange, pixelRange);
}

function commit(state, changes) {
  return { ...state, ...changes, preview: null, pending: null,
    history: [...state.history.slice(-29), snapshot(state)] };
}

function commitCamera(state, viewport, filter = state.filter) {
  if (sameViewport(state.viewport, viewport) && filter === state.filter) {
    // Ending a draft is still necessary, but a bounded camera no-op is not undo history.
    return state.pending ? { ...state, pending:null } : state;
  }
  return commit(state, { viewport, filter });
}

/** Views dispatch intent here; no renderer writes another renderer's state. */
export function reduce(state, action) {
  switch (action.type) {
    case 'mode': return { ...state, mode: action.mode === 'navigate' ? 'navigate' : 'brush', pending: null };
    case 'operation': return ['replace', 'add', 'subtract', 'intersect'].includes(action.operation)
      ? { ...state, operation: action.operation, pending: null } : state;
    case 'preview': return { ...state, preview: ids.has(action.id) ? action.id : null };
    case 'pin': return commit(state, { pin: ids.has(action.id) ? action.id : null });
    case 'filter': return action.filter === 'All' || HABITATS.includes(action.filter)
      ? commit(state, { filter: action.filter }) : state;
    case 'viewport': return commitCamera(state, normalizeViewport(action.viewport));
    case 'zoom': return commitCamera(state, zoomViewport(state.viewport, action.factor, action.anchor));
    case 'select': {
      const extent = normalizeExtent(action.extent);
      if (!extent) return state;
      return commit(state, { selection: setOperation(state.selection, brushIds(extent, state.filter), action.operation ?? state.operation), lastBrush: extent });
    }
    case 'clear-selection': return commit(state, { selection: null, lastBrush: null });
    case 'show-all': return commitCamera(state, [...DOMAIN.x], 'All');
    case 'fit-selection': {
      const selected = records.filter(r => state.selection?.has(r.id));
      if (!selected.length) return state;
      const start = Math.min(...selected.map(r => r.x));
      const end = Math.max(...selected.map(r => r.x));
      return commitCamera(state, normalizeViewport([start - .5, end + .5]), 'All');
    }
    case 'gesture-start': return { ...state, preview: null, pending: {
      kind: action.kind, source: action.source,
      extent: normalizeExtent(action.extent), viewport: [...state.viewport],
    } };
    case 'gesture-move': return state.pending ? { ...state, pending: { ...state.pending,
      ...(action.extent ? { extent: normalizeExtent(action.extent) } : {}),
      ...(action.viewport ? { viewport: normalizeViewport(action.viewport) } : {}),
    } } : state;
    case 'gesture-cancel': return { ...state, pending: null };
    case 'gesture-commit': {
      if (!state.pending) return state;
      const pending = state.pending;
      if (pending.kind === 'navigate') return commitCamera(state, pending.viewport);
      if (!pending.extent) return { ...state, pending: null };
      return commit(state, { selection: setOperation(state.selection, brushIds(pending.extent, state.filter), state.operation), lastBrush: pending.extent });
    }
    case 'undo': {
      if (state.pending) return { ...state, pending: null };
      const previous = state.history.at(-1);
      return previous ? { ...state, ...previous, preview: null, pending: null, history: state.history.slice(0, -1) } : state;
    }
    case 'reset': return commit(state, { ...snapshot(createState()), mode: 'brush', operation: 'replace' });
    default: return state;
  }
}

export function derive(state) {
  const viewport = state.pending?.kind === 'navigate' ? state.pending.viewport : state.viewport;
  const selection = state.pending?.kind === 'brush' && state.pending.extent
    ? setOperation(state.selection, brushIds(state.pending.extent, state.filter), state.operation)
    : state.selection;
  const eligible = records.filter(r => state.filter === 'All' || r.habitat === state.filter);
  const visible = eligible.filter(r => r.x >= viewport[0] && r.x <= viewport[1]);
  const selected = records.filter(r => selection?.has(r.id));
  const selectedVisible = visible.filter(r => selection?.has(r.id));
  return { viewport, selection, eligible, visible, selected, selectedVisible,
    selectedHidden: selected.length - selectedVisible.length,
    inspector: records.find(r => r.id === (state.preview ?? state.pin)) ?? null,
    groups: HABITATS.map(habitat => {
      const population = eligible.filter(r => r.habitat === habitat);
      const groupSelected = population.filter(r => selection?.has(r.id));
      return { habitat, total: population.length, selected: groupSelected.length,
        mean: population.length ? population.reduce((sum, r) => sum + r.detections, 0) / population.length : null,
        selectedMean: groupSelected.length ? groupSelected.reduce((sum, r) => sum + r.detections, 0) / groupSelected.length : null };
    }),
  };
}

/** Stable global grid. Membership, identity and selected denominator survive camera changes. */
export function aggregate(population, selection, binWidth = 2, yBinWidth = 20) {
  if (!finite(binWidth) || binWidth <= 0 || !finite(yBinWidth) || yBinWidth <= 0) {
    throw new RangeError('Bin widths must be finite and greater than zero.');
  }
  const bins = new Map();
  for (const record of population) {
    // Missing, nonnumeric and out-of-domain observations cannot become ghost marks.
    if (!validRecord(record)) continue;
    const ix = Math.min(Math.floor(record.x / binWidth), Math.ceil(32 / binWidth) - 1);
    const iy = Math.min(Math.floor(record.detections / yBinWidth), Math.ceil(100 / yBinWidth) - 1);
    const id = `bin:${binWidth}:${yBinWidth}:${ix}:${iy}`;
    if (!bins.has(id)) bins.set(id, { id, x: [ix * binWidth, Math.min(32, (ix + 1) * binWidth)], y: [iy * yBinWidth, Math.min(100, (iy + 1) * yBinWidth)], ids: [], selected: 0 });
    const bin = bins.get(id);
    bin.ids.push(record.id);
    bin.selected += Number(selection?.has(record.id) ?? false);
  }
  return [...bins.values()].map(bin => ({ ...bin, count: bin.ids.length, fraction: bin.selected / bin.ids.length }));
}


/** Choose a globally anchored time-bin size from measured pixel requirements. */
export function aggregateBinWidth(viewportWidth, plotWidth, requiredCellWidth) {
  if (![viewportWidth, plotWidth, requiredCellWidth].every(finite) ||
      viewportWidth <= 0 || plotWidth <= 0 || requiredCellWidth <= 0) {
    throw new RangeError('Responsive aggregation needs positive finite measurements.');
  }
  return [2, 4, 8, 16, 32].find(width => width / viewportWidth * plotWidth >= requiredCellWidth) ?? 32;
}

/** Projected occupancy, with distinct enter/leave thresholds to prevent flicker. */
export function semanticLevel(previous, visibleCount, width) {
  const spacing = width / Math.max(1, visibleCount);
  if (previous === 'aggregate') return spacing >= 10 ? (spacing >= 42 ? 'labels' : 'records') : 'aggregate';
  if (previous === 'labels') return spacing < 30 ? (spacing < 7 ? 'aggregate' : 'records') : 'labels';
  return spacing < 7 ? 'aggregate' : spacing >= 42 ? 'labels' : 'records';
}
