import test from 'node:test';
import assert from 'node:assert/strict';
import { records, DOMAIN } from '../plugins/muriel/skills/compose/examples/linked-atlas/data.mjs';
import { createState, reduce, derive, aggregate, aggregateBinWidth, semanticLevel, zoomViewport, pixelToData, dataToPixel, normalizeExtent, inside, setOperation } from '../plugins/muriel/skills/compose/examples/linked-atlas/model.mjs';

const sorted = set => [...set].sort();
const fixture = [
  { id:'left', x:0, detections:0 },
  { id:'shared', x:2, detections:20 },
  { id:'near', x:1.99, detections:19.99 },
  { id:'final', x:32, detections:100 },
];
let seed = 0x24d6e;
const random = () => { seed = (1664525 * seed + 1013904223) >>> 0; return seed / 2 ** 32; };

 test('strict extents, inclusive boundaries, and invalid record policy', () => {
  for (const x of [[], [1], [1,2,3], [null,2], ['1',2], [NaN,2], [Infinity,2]]) assert.equal(normalizeExtent({ x }), null);
  for (const y of [[], null, [1], [1,2,3], [1,NaN]]) assert.equal(normalizeExtent({ x:[0,2], y }), null);
  assert.deepEqual(normalizeExtent({ x:[9,-2], y:[110,10] }), { x:[0,9], y:[10,100] });
  const extent = { x:[0,2], y:[0,20] };
  assert.deepEqual(fixture.filter(r => inside(r, extent)).map(r => r.id), ['left','shared','near']);
  assert.equal(inside(fixture[3], { x:[0,32], y:[0,100] }), true);
  for (const r of [{x:null,detections:0},{x:0,detections:null},{x:'0',detections:0},{x:NaN,detections:0},{x:0,detections:Infinity}]) assert.equal(inside(r, extent), false);
});

test('set algebra supports replace/add/subtract/intersect with empty distinct from inactive', () => {
  const base = new Set(['A','B']), incoming = new Set(['B','C']);
  assert.deepEqual(sorted(setOperation(base, incoming, 'replace')), ['B','C']);
  assert.deepEqual(sorted(setOperation(base, incoming, 'add')), ['A','B','C']);
  assert.deepEqual(sorted(setOperation(base, incoming, 'subtract')), ['A']);
  assert.deepEqual(sorted(setOperation(base, incoming, 'intersect')), ['B']);
  assert.deepEqual(sorted(base), ['A','B']);
  assert.deepEqual(sorted(setOperation(null, incoming, 'subtract')), []);
  const initial = createState();
  const empty = reduce(initial, { type:'select', extent:{ x:[0,32], y:[99,100] } });
  assert.equal(initial.selection, null);
  assert.equal(empty.selection.size, 0);
  assert.notEqual(empty.selection, null);
  assert.equal(reduce(empty, { type:'clear-selection' }).selection, null);
});

test('seeded varied algebra respects membership truth tables and partition identities', () => {
  for (let trial = 0; trial < 100; trial++) {
    const universe = Array.from({ length:50 }, (_, i) => `record-${i}`);
    const a = new Set(universe.filter(() => random() < .5));
    const b = new Set(universe.filter(() => random() < .5));
    const union = setOperation(a,b,'add'), intersection = setOperation(a,b,'intersect'), difference = setOperation(a,b,'subtract');
    for (const id of universe) {
      assert.equal(union.has(id), a.has(id) || b.has(id));
      assert.equal(intersection.has(id), a.has(id) && b.has(id));
      assert.equal(difference.has(id), a.has(id) && !b.has(id));
    }
    assert.equal(union.size + intersection.size, a.size + b.size);
    assert.equal(difference.size + intersection.size, a.size);
  }
});

test('aggregation preserves identity, selected fractions, fixed-grid boundaries, and final endpoint', () => {
  const bins = aggregate(fixture, new Set(['near','final']));
  assert.equal(bins.length, 3);
  const first = bins.find(b => b.id === 'bin:2:20:0:0');
  assert.deepEqual(first.ids, ['left','near']);
  assert.equal(first.selected,1);
  assert.equal(first.fraction,.5);
  assert.deepEqual(bins.find(b => b.ids.includes('final')).x,[30,32]);
  assert.deepEqual(bins.find(b => b.ids.includes('final')).y,[80,100]);
  assert.equal(bins.reduce((n,b) => n + b.count,0),4);
  for (const width of [0,-1,NaN,Infinity]) assert.throws(() => aggregate(fixture,null,width), RangeError);
  const invalid = [{id:'null',x:null,detections:0},{id:'missing',x:0},{id:'nan',x:NaN,detections:20},{id:'outside',x:33,detections:0}];
  assert.deepEqual(aggregate(invalid,null),[]);
});

test('seeded varied aggregation conserves IDs and selection across bin sizes', () => {
  for (let trial=0;trial<30;trial++) {
    const population = Array.from({length:101},(_,i) => ({id:`r${i}`,x:random()*32,detections:random()*100}));
    const selected = new Set(population.filter(() => random()<.4).map(r => r.id));
    for (const [bw,yw] of [[1,10],[2,20],[4,25],[7,13]]) {
      const bins=aggregate(population,selected,bw,yw);
      assert.deepEqual(bins.flatMap(b=>b.ids).sort(),population.map(r=>r.id).sort());
      assert.equal(bins.reduce((n,b)=>n+b.selected,0),selected.size);
      assert.equal(bins.reduce((n,b)=>n+b.count,0),population.length);
      assert.ok(bins.every(b=>b.fraction>=0&&b.fraction<=1));
    }
  }
});

test('semantic thresholds depend on projected occupancy and retain hysteresis', () => {
  assert.equal(semanticLevel('aggregate',100,800),'aggregate');
  assert.equal(semanticLevel('aggregate',70,800),'records');
  assert.equal(semanticLevel('records',100,800),'records');
  assert.equal(semanticLevel('records',130,800),'aggregate');
  assert.equal(semanticLevel('records',10,800),'labels');
  assert.equal(semanticLevel('labels',24,800),'labels');
  assert.equal(semanticLevel('labels',30,800),'records');
  assert.equal(semanticLevel('records',30,200),'aggregate');
});

test('zoom keeps anchor in place with round trips; boundaries clamp predictably', () => {
  for (let i=0;i<100;i++) {
    const viewport=[8,24], fraction=.1+random()*.8, factor=.5+random()*.4;
    const next=zoomViewport(viewport,factor,fraction);
    const anchor=viewport[0]+16*fraction;
    assert.ok(Math.abs(next[0]+(next[1]-next[0])*fraction-anchor)<1e-10);
    const roundtrip=zoomViewport(next,1/factor,fraction);
    assert.ok(Math.abs(roundtrip[0]-8)<1e-10);
    assert.ok(Math.abs(roundtrip[1]-24)<1e-10);
  }
  assert.deepEqual(zoomViewport([0,32],.5,0),[0,16]);
  assert.deepEqual(zoomViewport([0,32],.5,1),[16,32]);
  assert.deepEqual(zoomViewport([0,32],2,.5),[0,32]);
});

test('coordinate conversion is reversible with nonzero and reversed pixel ranges', () => {
  for (const pixelRange of [[83,741],[445,27]]) {
    for (const value of [0,3.25,16,32]) {
      assert.ok(Math.abs(pixelToData(dataToPixel(value,[0,32],pixelRange),pixelRange,[0,32])-value)<1e-10);
    }
  }
});

test('linked displays use one identity set while filters/zoom preserve hidden membership', () => {
  let state=reduce(createState(),{type:'select',extent:{x:[0,32],y:[0,100]}});
  state=reduce(state,{type:'filter',filter:'Reedbed'});
  state=reduce(state,{type:'viewport',viewport:[10,14]});
  const d=derive(state);
  assert.equal(d.selected.length,192);
  assert.equal(d.eligible.length,64);
  assert.equal(d.selectedVisible.length,8);
  assert.equal(d.selectedHidden,184);
  assert.equal(d.groups.reduce((n,g)=>n+g.selected,0),64);
  assert.deepEqual(state.selection,new Set(records.map(r=>r.id)));
  const recovered=derive(reduce(state,{type:'fit-selection'}));
  assert.equal(recovered.selectedVisible.length,192);
  assert.equal(recovered.selectedHidden,0);
  assert.deepEqual(DOMAIN.x,[0,32]);
});

test('brush drafts are transactional: cancel/lost capture restores selection, commit adds one undo', () => {
  let state=reduce(createState(),{type:'select',extent:{x:[0,4],y:[0,100]}});
  const previous=sorted(state.selection), historyLength=state.history.length;
  state=reduce(state,{type:'gesture-start',kind:'brush',source:'detail',extent:{x:[8,8],y:[0,0]}});
  state=reduce(state,{type:'gesture-move',extent:{x:[8,12],y:[0,100]}});
  assert.deepEqual(sorted(state.selection),previous);
  assert.notDeepEqual(sorted(derive(state).selection),previous);
  const cancelled=reduce(state,{type:'gesture-cancel'});
  assert.deepEqual(sorted(cancelled.selection),previous);
  assert.equal(cancelled.pending,null);
  assert.equal(cancelled.history.length,historyLength);
  const committed=reduce(state,{type:'gesture-commit'});
  assert.equal(committed.pending,null);
  assert.equal(committed.history.length,historyLength+1);
  assert.deepEqual(sorted(reduce(committed,{type:'undo'}).selection),previous);
});

test('pan drafts cancel/undo and semantic controls cancel pending state', () => {
  let state=reduce(createState(),{type:'viewport',viewport:[8,16]});
  state=reduce(state,{type:'gesture-start',kind:'navigate',source:'detail'});
  state=reduce(state,{type:'gesture-move',viewport:[12,20]});
  assert.deepEqual(derive(state).viewport,[12,20]);
  assert.deepEqual(state.viewport,[8,16]);
  assert.deepEqual(derive(reduce(state,{type:'gesture-cancel'})).viewport,[8,16]);
  assert.deepEqual(reduce(reduce(state,{type:'gesture-commit'}),{type:'undo'}).viewport,[8,16]);
  for (const action of [{type:'filter',filter:'Shore'},{type:'operation',operation:'add'},{type:'mode',mode:'brush'}]) assert.equal(reduce(state,action).pending,null);
});

test('preview leaves pin intact and clearing preview restores its inspector, even when hidden', () => {
  let state=reduce(createState(),{type:'pin',id:'F001'});
  state=reduce(state,{type:'preview',id:'F150'});
  assert.equal(state.pin,'F001');
  assert.equal(derive(state).inspector.id,'F150');
  state=reduce(state,{type:'preview',id:null});
  state=reduce(state,{type:'filter',filter:'Upland'});
  assert.equal(derive(state).inspector.id,'F001');
  assert.equal(derive(state).visible.some(r=>r.id==='F001'),false);
});


test('responsive aggregate widths keep a measured label budget and conserve selected membership', () => {
  const selection = new Set(['left','near','final']);
  for (const [pixels, expected] of [[1024,2],[512,4],[256,8],[128,16]]) {
    const width = aggregateBinWidth(32,pixels,60);
    assert.equal(width,expected);
    assert.ok(width/32*pixels >= 60);
    const bins = aggregate(fixture,selection,width);
    assert.deepEqual(bins.flatMap(b=>b.ids).sort(),fixture.map(r=>r.id).sort());
    assert.equal(bins.reduce((sum,b)=>sum+b.count,0),4);
    assert.equal(bins.reduce((sum,b)=>sum+b.selected,0),3);
    assert.ok(bins.every(b=>b.x[0]%width===0));
  }
  assert.equal(aggregateBinWidth(8,256,60),2);
  assert.throws(()=>aggregateBinWidth(32,0,60),RangeError);
});


test('bounded camera no-ops do not drift, consume undo, or leave pending navigation', () => {
  for (const [viewport, factor] of [[[0,32],2],[[12.123456789,12.873456789],.5]]) {
    let state = reduce(createState(),{type:'viewport',viewport});
    const baseline = [...state.viewport], historyLength = state.history.length;
    state = reduce(state,{type:'preview',id:'F001'});
    for (let i=0;i<500;i++) {
      state = reduce(state,{type:'zoom',factor,anchor:(i%97)/97});
      assert.deepEqual(state.viewport,baseline);
      assert.equal(state.history.length,historyLength);
    }
    for (const factor of [NaN,Infinity,0,-1]) assert.deepEqual(zoomViewport(baseline,factor,.37),baseline);
    assert.deepEqual(zoomViewport(baseline,1,NaN),baseline);
    assert.equal(state.preview,'F001');
  }
  let state=reduce(createState(),{type:'viewport',viewport:[0,8]});
  const historyLength=state.history.length;
  for (let i=0;i<50;i++) {
    state=reduce(state,{type:'viewport',viewport:[-4,4]});
    state=reduce(state,{type:'gesture-start',kind:'navigate',source:'detail'});
    state=reduce(state,{type:'gesture-move',viewport:[-4,4]});
    state=reduce(state,{type:'gesture-commit'});
    assert.deepEqual(state.viewport,[0,8]);
    assert.equal(state.history.length,historyLength);
    assert.equal(state.pending,null);
  }
  state=reduce(state,{type:'gesture-start',kind:'navigate',source:'detail'});
  state=reduce(state,{type:'viewport',viewport:[0,8]});
  assert.equal(state.pending,null);
  assert.equal(state.history.length,historyLength);
  state=reduce(state,{type:'viewport',viewport:[1e-12,8+1e-12]});
  assert.deepEqual(state.viewport,[0,8]);
  assert.equal(state.history.length,historyLength);
  state=reduce(state,{type:'filter',filter:'Shore'});
  state=reduce(state,{type:'show-all'});
  assert.equal(state.filter,'All');
  const meaningfulHistory=state.history.length;
  state=reduce(state,{type:'show-all'});
  assert.equal(state.history.length,meaningfulHistory);
});
