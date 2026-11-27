// E2E del Command Center su build demo (VITE_DEMO=1) servita da `vite preview`.
// Uso: VITE_DEMO=1 npx vite build && npx vite preview --port 4173 &  poi  node e2e/run.mjs
import { createRequire } from 'node:module';
import { mkdirSync, readFileSync } from 'node:fs';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const URL = process.env.E2E_URL || 'http://localhost:4173';
const OUT = new globalThis.URL('./out/', import.meta.url).pathname; mkdirSync(OUT, { recursive: true });
const axe = readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8');
let falliti = 0; const ok = (cond, nome) => { console.log(`${cond ? 'OK  ' : 'FAIL'} ${nome}`); if (!cond) falliti++; };

const b = await chromium.launch();
async function entra(w = 1440, h = 1000) {
  const p = await b.newPage({ viewport: { width: w, height: h } });
  const errori = []; p.on('pageerror', (e) => errori.push(e.message)); p.on('console', (m) => m.type() === 'error' && errori.push(m.text()));
  await p.goto(URL); await p.fill('input', 'menotti'); await p.click('button[type=submit]');
  await p.waitForSelector('text=Prossime azioni'); return { p, errori };
}
const titoloDrawer = (p) => p.locator('.drawer h2').textContent();
const centroVisibile = (p) => p.locator('.hero').isVisible();

// 1. vista centrale e nessun errore
let { p, errori } = await entra();
ok(await p.locator('.kpi').count() === 4, 'vista centrale con 4 KPI');
ok((await p.locator('.hero .stato').textContent()).includes('Coordino 1 agente'), 'testo di stato derivato dai dati');

// 2. cinque pannelli in sequenza senza perdere centro, input e conversazione
await p.fill('.dock input', 'Quanti agenti sono attivi?'); await p.press('.dock input', 'Enter');
await p.waitForSelector('.msg.guardian');
ok((await p.locator('.msg.guardian').first().textContent()).includes('agenti al lavoro'), 'chat: risposta dai dati con fonte');
await p.fill('.dock input', 'bozza non inviata');
for (const [voce, titolo] of [['Agenti', 'Agenti'], ['Task', 'Task'], ['Approva', 'Approvazioni'], ['Memoria', 'Memoria condivisa'], ['Statistiche', 'Statistiche']]) {
  await p.click(`.rail button:has-text("${voce}")`); await p.waitForSelector('.drawer');
  ok((await titoloDrawer(p)) === titolo && await centroVisibile(p), `pannello ${titolo} aperto, centro visibile`);
}
ok(await p.inputValue('.dock input') === 'bozza non inviata', 'input di Guardian conservato tra i pannelli');
ok(await p.locator('.msg').count() >= 2, 'conversazione conservata tra i pannelli');
await p.keyboard.press('Escape'); ok(await p.locator('.drawer').count() === 0, 'Esc chiude il pannello');

// 3. ogni voce della rail apre il suo pannello
for (const voce of ['Agenti', 'Aziende', 'Task', 'Approva', 'Memoria', 'Handoff', 'Attività', 'Statistiche', 'Workflow', 'PC', 'Impostazioni']) {
  await p.click(`.rail button:has-text("${voce}")`); ok(await p.locator('.drawer').count() === 1, `rail: ${voce}`);
}
await p.click('.rail button:has-text("Centro")'); ok(await p.locator('.drawer').count() === 0, 'rail: Centro chiude i pannelli');

// 4. KPI, prossime azioni, salute, notifiche
await p.click('.kpi:has-text("Approvazioni in attesa")'); ok((await titoloDrawer(p)) === 'Approvazioni', 'KPI approvazioni');
await p.click('.item:has-text("Decidi l\'approvazione #1")'); ok((await titoloDrawer(p)) === 'Approvazione #1', 'prossima azione → approvazione');
await p.click('button:has-text("Database")'); ok((await titoloDrawer(p)) === 'Salute del sistema', 'pillola salute');
await p.click('button[aria-label^="Notifiche"]'); ok((await titoloDrawer(p)) === 'Notifiche', 'campanella notifiche');
await p.click('.drawer .item:has-text("Invio preventivo")'); ok((await titoloDrawer(p)) === 'Approvazione #1', 'notifica → pannello collegato');
ok(await p.locator('.crumbs').count() === 1, 'traccia di navigazione');
await p.click('button[aria-label="Indietro"]'); ok((await titoloDrawer(p)) === 'Notifiche', 'Indietro');

// 5. approvazione reale (demo): task #3 needs_approval -> ready
await p.click('.drawer .item:has-text("Invio preventivo")'); await p.click('.drawer button:has-text("Approva")');
await p.waitForSelector('.toast:has-text("Approvata")'); ok(true, 'Approva → toast');
await p.click('.rail button:has-text("Task")'); await p.click('.drawer button:has-text("Tutti")');
await p.click('.drawer .item:has-text("#3 Invio preventivo")');
ok(await p.locator('.drawer .pill:has-text("Pronto")').count() >= 1, 'task #3 tornato Pronto dopo l\'approvazione');

// 6. vincoli: titolo duplicato rifiutato, nuovo task creato
await p.click('.rail button:has-text("Task")'); await p.click('.drawer button:has-text("Nuovo task")');
await p.fill('.drawer form .input >> nth=0', 'Sito demo Ottica Ungari');
await p.selectOption('.drawer form select >> nth=0', { label: 'Siti web' }); await p.click('.drawer form button:has-text("Crea task")');
ok(await p.locator('.toast.err:has-text("Esiste già")').count() === 1, 'titolo duplicato rifiutato con messaggio leggibile');
await p.fill('.drawer form .input >> nth=0', 'Verifica E2E'); await p.click('.drawer form button:has-text("Crea task")');
await p.waitForSelector('.toast:has-text("Task creato")'); ok(true, 'nuovo task creato');
await p.fill('.drawer form .input >> nth=0', 'password=segreta123').catch(() => {});

// 7. palette Ctrl+K e chat che apre un pannello
await p.keyboard.press('Escape'); await p.keyboard.press('Control+k'); ok(await p.locator('.palette').isVisible(), 'Ctrl+K apre la palette');
await p.keyboard.type('Ottica'); await p.keyboard.press('Enter'); ok((await titoloDrawer(p)) === 'Task #1', 'palette → task #1');
await p.fill('.dock input', 'Cosa è bloccato?'); await p.press('.dock input', 'Enter');
await p.waitForTimeout(200); ok((await p.locator('.msg.guardian').last().textContent()).includes('#5'), 'chat: cosa è bloccato');
await p.click('.item:has-text("Sito demo Ottica Ungari") >> nth=0').catch(() => {});
await p.click('.rail button:has-text("Task")'); await p.click('.drawer button:has-text("Tutti")'); await p.click('.drawer .item:has-text("#4 Pubblicazione")');
await p.fill('.dock input', 'perché questo task è fermo?'); await p.press('.dock input', 'Enter'); await p.waitForTimeout(200);
ok((await p.locator('.msg.guardian').last().textContent()).includes('dipende dal task #1'), 'chat con contesto del pannello');

// 8. statistiche: vista tabella
await p.click('.rail button:has-text("Statistiche")'); await p.click('.drawer button:has-text("Vista tabella") >> nth=0');
ok(await p.locator('.drawer table.data').count() >= 1, 'grafico → vista tabella');

// 9. accessibilità (axe) sulla vista centrale
await p.keyboard.press('Escape');
await p.addScriptTag({ content: axe });
const ris = await p.evaluate(async () => (await window.axe.run(document, { resultTypes: ['violations'] })).violations
  .filter((v) => ['serious', 'critical'].includes(v.impact)).map((v) => `${v.id} (${v.nodes.length})`));
ok(ris.length === 0, `axe: nessuna violazione seria/critica ${ris.join(', ')}`);
const senzaNome = await p.evaluate(() => [...document.querySelectorAll('button')].filter((x) => !(x.getAttribute('aria-label') || x.textContent.trim())).length);
ok(senzaNome === 0, 'ogni pulsante ha un nome accessibile');
ok(errori.length === 0, `nessun errore in console ${errori.slice(0, 2).join(' | ')}`);

// 10. larghezze: nessuno scroll orizzontale, screenshot
for (const [w, h] of [[390, 844], [768, 1024], [1280, 900], [1920, 1080]]) {
  const r = await entra(w, h);
  await r.p.screenshot({ path: `${OUT}centro-${w}.png` });
  await r.p.click('.kpi >> nth=1'); await r.p.waitForSelector('.drawer'); await r.p.waitForTimeout(500); await r.p.screenshot({ path: `${OUT}pannello-${w}.png` });
  const sw = await r.p.evaluate(() => document.documentElement.scrollWidth);
  ok(sw <= w && r.errori.length === 0, `${w}px: nessuno scroll orizzontale (${sw}) e nessun errore`);
  await r.p.close();
}
await b.close();
console.log(falliti ? `\n${falliti} controlli FALLITI` : '\nTutti i controlli E2E superati');
process.exit(falliti ? 1 : 0);
