// Harvest a muriel control map from a built Spinodal: rest, revealed, mid-beat,
// then each revealed control activated in turn (one level deep), plus the
// armed state of each control that opens something. Records every visible
// interactive element in #ui with its box. Serves the build itself (Node, not
// python http.server). Full Chrome: run on cylon.
//
//   node harvest-control-map.mjs <dist-dir> <out-dir> [WxH,touch|mouse ...]
import { chromium } from '/Users/andyed/Documents/dev/worktrees/spinodal-staging-7d95b56/node_modules/playwright/index.mjs';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const [dist, out, ...vps] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const VIEWPORTS = (vps.length ? vps : ['390x844,touch', '1470x956,mouse']).map(s => {
    const [wh, input] = s.split(','); const [w, h] = wh.split('x').map(Number); return { w, h, touch: input === 'touch' };
});

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png', '.json': 'application/json', '.wasm': 'application/wasm', '.ico': 'image/x-icon', '.mp4': 'video/mp4', '.webm': 'video/webm' };
const server = http.createServer((req, res) => {
    let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    if (p.endsWith('/')) p += 'index.html';
    const f = path.join(dist, p);
    if (!f.startsWith(dist) || !fs.existsSync(f)) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'content-type': MIME[path.extname(f)] ?? 'application/octet-stream' });
    fs.createReadStream(f).pipe(res);
}).listen(0, '127.0.0.1');
await new Promise(r => server.once('listening', r));
const base = `http://127.0.0.1:${server.address().port}/?warm=1&tour=0`;

const browser = await chromium.launch({ channel: 'chrome', headless: true,
    args: ['--enable-unsafe-webgpu', '--enable-features=Vulkan,WebGPU', '--use-angle=metal'] });

// Every visible, operable control inside #ui, keyed by a stable id.
const HARVEST = () => {
    const sel = 'button, [role=button], [role=switch], [role=radio], [role=slider], [role=tab], input:not([type=hidden]), select, a[href]';
    const opacity = el => { let o = 1; for (let e = el; e && e !== document; e = e.parentElement) o *= +getComputedStyle(e).opacity; return o; };
    const out = {}, seen = {};
    const root = document.querySelector('#ui') ?? document.body;
    for (const el of root.querySelectorAll(sel)) {
        const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
        if (r.width < 2 || r.height < 2 || cs.visibility === 'hidden' || cs.display === 'none') continue;
        if (el.closest('[inert], [aria-hidden=true], [hidden], .sr-only') || opacity(el) < 0.05) continue;
        if (r.right < 0 || r.bottom < 0 || r.left > innerWidth || r.top > innerHeight) continue;
        const rawName = (el.dataset.control || el.getAttribute('aria-label') || el.textContent || el.className || el.tagName)
            .replace(/\s+/g, ' ').trim().replace(/\d+\s*%/g, 'N%').replace(/\d+:\d+/g, 'M:SS').slice(0, 40);
        // Scope by the panel a control lives in, so two panels' "More" stay two controls.
        const sheet = el.closest('.sheet, [role=dialog], dialog');
        const scope = sheet && (sheet.getAttribute('aria-label') || sheet.querySelector('h1, h2, h3, .title, .head')?.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24);
        const name = scope && !rawName.startsWith(scope) ? `${scope} › ${rawName}` : rawName;
        const id = seen[name] ? `${name} #${++seen[name]}` : (seen[name] = 1, name);
        out[id] = [r.x, r.y, r.width, r.height].map(Math.round);
    }
    return out;
};

for (const vp of VIEWPORTS) {
    const ctx = await browser.newContext({ viewport: { width: vp.w, height: vp.h }, deviceScaleFactor: 1, hasTouch: vp.touch, isMobile: vp.touch });
    const page = await ctx.newPage();
    const wait = ms => page.waitForTimeout(ms);
    const tag = `${vp.w}x${vp.h}`;
    const states = {}, shots = [];
    let parts;

    const boot = async () => {
        await page.goto(base);
        await page.waitForFunction(() => window.lavites?.ui?.() && window.lavites.simTime() > 1, null, { timeout: 30000 });
        await wait(800);
        parts = (await page.evaluate(() => window.lavites.ui().inspect())).parts;
    };
    const press = async (x, y) => vp.touch ? page.touchscreen.tap(x, y) : page.mouse.click(x, y);
    const reveal = async () => { await press(8, Math.round((parts.rimY + parts.capBottomY) / 2)); await wait(500); };
    const record = async name => {
        states[name] = { controls: await page.evaluate(HARVEST) };
        const f = `${tag}-${String(shots.length + 1).padStart(2, '0')}-${name.replace(/[^\w-]+/g, '_').slice(0, 40)}.png`;
        await page.screenshot({ path: path.join(out, f) }); shots.push(f);
    };

    await boot();
    await record('rest');
    await reveal();
    await record('revealed');
    await page.evaluate(() => window.lavites.ui().beat(1)); await wait(90);
    await record('revealed, mid-beat');

    const top = Object.entries(states.revealed.controls);
    for (const [id, b] of top) {
        await boot(); await reveal();
        // Re-find by id: a fresh boot may lay out a hair differently.
        const cur = (await page.evaluate(HARVEST))[id] ?? b;
        await press(cur[0] + cur[2] / 2, cur[1] + cur[3] / 2); await wait(650);
        await record(`after ${id}`);
    }

    const protectedBox = parts && (() => {
        const hw = Math.max(...parts.outline.map(o => o.hw));
        return { lamp: [Math.round(parts.axisX - hw), Math.round(parts.capTopY), Math.round(2 * hw), Math.round(parts.baseBottomY - parts.capTopY)] };
    })();
    const map = { viewport: [vp.w, vp.h], protected: protectedBox, source: 'spinodal staging 7d95b56', states };
    fs.writeFileSync(path.join(out, `map-${tag}.json`), JSON.stringify(map, null, 1));
    console.log(tag, Object.keys(states).length, 'states,', new Set(Object.values(states).flatMap(s => Object.keys(s.controls))).size, 'controls');
    await ctx.close();
}
await browser.close();
server.close();
