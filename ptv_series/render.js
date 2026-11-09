// Headless deterministic renderer (Puppeteer + SwiftShader). Usage:
//   node render.js --still kit [--t 1.2] [--pr 2] [--out out/still_kit.png]
import http from 'http'; import fs from 'fs'; import path from 'path'; import { spawnSync } from 'child_process'; import { fileURLToPath } from 'url'; import puppeteer from 'puppeteer-core';
const root = path.dirname(fileURLToPath(import.meta.url));
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > -1 ? process.argv[i + 1] : d; };
const PR = +arg('pr', 2), CHROME = process.env.CHROME || '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome';
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.mjs': 'text/javascript' };
const server = http.createServer((req, res) => { const f = path.join(root, decodeURIComponent(req.url.split('?')[0])); if (!f.startsWith(root) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); } res.writeHead(200, { 'content-type': mime[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(res); });
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', protocolTimeout: 900000, args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--hide-scrollbars', '--js-flags=--max-old-space-size=4096'] });
const page = await browser.newPage(); await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: PR });
page.on('pageerror', (e) => console.error('PAGE ERROR', e.message)); page.on('console', (m) => { if (['error', 'warning'].includes(m.type())) console.log('[page]', m.text().slice(0, 300)); });
await page.goto(`http://127.0.0.1:${server.address().port}/index.html?pr=${PR}`); await page.waitForFunction('window.ptvReady===true', { timeout: 300000 });
fs.mkdirSync(path.join(root, 'out'), { recursive: true });
const custom = arg('custom', '');
if (custom) { const o = JSON.parse(fs.readFileSync(custom, 'utf8')); const list = Array.isArray(o) ? o : [o];
  for (const [i, c] of list.entries()) { await page.evaluate((c) => window.renderCustom(c), c); const nm = c.name || `custom${i}`; fs.writeFileSync(path.join(root, 'out', `still_${nm}.png`), await page.screenshot({ type: 'png' })); console.log('custom', nm); } }
const names = arg('still', '').split(',').filter(Boolean);
for (const n of names) {
  const t0 = Date.now(); const info = await page.evaluate((n, t) => window.renderStill(n, t), n, +arg('t', 1.2));
  const raw = path.join(root, 'out', `still_${n}${PR === 2 ? '_2x' : ''}.png`); fs.writeFileSync(raw, await page.screenshot({ type: 'png', optimizeForSpeed: true }));
  if (PR === 2) spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', raw, '-vf', 'scale=1080:1920:flags=lanczos', path.join(root, 'out', `still_${n}.png`)]);
  console.log(n, ((Date.now() - t0) / 1000).toFixed(1) + 's', JSON.stringify(info));
}
await browser.close(); server.close();
