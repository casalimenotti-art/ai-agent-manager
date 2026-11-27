// E2E del volto di NEXO Sentinel (build demo servita da `vite preview` su 4173).
// Controlla: modalità WebGL, reazione a una richiesta, fasi della conversazione finta, lampo sugli eventi,
// ripiego su immagine senza WebGL e sul telefono, accessibilità e console pulita.
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const URL = process.env.E2E_URL || 'http://localhost:4173';
const OUT = new globalThis.URL('./out/', import.meta.url).pathname;
const axe = readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8');
let falliti = 0; const ok = (c, m) => { console.log(`${c ? 'OK  ' : 'FAIL'} ${m}`); if (!c) falliti++; };

const b = await chromium.launch();
async function entra(w, h, query = '', ctxOpts = {}) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, ...ctxOpts });
  const p = await ctx.newPage();
  const errori = []; p.on('pageerror', (e) => errori.push(e.message)); p.on('console', (m) => m.type() === 'error' && errori.push(m.text()));
  const scaricati = []; p.on('request', (r) => scaricati.push(r.url()));
  await p.goto(URL + query); await p.fill('input', 'menotti'); await p.click('button[type=submit]');
  await p.waitForSelector('text=Prossime azioni');
  await p.waitForSelector('.volto-sfondo.pronto', { timeout: 15000 });
  return { p, ctx, errori, scaricati };
}
const attr = (p, n) => p.locator('.volto-sfondo').getAttribute(n);
const intensita = async (p) => Number(await attr(p, 'data-volto-intensita'));

{
  const { p, ctx, errori } = await entra(1440, 900, '?voce=finta&cervello=finto');
  const modo = await attr(p, 'data-volto-modalita');
  ok(modo === 'webgl', `1440 px: volto animato con WebGL2 (modalità: ${modo})`);
  await p.waitForTimeout(1500);
  const riposo = await intensita(p);
  ok(riposo <= 0.25, `a riposo l'occhio è fioco (${riposo})`);
  await p.screenshot({ path: `${OUT}volto-riposo.png` });
  await p.fill('.dock input', 'quanti agenti sono attivi?'); await p.press('.dock input', 'Enter');
  await p.waitForTimeout(400);
  const sveglio = await intensita(p);
  ok(sveglio >= 0.5, `dopo una domanda l'occhio si accende entro 400 ms (${sveglio})`);
  await p.screenshot({ path: `${OUT}volto-richiesta.png` });
  await p.waitForTimeout(2500);
  ok(await intensita(p) < sveglio, 'poi torna a riposo');
  // conversazione finta: ascolto → elaborazione → parla → ascolto
  const fasi = new Set();
  const segui = setInterval(async () => { try { fasi.add(await attr(p, 'data-volto-fase')); } catch { /* pagina chiusa */ } }, 50);
  await p.click('.conv-btn'); await p.waitForSelector('.conv-barra[data-fase="ascolto"]');
  await p.evaluate(() => window.__guardianDici('Raccontami una storia breve'));
  await p.waitForTimeout(4000);
  clearInterval(segui);
  ok(['ascolto', 'elaborazione', 'parla'].every((f) => fasi.has(f)), `il volto segue le fasi della conversazione (${[...fasi].join(' → ')})`);
  await p.keyboard.press('Escape'); await p.waitForTimeout(200);
  // evento demo: spostare un task produce un evento → lampo
  await p.click('.dock button:has-text("Nascondi")').catch(() => {});
  await p.locator('.porta:has-text("Vendite")').evaluate((e) => e.scrollIntoView({ block: 'center' }));
  await p.click('.porta:has-text("Vendite")');
  const lampiPrima = Number(await attr(p, 'data-volto-lampi') ?? 0);
  await p.selectOption('[data-task="2"] select', { label: 'In corso' });
  await p.waitForSelector('.toast:has-text("Task #2")');
  await p.waitForTimeout(1000); // i dati si ricaricano dopo ~400 ms, poi il lampo
  const lampiDopo = Number(await attr(p, 'data-volto-lampi') ?? 0);
  ok(lampiDopo > lampiPrima, `un evento nuovo (task spostato) fa lampeggiare l'occhio (${lampiPrima} → ${lampiDopo})`);
  await p.keyboard.press('Escape');
  await p.addScriptTag({ content: axe });
  const vio = await p.evaluate(async () => (await window.axe.run(document, { resultTypes: ['violations'] })).violations
    .filter((v) => ['serious', 'critical'].includes(v.impact)).map((v) => `${v.id} (${v.nodes.length})`));
  ok(vio.length === 0, `axe: nessuna violazione seria sopra il volto ${vio.join(', ')}`);
  ok(errori.length === 0, `console pulita ${errori.slice(0, 2).join(' | ')}`);
  await ctx.close();
}
{ // senza WebGL: immagine con bagliore
  const ctx = await b.newContext({ viewport: { width: 1280, height: 800 } });
  await ctx.addInitScript(() => { const o = HTMLCanvasElement.prototype.getContext; HTMLCanvasElement.prototype.getContext = function (t, ...a) { return t === 'webgl2' ? null : o.call(this, t, ...a); }; });
  const p = await ctx.newPage(); const errori = []; p.on('pageerror', (e) => errori.push(e.message));
  await p.goto(URL); await p.fill('input', 'menotti'); await p.click('button[type=submit]'); await p.waitForSelector('.volto-sfondo.pronto');
  ok(await attr(p, 'data-volto-modalita') === 'immagine' && await p.locator('.volto-img').count() === 1, 'senza WebGL2: immagine ferma con l\'occhio che si illumina');
  ok(errori.length === 0, 'nessun errore senza WebGL');
  await ctx.close();
}
{ // telefono: immagine da 960 px, niente strati grandi
  const { p, ctx, scaricati } = await entra(390, 844);
  ok(await attr(p, 'data-volto-modalita') === 'immagine', 'telefono: immagine, niente WebGL');
  ok(!scaricati.some((u) => /\/volto\/luce\.webp$/.test(u)) && scaricati.some((u) => /\/volto\/960\/base\.webp$/.test(u)), 'telefono: scarica solo la base da 960 px');
  const sw = await p.evaluate(() => document.documentElement.scrollWidth);
  ok(sw <= 390, `telefono: nessuno scroll orizzontale (${sw})`);
  await p.screenshot({ path: `${OUT}volto-390.png`, fullPage: false });
  await ctx.close();
}
for (const [w, h] of [[768, 1024], [1280, 800], [1920, 1080]]) {
  const { p, ctx, errori } = await entra(w, h);
  await p.waitForTimeout(800);
  const sw = await p.evaluate(() => document.documentElement.scrollWidth);
  ok(sw <= w && errori.length === 0, `${w} px: volto senza scroll orizzontale né errori (${sw})`);
  if (w >= 1280) await p.screenshot({ path: `${OUT}volto-${w}.png` });
  await ctx.close();
}
await b.close();
console.log(falliti ? `${falliti} FALLITI` : 'Volto: tutti i controlli superati');
process.exit(falliti ? 1 : 0);
