// Focus lifecycle tests with deterministic frames; rendered framing is checked in Chrome.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const moduleURL = source => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const values = moduleURL(`export class Vector3 {
  constructor(x=0,y=0,z=0) {Object.assign(this,{x,y,z});}
  clone(){return new Vector3(this.x,this.y,this.z);}
  copy(v){Object.assign(this,v);return this;}
  lerpVectors(a,b,t){for(const k of ['x','y','z'])this[k]=a[k]+(b[k]-a[k])*t;return this;}
  slerpQuaternions(a,b,t){return this.lerpVectors(a,b,t);}
}`);
const renderer = moduleURL('export class CSS3DObject {} export class CSS3DRenderer {}');
const source = (await readFile(new URL('../render_assets/_lib/spatial.js',import.meta.url),'utf8'))
  .replace("import * as THREE from 'three';",`import * as THREE from '${values}';`).replace("from 'three/addons/renderers/CSS3DRenderer.js'",`from '${renderer}'`);
const {FocusController,THREE} = await import(moduleURL(source));
const V=THREE.Vector3;
let frames, sequence, reduced;
function reset(){frames=new Map();sequence=0;reduced=false;}
globalThis.requestAnimationFrame = cb => {const id=++sequence;frames.set(id,cb);return id;};
globalThis.cancelAnimationFrame = id => frames.delete(id);
globalThis.matchMedia = () => ({matches:reduced});
function finish(){const pending=[...frames.values()];frames.clear();for(const cb of pending)cb(performance.now()+1000);}
function card(x,featured=false){
 const classes=new Set(featured?['featured']:[]);
 return {position:new V(x,20,-100),scale:new V(1,1,1),quaternion:new V(),userData:{featured},
 element:{classList:{add:c=>classes.add(c),remove:c=>classes.delete(c),contains:c=>classes.has(c)},addEventListener(){}}};
}

test('rapid A → B → A → close cancels stale flights and returns both cards home',()=>{
 reset();const a=card(-100,true),b=card(100);const f=new FocusController();f.bind([a,b]);
 const homeA=a.position.clone(),homeB=b.position.clone();
 f.toggle(a);f.toggle(b);f.toggle(a);f.unfocus(a);
 assert.equal(frames.size,2,'only the final trajectory per card remains');
 finish();assert.deepEqual(a.position,homeA);assert.deepEqual(b.position,homeB);
 assert.equal(f.focused,null);assert.equal(frames.size,0);
 assert.ok(a.element.classList.contains('featured'),'authored feature survives dismissal');
 assert.ok(!b.element.classList.contains('featured'));
});

test('switch notification preserves the prior selection and repeated read clicks keep focus',()=>{
 reset();const changes=[];const a=card(0),b=card(100);
 const f=new FocusController({toggleOnRepeat:false,onChange:(...args)=>changes.push(args)});f.bind([a,b]);
 f.toggle(a);f.toggle(a);f.toggle(b);
 assert.deepEqual(changes,[[a,null],[b,a]],'switching never emits a false closed state');
 f.unfocus(b);assert.deepEqual(changes.at(-1),[null,b]);finish();
});

test('reduced motion applies and restores framing atomically; resize replaces its target',()=>{
 reset();reduced=true;const a=card(30);const f=new FocusController();f.bind([a]);
 const home={p:a.position.clone(),s:a.scale.clone(),q:a.quaternion.clone()};
 f.focusScale=new V(.3,.3,.3);f.focusQuaternion=new V(.02,0,0);f.toggle(a);
 assert.deepEqual(a.scale,f.focusScale);assert.deepEqual(a.quaternion,f.focusQuaternion);assert.equal(frames.size,0);
 f.focusPos=new V(0,150,500);f.reframe();assert.deepEqual(a.position,f.focusPos);
 f.unfocus(a);assert.deepEqual(a.position,home.p);assert.deepEqual(a.scale,home.s);assert.deepEqual(a.quaternion,home.q);
 assert.equal(frames.size,0);
});
