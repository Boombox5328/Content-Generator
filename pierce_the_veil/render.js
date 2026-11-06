// Headless frame capture: Puppeteer (SwiftShader WebGL) -> PNG frames -> ffmpeg (H.264, veryfast, CRF 20).
// usage: node render.js [--from 0] [--to 3] [--fps 30] [--workers 4] [--out out/test.mp4] [--stills 0,1.5,2.9]
import http from 'http'; import fs from 'fs'; import path from 'path'; import { spawn } from 'child_process';
import { fileURLToPath } from 'url'; import puppeteer from 'puppeteer-core';

const root = path.dirname(fileURLToPath(import.meta.url));
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > -1 ? process.argv[i + 1] : d; };
const FPS = +arg('fps', 30), FROM = +arg('from', 0), TO = +arg('to', 75), WORKERS = +arg('workers', 4);
const OUT = path.resolve(root, arg('out', 'out/ptv_history_reel.mp4'));
const STILLS = arg('stills', '').split(',').filter(Boolean).map(Number);
const CHROME = process.env.CHROME || '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome';
fs.mkdirSync(path.dirname(OUT), { recursive: true });

const mime = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  const f = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (!f.startsWith(root) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'content-type': mime[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(res);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const url = `http://127.0.0.1:${server.address().port}/index.html`;

async function worker() {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: [
    '--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--hide-scrollbars'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => console.error('PAGE ERROR', e.message));
  await page.goto(url); await page.waitForFunction('window.ptvReady===true', { timeout: 120000 });
  return { browser, page, shot: async (t) => { await page.evaluate((x) => window.renderFrame(x), t); return page.screenshot({ type: 'png', optimizeForSpeed: true }); } };
}

const workers = await Promise.all(Array.from({ length: WORKERS }, worker));
for (const t of STILLS) fs.writeFileSync(path.join(path.dirname(OUT), `still_${t.toFixed(2)}.png`), await workers[0].shot(t));

const f0 = Math.round(FROM * FPS), f1 = Math.round(TO * FPS);
if (f1 > f0 && !arg('no-video', false)) {
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-vcodec', 'png', '-i', '-',
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', OUT], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((r) => ff.on('close', r));
  const pending = new Map(); let next = f0, write = f0; const t0 = Date.now();
  async function flush() {
    while (pending.has(write)) { const b = pending.get(write); pending.delete(write); write++;
      if (!ff.stdin.write(b)) await new Promise((r) => ff.stdin.once('drain', r));
      if ((write - f0) % 30 === 0) console.log(`frame ${write - f0}/${f1 - f0}  ${((Date.now() - t0) / 1000).toFixed(0)}s`); }
  }
  await Promise.all(workers.map(async (w) => {
    while (true) {
      const i = next++; if (i >= f1) break;
      while (pending.size > WORKERS * 3) await new Promise((r) => setTimeout(r, 20)); // bound memory
      pending.set(i, await w.shot(i / FPS)); await flush();
    }
  }));
  await flush(); ff.stdin.end(); await done; console.log('wrote', OUT);
}
await Promise.all(workers.map((w) => w.browser.close())); server.close();
