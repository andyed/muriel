import { DOMAIN, records } from './data.mjs';
import { createState, reduce, derive, aggregate, aggregateBinWidth, semanticLevel, pixelToData, dataToPixel, zoomViewport } from './model.mjs';

const $ = id => document.getElementById(id);
let state = createState();
let level = 'aggregate';
let drag = null;
let frame = null;
let latest = derive(state);
let aggregateWidth = 2;
const labelMeasure = document.createElement('canvas').getContext('2d');
labelMeasure.font = '500 16px Helvetica, Arial, sans-serif';
const plots = {};
const format = n => Number(n.toFixed(2)).toString();
const nameLevel = { aggregate: 'Aggregate cells', records: 'Individual records', labels: 'Records + labels' };
const extentFromPoints = (a, b, source) => ({ x: [a.x, b.x], y: source === 'overview' ? [...DOMAIN.y] : [a.y, b.y] });

function dispatch(action, deferred = false) {
  state = reduce(state, action);
  if (deferred) {
    if (!frame) frame = requestAnimationFrame(() => { frame = null; render(); });
  } else {
    if (frame) cancelAnimationFrame(frame);
    frame = null;
    render();
  }
  if (!['preview', 'gesture-move', 'gesture-start'].includes(action.type)) {
    const d = derive(state);
    $('announcement').textContent = `${d.selection === null ? 'Selection inactive' : `${d.selected.length} selected, ${d.selectedVisible.length} visible, ${d.selectedHidden} hidden`}. Detail window ${format(d.viewport[0])} to ${format(d.viewport[1])} elapsed days. ${state.filter} habitats.`;
  }
}
function dimensions(id) {
  const element = $(id);
  const width = Math.max(240, element.clientWidth);
  const height = element.clientHeight;
  const plot = { width, height, left:46, right:width - 16, top:18, bottom:height - 38 };
  element.setAttribute('viewBox', `0 0 ${width} ${height}`);
  return plots[id] = plot;
}
function ticks(plot, domain, vertical = false, count = 4) {
  let markup = '';
  for (let i = 0; i <= count; i++) {
    const value = domain[0] + (domain[1] - domain[0]) * i / count;
    if (vertical) {
      const y = dataToPixel(value, domain, [plot.bottom, plot.top]);
      markup += `<line class="grid-line" x1="${plot.left}" x2="${plot.right}" y1="${y}" y2="${y}"/><text x="${plot.left - 10}" y="${y + 5}" text-anchor="end">${format(value)}</text>`;
    } else {
      const x = dataToPixel(value, domain, [plot.left, plot.right]);
      markup += `<text x="${x}" y="${plot.bottom + 27}" text-anchor="${i === 0 ? 'start' : i === count ? 'end' : 'middle'}">${format(value)}</text>`;
    }
  }
  return markup;
}
function outline(extent, plot, domain, className = 'brush') {
  const x1 = Math.max(plot.left, Math.min(plot.right, dataToPixel(Math.min(...extent.x), domain, [plot.left, plot.right])));
  const x2 = Math.max(plot.left, Math.min(plot.right, dataToPixel(Math.max(...extent.x), domain, [plot.left, plot.right])));
  const y1 = dataToPixel(Math.max(...extent.y), DOMAIN.y, [plot.bottom, plot.top]);
  const y2 = dataToPixel(Math.min(...extent.y), DOMAIN.y, [plot.bottom, plot.top]);
  return `<rect class="${className}" x="${x1}" y="${y1}" width="${Math.max(1, x2 - x1)}" height="${Math.max(1, y2 - y1)}"/>`;
}
function renderOverview(d) {
  const plot = dimensions('overview');
  const x = value => dataToPixel(value, DOMAIN.x, [plot.left, plot.right]);
  const y = value => dataToPixel(value, [0, 6], [plot.bottom, plot.top]);
  const bins = Array.from({ length:32 }, (_, index) => ({ day:index, total:0, selected:0 }));
  for (const record of d.eligible) { const bin = bins[Math.floor(record.x)]; bin.total++; bin.selected += Number(d.selection?.has(record.id) ?? false); }
  let markup = ticks(plot, DOMAIN.x, false, plot.width < 500 ? 2 : 4) + ticks(plot, [0, 6], true, 2);
  for (const bin of bins) {
    const width = Math.max(1, x(bin.day + 1) - x(bin.day) - 2);
    markup += `<rect class="mark-base" x="${x(bin.day) + 1}" y="${y(bin.total)}" width="${width}" height="${plot.bottom - y(bin.total)}"/><rect class="mark" x="${x(bin.day) + 1}" y="${y(bin.selected)}" width="${width}" height="${plot.bottom - y(bin.selected)}"/>`;
  }
  markup += `<rect class="window" x="${x(d.viewport[0])}" y="${plot.top - 4}" width="${x(d.viewport[1]) - x(d.viewport[0])}" height="${plot.bottom - plot.top + 8}"/>`;
  if (state.pending?.kind === 'brush' && state.pending.source === 'overview' && state.pending.extent) {
    markup += outline({ ...state.pending.extent, y:DOMAIN.y }, plot, DOMAIN.x);
  }
  $('overview').innerHTML = markup;
  $('overview').dataset.domain = DOMAIN.x.join(',');
}
function renderDetail(d) {
  const plot = dimensions('detail');
  const width = plot.right - plot.left;
  level = semanticLevel(level, d.visible.length, width);
  const x = value => dataToPixel(value, d.viewport, [plot.left, plot.right]);
  const y = value => dataToPixel(value, DOMAIN.y, [plot.bottom, plot.top]);
  let markup = `<defs><clipPath id="detail-clip"><rect x="${plot.left}" y="${plot.top}" width="${width}" height="${plot.bottom - plot.top}"/></clipPath></defs>`;
  markup += ticks(plot, DOMAIN.y, true) + ticks(plot, d.viewport, false, plot.width < 500 ? 2 : 4);
  markup += '<g clip-path="url(#detail-clip)">';
  if (level === 'aggregate') {
    // Coarsen the globally anchored grid until its count labels fit at this scale.
    // Measure total/total so changing selected membership cannot trigger rebinning.
    aggregateWidth = 2;
    let bins;
    for (;;) {
      bins = aggregate(d.eligible, d.selection, aggregateWidth);
      const labelWidth = Math.max(0, ...bins.map(bin => labelMeasure.measureText(`${bin.count}/${bin.count}`).width));
      const candidate = aggregateBinWidth(d.viewport[1] - d.viewport[0], width, labelWidth + 20);
      if (candidate <= aggregateWidth) break;
      aggregateWidth = candidate;
    }
    for (const bin of bins) {
      if (bin.x[1] < d.viewport[0] || bin.x[0] > d.viewport[1]) continue;
      const bx = x(bin.x[0]) + 2, by = y(bin.y[1]) + 2;
      const bw = Math.max(1, x(bin.x[1]) - bx - 2), bh = Math.max(1, y(bin.y[0]) - by - 2);
      markup += `<g data-bin="${bin.id}" data-members="${bin.ids.join(',')}" data-selected="${bin.selected}"><rect class="mark-base" x="${bx}" y="${by}" width="${bw}" height="${bh}"/><rect class="mark" x="${bx}" y="${by + bh * (1 - bin.fraction)}" width="${bw}" height="${bh * bin.fraction}"/>`;
      const label = `${bin.selected}/${bin.count}`;
      const labelWidth = labelMeasure.measureText(label).width + 12;
      markup += `<rect x="${bx + bw / 2 - labelWidth / 2}" y="${by + bh / 2 - 12}" width="${labelWidth}" height="24" rx="2" fill="#0a0a0f"/><text class="aggregate-label" x="${bx + bw / 2}" y="${by + bh / 2 + 5}" text-anchor="middle" style="fill:#e6e4d2">${label}</text>`;
      markup += '</g>';
    }
  } else {
    const occupied = [];
    for (const record of d.visible) {
      const selected = d.selection?.has(record.id);
      markup += `<circle data-record="${record.id}" class="point ${selected ? 'selected' : d.selection !== null ? 'faded' : ''}" cx="${x(record.x)}" cy="${y(record.detections)}" r="${selected ? 5.5 : 4.5}"/>`;
      if (level === 'labels') {
        const box = { x:x(record.x) + 9, y:y(record.detections) - 8, w:48, h:20 };
        if (box.x + box.w > plot.right) box.x = x(record.x) - box.w - 9;
        const overlaps = occupied.some(other => box.x < other.x + other.w && box.x + box.w > other.x && box.y < other.y + other.h && box.y + box.h > other.y);
        if (!overlaps && box.y >= plot.top && box.y + box.h <= plot.bottom) {
          occupied.push(box);
          markup += `<text class="record-label" x="${box.x}" y="${box.y + 15}">${record.id}</text>`;
        }
      }
    }
  }
  for (const id of new Set([state.pin, state.preview])) {
    const record = d.visible.find(r => r.id === id);
    if (record) markup += `<circle class="pinned" cx="${x(record.x)}" cy="${y(record.detections)}" r="11"/>`;
  }
  if (state.pending?.kind === 'brush' && state.pending.extent) markup += outline(state.pending.extent, plot, d.viewport);
  markup += '</g>';
  if (!d.visible.length) markup += `<text x="${plot.left + 12}" y="${plot.top + 30}" style="fill:#e6e4d2">No observations in this window.</text>`;
  $('detail').innerHTML = markup;
  $('detail').dataset.level = level;
  $('detail').dataset.binWidth = level === 'aggregate' ? aggregateWidth : ''; 
  $('detail').dataset.domain = d.viewport.join(',');
  $('semantic-level').textContent = nameLevel[level];
  $('representation-help').textContent = level === 'aggregate'
    ? `Cells use a ${aggregateWidth}-day × 20-detection grid sized to keep counts readable. Cyan height and labels show selected / total members; clipped cells keep their full membership.`
    : level === 'records' ? 'Each dot is one observation. Cyan filled dots are selected; outlined dots remain available. Zoom further to reveal stable record IDs.'
      : 'Labels reveal stable record IDs where space allows. Overlapping labels are omitted; every visible record remains in the table below.';
}
function renderGroups(d) {
  $('groups').innerHTML = d.groups.map(group => `<div class="group"><div class="group-line"><strong>${group.habitat}</strong><span>${group.selected} / ${group.total}</span></div><div class="group-meter" aria-hidden="true"><span style="width:${group.total ? group.selected / group.total * 100 : 0}%"></span></div><p>${group.selectedMean === null ? 'No selected mean' : `Selected mean ${group.selectedMean.toFixed(1)}`}<br>${group.mean === null ? 'Filtered out' : `Eligible mean ${group.mean.toFixed(1)}`}</p></div>`).join('');
  const eligibleSelected = d.eligible.filter(r => d.selection?.has(r.id)).length;
  $('cohort-summary').textContent = `${eligibleSelected} selected of ${d.eligible.length} eligible observations (${d.eligible.length ? (eligibleSelected / d.eligible.length * 100).toFixed(1) : '0'}%). Means are detections per 10-minute survey; they include the full study, independent of zoom.`;
}
let tableKey = '';
function renderTable(d) {
  // Do not replace focused rows during hover or resize; table identity is independent of representation.
  const key = `${d.visible.map(r => r.id).join(',')}|${[...(d.selection ?? [])].join(',')}|${state.pin}`;
  $('table-count').textContent = `${d.visible.length} visible rows`;
  if (key === tableKey) return;
  tableKey = key;
  const focusedId = document.activeElement?.dataset.pin;
  const scrollTop = $('records').parentElement.parentElement.scrollTop;
  $('records').innerHTML = d.visible.length ? d.visible.map(record => `<tr class="${d.selection?.has(record.id) ? 'selected' : ''}"><td>${record.id}</td><td>${record.day}</td><td>${record.habitat}</td><td>${record.detections}</td><td>${d.selection?.has(record.id) ? 'Yes' : '—'}</td><td><button data-pin="${record.id}" aria-label="Pin ${record.id}" aria-pressed="${state.pin === record.id}">${state.pin === record.id ? 'Pinned' : 'Pin'}</button></td></tr>`).join('') : '<tr><td colspan="6">No visible records. Use Full extent or change the habitat filter.</td></tr>';
  if (focusedId) {
    const retained = $('records').querySelector(`[data-pin="${focusedId}"]`);
    (retained ?? document.querySelector('.table-scroll')).focus({ preventScroll:true });
  }
  $('records').parentElement.parentElement.scrollTop = scrollTop;
}
function renderInspector(d) {
  $('unpin').disabled = state.pin === null;
  const record = d.inspector;
  if (!record) {
    $('inspector-body').innerHTML = '<p>Pin a table record to keep its details here. Hover a plotted record to preview it; leaving restores the pin.</p>';
    return;
  }
  const visible = d.visible.some(r => r.id === record.id);
  $('inspector-body').innerHTML = `<p class="mode-label">${state.preview ? 'Preview' : 'Pinned'}${state.preview && state.pin ? ` · returns to ${state.pin}` : ''}</p><h3>${record.id}</h3><p>${record.habitat} · station ${record.station}</p><dl><dt>Study day / elapsed time</dt><dd>${record.day} / ${format(record.x)} days</dd><dt>Detections per 10 minutes</dt><dd>${record.detections}</dd><dt>Synthetic quality score</dt><dd>${record.confidence} / 100</dd><dt>Selection / visibility</dt><dd>${d.selection?.has(record.id) ? 'Selected' : 'Unselected'} · ${visible ? 'visible' : 'outside current view'}</dd></dl><p class="muted">Generated record, seed formula v1. Quality scores illustrate an additional record attribute; they are not measurement uncertainty.</p>`;
}
function render() {
  latest = derive(state);
  const d = latest;
  $('mobile-selection-count').textContent = d.selection === null ? 'Selection inactive.' : `${d.selected.length} selected · ${d.selectedVisible.length} visible · ${d.selectedHidden} hidden.`;
  $('selection-count').textContent = d.selection === null ? 'Inactive' : `${d.selected.length} selected`;
  $('selection-context').textContent = d.selection === null ? 'No membership constraint.' : `${d.selectedVisible.length} visible · ${d.selectedHidden} hidden${state.pending?.kind === 'brush' ? ' · preview' : ''}`;
  $('window-label').textContent = `${format(d.viewport[0])}–${format(d.viewport[1])} days`;
  $('visible-count').textContent = `${d.visible.length} of ${d.eligible.length} eligible observations`;
  $('fit-selection').disabled = !d.selected.length;
  $('clear-selection').disabled = state.selection === null && !state.pending;
  $('undo').disabled = !state.history.length && !state.pending;
  $('zoom-in').disabled = d.viewport[1] - d.viewport[0] <= .75001;
  $('zoom-out').disabled = d.viewport[1] - d.viewport[0] >= 31.99999;
  $('pan-left').disabled = d.viewport[0] <= 0;
  $('pan-right').disabled = d.viewport[1] >= 32;
  $('operation').value = state.operation;
  $('filter').value = state.filter;
  document.querySelector(`input[name=mode][value=${state.mode}]`).checked = true;
  $('detail-help').textContent = state.mode === 'brush'
    ? 'Drag to select a rectangle. Exact selection below supports keyboard input. Escape cancels an unfinished gesture.'
    : 'Drag to pan. Use the zoom buttons, or the mouse wheel over the detail plot to zoom at the pointer. Escape cancels a drag.';
  $('detail').style.cursor = $('overview').style.cursor = state.mode === 'brush' ? 'crosshair' : drag ? 'grabbing' : 'grab';
  renderOverview(d); renderDetail(d); renderGroups(d); renderTable(d); renderInspector(d);
}

for (const input of document.querySelectorAll('input[name=mode]')) input.addEventListener('change', () => dispatch({ type:'mode', mode:input.value }));
$('operation').addEventListener('change', event => dispatch({ type:'operation', operation:event.target.value }));
$('filter').addEventListener('change', event => dispatch({ type:'filter', filter:event.target.value }));
for (const [id, type] of [['clear-selection','clear-selection'], ['fit-selection','fit-selection'], ['undo','undo'], ['reset','reset']]) $(id).addEventListener('click', () => dispatch({ type }));
$('full-extent').addEventListener('click', () => dispatch({ type:'viewport', viewport:DOMAIN.x }));
$('zoom-in').addEventListener('click', () => dispatch({ type:'zoom', factor:.5 }));
$('zoom-out').addEventListener('click', () => dispatch({ type:'zoom', factor:2 }));
for (const [id, direction] of [['pan-left', -1], ['pan-right', 1]]) $(id).addEventListener('click', () => {
  const shift = (state.viewport[1] - state.viewport[0]) * .5 * direction;
  dispatch({ type:'viewport', viewport:state.viewport.map(x => x + shift) });
});
$('unpin').addEventListener('click', () => dispatch({ type:'pin', id:null }));
$('records').addEventListener('click', event => { const button = event.target.closest('[data-pin]'); if (button) dispatch({ type:'pin', id:button.dataset.pin }); });
$('exact-form').addEventListener('submit', event => {
  event.preventDefault();
  dispatch({ type:'select', extent:{ x:[Number($('range-start').value), Number($('range-end').value)], y:[Number($('value-start').value), Number($('value-end').value)] } });
});

function point(event, source, viewport) {
  const element = $(source), plot = plots[source];
  // Invert the full SVG screen matrix: CSS scaling, viewBox origin and aspect-ratio letterboxing.
  const local = new DOMPoint(event.clientX, event.clientY).matrixTransform(element.getScreenCTM().inverse());
  const px = local.x;
  const py = local.y;
  return { px, py,
    x:pixelToData(Math.max(plot.left, Math.min(plot.right, px)), [plot.left, plot.right], source === 'overview' ? DOMAIN.x : viewport),
    y:pixelToData(Math.max(plot.top, Math.min(plot.bottom, py)), [plot.bottom, plot.top], DOMAIN.y),
    inPlot:px >= plot.left && px <= plot.right && py >= plot.top && py <= plot.bottom };
}
function cancelGesture() {
  if (!drag) return;
  const oldDrag = drag;
  drag = null;
  dispatch({ type:'gesture-cancel' });
  if ($(oldDrag.source).hasPointerCapture(oldDrag.id)) $(oldDrag.source).releasePointerCapture(oldDrag.id);
}
for (const source of ['overview', 'detail']) {
  const element = $(source);
  element.addEventListener('pointerdown', event => {
    if (!event.isPrimary || event.button !== 0 || drag) return;
    const start = point(event, source, latest.viewport);
    if (!start.inPlot) return;
    event.preventDefault();
    drag = { id:event.pointerId, source, start, clientStart:[event.clientX, event.clientY], viewport:[...state.viewport], mode:state.mode };
    element.setPointerCapture(event.pointerId);
    dispatch({ type:'gesture-start', kind:state.mode, source, extent:extentFromPoints(start, start, source) });
  });
  element.addEventListener('pointermove', event => {
    if (drag && drag.source === source && event.pointerId === drag.id) {
      const current = point(event, source, drag.viewport);
      if (drag.mode === 'brush') dispatch({ type:'gesture-move', extent:extentFromPoints(drag.start, current, source) }, true);
      else {
        const delta = current.x - drag.start.x;
        const shift = source === 'overview' ? delta : -delta;
        dispatch({ type:'gesture-move', viewport:drag.viewport.map(x => x + shift) }, true);
      }
      return;
    }
    if (drag || source !== 'detail' || level === 'aggregate') return;
    const current = point(event, source, latest.viewport), plot = plots.detail;
    let nearest = null, distance = 13;
    if (current.inPlot) for (const record of latest.visible) {
      const dx = dataToPixel(record.x, latest.viewport, [plot.left, plot.right]) - current.px;
      const dy = dataToPixel(record.detections, DOMAIN.y, [plot.bottom, plot.top]) - current.py;
      const candidate = Math.hypot(dx, dy);
      if (candidate < distance) { distance = candidate; nearest = record.id; }
    }
    if (state.preview !== nearest) dispatch({ type:'preview', id:nearest }, true);
  });
  element.addEventListener('pointerup', event => {
    if (!drag || event.pointerId !== drag.id) return;
    // A tap is not an empty brush. Empty selection requires a deliberate rectangle or exact form.
    if (Math.hypot(event.clientX - drag.clientStart[0], event.clientY - drag.clientStart[1]) < 4) { cancelGesture(); return; }
    // Include the final pointer coordinate even when no move event followed it.
    const current = point(event, source, drag.viewport);
    if (drag.mode === 'brush') state = reduce(state, { type:'gesture-move', extent:extentFromPoints(drag.start, current, source) });
    else {
      const delta = (current.x - drag.start.x) * (source === 'overview' ? 1 : -1);
      state = reduce(state, { type:'gesture-move', viewport:drag.viewport.map(x => x + delta) });
    }
    drag = null;
    dispatch({ type:'gesture-commit' });
    if (element.hasPointerCapture(event.pointerId)) element.releasePointerCapture(event.pointerId);
  });
  element.addEventListener('pointercancel', cancelGesture);
  element.addEventListener('lostpointercapture', () => { if (drag?.source === source) cancelGesture(); });
  element.addEventListener('pointerleave', () => { if (!drag && state.preview) dispatch({ type:'preview', id:null }, true); });
}
$('detail').addEventListener('wheel', event => {
  if (state.mode !== 'navigate' || drag) return;
  const current = point(event, 'detail', latest.viewport), plot = plots.detail;
  if (!current.inPlot) return;
  event.preventDefault();
  const factor = event.deltaY > 0 ? 1.18 : 1 / 1.18;
  const viewport = zoomViewport(state.viewport, factor, (current.px - plot.left) / (plot.right - plot.left));
  dispatch({ type:'viewport', viewport }, true);
}, { passive:false });
document.addEventListener('pointerdown', event => {
  if (drag && event.pointerId !== drag.id) cancelGesture();
}, { capture:true });
document.addEventListener('keydown', event => { if (event.key === 'Escape') cancelGesture(); });
window.addEventListener('blur', cancelGesture);
new ResizeObserver(() => { if (drag) cancelGesture(); render(); }).observe($('detail'));

// Read-only snapshots support external tests without a second writable control path.
window.linkedAtlas = Object.freeze({ snapshot:() => {
  const d = derive(state);
  return structuredClone({
    state:{ viewport:state.viewport, selection:state.selection === null ? null : [...state.selection], filter:state.filter, pin:state.pin, preview:state.preview, pending:state.pending, mode:state.mode, operation:state.operation, historyLength:state.history.length },
    derived:{ viewport:d.viewport, eligibleIds:d.eligible.map(r => r.id), visibleIds:d.visible.map(r => r.id), selectedIds:d.selected.map(r => r.id), selectedVisibleIds:d.selectedVisible.map(r => r.id), selectedHidden:d.selectedHidden, inspectorId:d.inspector?.id ?? null },
    level, aggregateWidth, plots,
  });
} });
render();
