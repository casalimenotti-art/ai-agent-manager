// E2E del livello A: microfono finto di Chromium (file WAV) → servizio vocale locale del bridge (riconoscitore di prova)
// → la conversazione sceglie da sola l'ascolto locale e privato e capisce la frase.
import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';
import { writeFileSync } from 'node:fs';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const REPO = new globalThis.URL('../../', import.meta.url).pathname;
const OUT = new globalThis.URL('./out/', import.meta.url).pathname;

// 1) audio: 1,2 s di "voce" (tono modulato) poi 2 s di silenzio, in loop
const sr = 48000, n = sr * 3.2, buf = Buffer.alloc(44 + n * 2);
buf.write('RIFF', 0); buf.writeUInt32LE(36 + n * 2, 4); buf.write('WAVEfmt ', 8); buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20);
buf.writeUInt16LE(1, 22); buf.writeUInt32LE(sr, 24); buf.writeUInt32LE(sr * 2, 28); buf.writeUInt16LE(2, 32); buf.writeUInt16LE(16, 34);
buf.write('data', 36); buf.writeUInt32LE(n * 2, 40);
for (let i = 0; i < n; i++) { const t = i / sr; const v = t < 1.2 ? 0.4 * Math.sin(2 * Math.PI * 220 * t) * (0.6 + 0.4 * Math.sin(2 * Math.PI * 3 * t)) : 0;
  buf.writeInt16LE(Math.round(v * 32767), 44 + i * 2); }
writeFileSync(OUT + 'voce-finta.wav', buf);

// 2) servizio vocale locale reale, con un riconoscitore di prova
const py = spawn('python3', ['-c', `
import sys, threading; sys.path.insert(0, ${JSON.stringify(REPO)})
from bridge.voce_locale import crea_server
srv = crea_server(lambda c, sr: 'quanti agenti sono attivi', 'riconoscitore di prova', porta=8765, origini={'http://localhost:4173'})
print('PRONTO', flush=True); srv.serve_forever()`], { stdio: ['ignore', 'pipe', 'inherit'] });
await new Promise((ok) => py.stdout.on('data', (d) => String(d).includes('PRONTO') && ok()));

let falliti = 0; const ok = (c, m) => { console.log(`${c ? 'OK  ' : 'FAIL'} ${m}`); if (!c) falliti++; };
const b = await chromium.launch({ args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', `--use-file-for-fake-audio-capture=${OUT}voce-finta.wav`] });
const p = await b.newPage({ viewport: { width: 1440, height: 1000 } });
await p.goto('http://localhost:4173'); await p.fill('input', 'menotti'); await p.click('button[type=submit]'); await p.waitForSelector('text=Prossime azioni');
await p.click('.conv-btn');
await p.waitForSelector('.conv-barra .pill:has-text("Ascolto locale")', { timeout: 8000 });
ok((await p.locator('.conv-barra .pill').first().textContent()).includes('privato'), 'livello A scelto da solo: ascolto locale e privato');
await p.waitForSelector('.conv-barra:has-text("quanti agenti sono attivi")', { timeout: 15000 }).catch(() => {});
await p.click('.dock button:has-text("Conversazione (")').catch(() => {});
ok(await p.locator('.msg.user:has-text("quanti agenti sono attivi")').count() >= 1, 'VAD + WAV 16 kHz + trascrizione locale: frase capita');
ok(await p.locator('.msg.guardian:has-text("agenti al lavoro")').count() >= 1, 'Guardian risponde alla frase capita in locale');
await p.screenshot({ path: OUT + 'voce-locale.png' });
await b.close(); py.kill();
console.log(falliti ? `${falliti} FALLITI` : 'Voce locale: tutti i controlli superati');
process.exit(falliti ? 1 : 0);
