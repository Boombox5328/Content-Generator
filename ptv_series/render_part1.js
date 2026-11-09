// node render_part1.js [--pr 2] [--workers 4] [--from 0] [--to 60] [--out out/part1.mp4]   (frames are captured deterministically, piped to ffmpeg)
import http from 'http'; import fs from 'fs'; import path from 'path'; import { spawn } from 'child_process'; import { fileURLToPath } from 'url'; import puppeteer from 'puppeteer-core';
const root = path.dirname(fileURLToPath(import.meta.url)); const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > -1 ? process.argv[i + 1] : d; };
const PR = +arg('pr', 2), W = +arg('workers', 4), FROM = +arg('from', 0), TO = +arg('to', 60), OUT = path.resolve(root, arg('out', 'out/part1.mp4')), CRF = arg('crf', '18');
const mime = { '.html': 'text/html', '.js': 'text/javascript' };
const server = http.createServer((q, r) => { const f = path.join(root, decodeURIComponent(q.url.split('?')[0])); if (!f.startsWith(root) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'content-type': mime[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r); });
await new Promise((r) => server.listen(0, '127.0.0.1', r)); const url = `http://127.0.0.1:${server.address().port}/index.html?pr=${PR}`;
async function worker() { const b = await puppeteer.launch({ executablePath: '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome', headless: 'new', protocolTimeout: 1800000, args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--hide-scrollbars'] });
  const p = await b.newPage(); await p.setViewport({ width: 1080, height: 1920, deviceScaleFactor: PR }); p.on('pageerror', (e) => console.error('PAGE ERROR', e.message)); await p.goto(url); await p.waitForFunction('window.ptvReady===true', { timeout: 600000 }); return { b, p }; }
const ws = await Promise.all(Array.from({ length: W }, worker));
fs.mkdirSync(path.dirname(OUT), { recursive: true });
const f0 = Math.round(FROM * 30), f1 = Math.round(TO * 30);
const vf = PR === 2 ? ['-vf', 'scale=1080:1920:flags=lanczos'] : [];
const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '30', '-vcodec', 'png', '-i', '-', ...vf, '-c:v', 'libx264', '-preset', 'medium', '-crf', CRF, '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', OUT], { stdio: ['pipe', 'inherit', 'inherit'] });
const done = new Promise((r) => ff.on('close', r)); const pend = new Map(); let next = f0, wr = f0; const t0 = Date.now();
async function flush() { while (pend.has(wr)) { const b = pend.get(wr); pend.delete(wr); wr++; if (!ff.stdin.write(b)) await new Promise((r) => ff.stdin.once('drain', r)); if ((wr - f0) % 30 === 0) console.log(`frame ${wr - f0}/${f1 - f0} ${((Date.now() - t0) / 1000).toFixed(0)}s`); } }
await Promise.all(ws.map(async ({ p }) => { while (true) { const i = next++; if (i >= f1) break; while (pend.size > W * 3) await new Promise((r) => setTimeout(r, 30)); await p.evaluate((f) => window.renderFrame(f), i); pend.set(i, await p.screenshot({ type: 'png', optimizeForSpeed: true })); await flush(); } }));
await flush(); ff.stdin.end(); await done; console.log('wrote', OUT); await Promise.all(ws.map((w) => w.b.close())); server.close();
