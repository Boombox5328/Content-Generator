import http from 'http'; import fs from 'fs'; import path from 'path'; import { fileURLToPath } from 'url'; import puppeteer from 'puppeteer-core';
const root = path.dirname(fileURLToPath(import.meta.url)); const mime = { '.html': 'text/html', '.js': 'text/javascript' };
const server = http.createServer((q, r) => { const f = path.join(root, decodeURIComponent(q.url.split('?')[0])); if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'content-type': mime[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r); });
await new Promise((r) => server.listen(0, r));
const b = await puppeteer.launch({ executablePath: '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome', headless: 'new', args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const p = await b.newPage(); await p.goto(`http://127.0.0.1:${server.address().port}/index.html?pr=1`); await p.waitForFunction('window.ptvReady===true');
const r = await p.evaluate(() => window.checkCameras()); console.log(r.map((s) => `${s.id.padEnd(4)} dur ${String(s.dur).padEnd(5)} maxRot ${String(s.maxDegPerSec).padEnd(5)} deg/s  hold-speed ${s.holdSpeed}`).join('\n'));
fs.writeFileSync('out/camcheck.json', JSON.stringify(r, null, 1)); await b.close(); server.close();
