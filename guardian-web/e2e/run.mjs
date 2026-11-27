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
async function entra(w = 1440, h = 1000, query = '') {
  const p = await b.newPage({ viewport: { width: w, height: h } });
  const errori = []; p.on('pageerror', (e) => errori.push(e.message)); p.on('console', (m) => m.type() === 'error' && errori.push(m.text()));
  await p.goto(URL + query); await p.fill('input', 'menotti'); await p.click('button[type=submit]');
  await p.waitForSelector(query.includes('parete') ? '.parete' : 'text=Prossime azioni'); return { p, errori };
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


// 8b. stanze dell'HQ (pagina nuova: dati demo freschi)
{
  const { p: q, errori: err2 } = await entra();
  ok(await q.locator('.porta').count() === 3, 'orbita: tre stanze');
  await q.click('.porta:has-text("Vendite")');
  ok(await q.locator('.stanza h2').textContent() === 'Vendite' && await q.locator('.nucleo-compatto').isVisible(), 'stanza Vendite aperta, Guardian presente (compatto)');
  ok(new globalThis.URL(q.url()).searchParams.get('s') === 'vendite', 'stanza nell\'URL condivisibile');
  await q.selectOption('[data-task="2"] select', { label: 'In corso' });
  await q.waitForSelector('.toast:has-text("Task #2")');
  ok(await q.locator('[data-colonna="corso"] [data-task="2"]').count() === 1, 'kanban: task #2 spostato in corso (stato reale)');
  await q.keyboard.press('Escape'); ok(await q.locator('.porta').count() === 3, 'Esc: ritorno all\'orbita');
  await q.click('.porta:has-text("Sviluppo")');
  await q.dragAndDrop('[data-task="4"]', '[data-colonna="corso"]');
  await q.waitForSelector('.toast.err');
  ok((await q.locator('.toast.err').last().textContent()).includes('dipendenze') && (await q.locator('.toast.err').last().textContent()).includes('annullata'), 'kanban ottimistico: rifiuto del vincolo, modifica annullata e messaggio chiaro');
  ok(await q.locator('[data-colonna="coda"] [data-task="4"]').count() === 1, 'kanban: il task resta dov\'era');
  await q.click('.nucleo-compatto'); ok(await q.locator('.porta').count() === 3, 'clic sul nucleo: ritorno all\'orbita');
  await q.fill('.dock input', 'Guardian, apri amministrazione'); await q.press('.dock input', 'Enter');
  ok(await q.locator('.stanza h2').textContent() === 'Amministrazione', 'comando "apri amministrazione"');
  await q.fill('.dock input', 'cosa succede in questa stanza?'); await q.press('.dock input', 'Enter'); await q.waitForTimeout(200);
  ok((await q.locator('.msg.guardian').last().textContent()).includes('Stanza Amministrazione'), 'chat con il contesto della stanza');
  await q.keyboard.press('Control+k'); await q.keyboard.type('stanza vendite'); await q.keyboard.press('Enter');
  ok(await q.locator('.stanza h2').textContent() === 'Vendite', 'palette → stanza');
  await q.click('.scheda .link-t >> nth=0'); ok(await q.locator('.drawer').count() === 1 && await q.locator('.stanza').isVisible(), 'pannello sopra la stanza, stanza visibile');
  await q.keyboard.press('Escape'); ok(await q.locator('.stanza').isVisible(), 'Esc chiude prima il pannello, poi la stanza');
  await q.screenshot({ path: `${OUT}stanza-1440.png` });
  ok(err2.length === 0, `stanze: nessun errore in console ${err2.slice(0, 2).join(' | ')}`);
  await q.close();
}


// 8c. conversazione a voce (microfono simulato SOLO nel test: build demo + ?voce=finta)
{
  const q = await b.newPage({ viewport: { width: 1440, height: 1000 } });
  const err3 = []; q.on('pageerror', (e) => err3.push(e.message)); q.on('console', (m) => m.type() === 'error' && err3.push(m.text()));
  await q.goto(URL + '?voce=finta'); await q.fill('input', 'menotti'); await q.click('button[type=submit]'); await q.waitForSelector('text=Prossime azioni');
  await q.click('.conv-btn'); await q.waitForSelector('.conv-barra:has-text("Ti ascolto")');
  ok((await q.locator('.core').getAttribute('data-stato')) === 'listening', 'conversazione: nucleo in ascolto');
  const dici = async (t) => { await q.waitForSelector('.conv-barra[data-fase="ascolto"]', { timeout: 6000 }); await q.evaluate((x) => window.__guardianDici(x), t); };
  await dici('quanti agenti sono attivi?');
  await q.waitForFunction(() => (window.__guardianParlato || []).length > 0);
  ok((await q.evaluate(() => window.__guardianParlato.join(' '))).includes('agenti al lavoro'), 'conversazione: risponde a voce dai dati');
  await q.click('.dock button:has-text("Conversazione (")');
  ok(await q.locator('.msg.user:has-text("quanti agenti")').count() === 1, 'conversazione: anche nel registro della chat');
  await q.click('.dock button:has-text("Nascondi")');
  await q.waitForSelector('.conv-barra[data-fase="ascolto"]', { timeout: 5000 }); ok(true, 'conversazione: dopo la risposta torna ad ascoltare');
  await q.evaluate(() => { window.__guardianParlato = []; });
  await dici('cosa mi consigli di fare?');
  await q.waitForSelector('.conv-barra[data-fase="parla"]');
  ok((await q.locator('.core').getAttribute('data-stato')) === 'speaking', 'conversazione: nucleo in modalità parla');
  await q.evaluate(() => { window.__guardianLivello = 0.3; }); await q.waitForSelector('.conv-barra[data-fase="ascolto"]', { timeout: 2000 });
  await q.evaluate(() => { window.__guardianLivello = 0; });
  ok((await q.evaluate(() => window.__guardianParlato.length)) < 4, 'barge-in: parlandogli sopra si zittisce e ascolta');
  await dici('Guardian, apri vendite'); await q.waitForSelector('.stanza h2:has-text("Vendite")'); ok(true, 'voce: «apri vendite» apre la stanza');
  await dici('approva il preventivo'); await q.waitForSelector('.drawer h2:has-text("Approvazione #1")');
  ok(await q.locator('.drawer .pill.warn:has-text("richiesta")').count() === 1, 'voce: «approva» apre il pannello ma NON approva (serve il clic)');
  await q.keyboard.press('Escape'); ok(await q.locator('.conv-barra').count() === 1, 'Esc chiude prima il pannello, la conversazione resta');
  await dici('silenzio'); await q.waitForTimeout(300); ok(await q.locator('.conv-barra').count() === 1, '«silenzio» non chiude la conversazione');
  await dici('basta'); await q.waitForTimeout(100); await q.waitForSelector('.conv-barra', { state: 'detached', timeout: 4000 }); ok(true, '«basta» chiude la conversazione');
  await q.click('.rail button:has-text("Impostazioni")');
  ok((await q.locator('.drawer:has-text("Diagnostica voce")').textContent()).includes('Testo → prima frase'), 'diagnostica voce con misure');
  await q.click('.rail button:has-text("Centro")'); await q.click('.conv-btn'); await q.waitForSelector('.conv-barra');
  await q.click('.conv-barra button:has-text("Termina")'); ok(await q.locator('.conv-barra').count() === 0, 'pulsante Termina');
  ok(err3.length === 0, `conversazione: nessun errore in console ${err3.slice(0, 2).join(' | ')}`);
  await q.close();
}


// 8d. cervello (finto, SOLO in demo con ?cervello=finto): domande aperte → risposta a frasi, anche a voce
{
  const q = await b.newPage({ viewport: { width: 1440, height: 1000 } });
  const err4 = []; q.on('pageerror', (e) => err4.push(e.message));
  await q.goto(URL); await q.fill('input', 'menotti'); await q.click('button[type=submit]'); await q.waitForSelector('text=Prossime azioni');
  ok(await q.locator('.pill:has-text("Cervello offline")').count() === 1, 'senza cervello: stato offline dichiarato');
  await q.close();
  const c = await b.newPage({ viewport: { width: 1440, height: 1000 } });
  await c.goto(URL + '?cervello=finto&voce=finta'); await c.fill('input', 'menotti'); await c.click('button[type=submit]'); await c.waitForSelector('text=Prossime azioni');
  ok(await c.locator('.pill:has-text("Cervello online")').count() === 1, 'cervello online mostrato');
  await c.fill('.dock input', 'Scrivimi un piano per domani'); await c.press('.dock input', 'Enter');
  await c.waitForSelector('.msg.guardian:has-text("Risposta di prova del cervello")');
  ok((await c.locator('.msg.guardian').last().textContent()).includes('cervello sul PC'), 'chat: domanda aperta → cervello, con la fonte');
  await c.click('.conv-btn'); await c.waitForSelector('.conv-barra[data-fase="ascolto"]');
  await c.evaluate(() => window.__guardianDici('Raccontami una storia breve'));
  await c.waitForFunction(() => (window.__guardianParlato || []).length >= 2, null, { timeout: 6000 });
  ok((await c.evaluate(() => window.__guardianParlato.join(' '))).includes('Ho ricevuto'), 'voce: il cervello risponde a voce frase per frase');
  await c.click('.conv-barra button:has-text("Termina")');
  ok(err4.length === 0, `cervello: nessun errore in console ${err4.slice(0, 2).join(' | ')}`);
  await c.close();
}

// 9. accessibilità (axe) sulla vista centrale
await p.keyboard.press('Escape');
await p.addScriptTag({ content: axe });
const ris = await p.evaluate(async () => (await window.axe.run(document, { resultTypes: ['violations'] })).violations
  .filter((v) => ['serious', 'critical'].includes(v.impact)).map((v) => `${v.id} (${v.nodes.length})`));
ok(ris.length === 0, `axe: nessuna violazione seria/critica ${ris.join(', ')}`);
const senzaNome = await p.evaluate(() => [...document.querySelectorAll('button')].filter((x) => !(x.getAttribute('aria-label') || x.textContent.trim())).length);
ok(senzaNome === 0, 'ogni pulsante ha un nome accessibile');
ok(errori.length === 0, `nessun errore in console ${errori.slice(0, 2).join(' | ')}`);

// 8c. Ondata 8: presenza e mappa operativa
{
  const { p: q, errori: e3 } = await entra();
  ok((await q.locator('.presenti').getAttribute('aria-label')).includes('Tu (Centro)'), 'presenza: tu nell\'HQ, al centro');
  await q.click('.porta:has-text("Vendite")'); await q.waitForTimeout(100);
  ok((await q.locator('.presenti').getAttribute('aria-label')).includes('Tu (Vendite)'), 'presenza: segue la stanza in cui sei');
  await q.keyboard.press('Escape');
  await q.click('.rail button:has-text("Mappa")'); await q.waitForSelector('.mappa-svg');
  const nodi = await q.locator('.mappa-nodo').count(); const archi = await q.locator('.mappa-arco').count();
  ok(nodi >= 6 && archi >= 3, `mappa: ${nodi} nodi e ${archi} collegamenti dai dati`);
  ok(await q.locator('.mappa-nodo[aria-label^="#"]').count() >= 1 && await q.locator('.mappa-nodo[aria-label*="Completato"]').count() === 0, 'mappa: solo task aperti');
  await q.locator('.mappa-nodo[aria-label^="#"]').first().focus(); await q.keyboard.press('Enter');
  ok((await q.locator('.drawer h2').textContent()).startsWith('Task #'), 'mappa: Invio su un task apre il suo pannello');
  ok(e3.length === 0, `mappa e presenza senza errori in console ${e3.slice(0, 2).join(' | ')}`);
  await q.screenshot({ path: `${OUT}mappa.png` });
  await q.close();
}

// 8d. Ondate 5 e 7: pipeline vendite, scadenze, costi (dati di esempio, niente dati personali)
{
  const { p: q, errori: e4 } = await entra();
  ok(await q.locator('.item:has-text("Scadenza passata")').count() >= 1, 'prossime azioni: scadenza passata in evidenza');
  await q.click('.porta:has-text("Vendite")'); await q.waitForSelector('.pipeline');
  ok(await q.locator('.pipeline-fase').count() === 6 && await q.locator('[data-vendita]').count() === 5, 'pipeline: 6 fasi, 5 aziende');
  await q.click('.pipeline button:has-text("Aggiungi")');
  await q.fill('.pipeline input >> nth=0', 'Gelateria Neve'); await q.fill('.pipeline input[placeholder^="es. visita"]', 'visita 27/11');
  await q.fill('.pipeline .field:has-text("Prossimo passo") input', 'scrivere a gelateria@example.com');
  await q.click('.pipeline button[type=submit]'); await q.waitForSelector('.toast.err');
  ok((await q.locator('.toast.err').last().textContent()).includes('CSV dei lead'), 'pipeline: email rifiutata, i dati dei clienti restano nel CSV');
  await q.fill('.pipeline .field:has-text("Prossimo passo") input', 'preparare la bozza'); await q.click('.pipeline button[type=submit]');
  await q.waitForSelector('.toast:has-text("Aggiunta alla pipeline")');
  ok(await q.locator('[data-fase="contatto"] .scheda-mini:has-text("Gelateria Neve")').count() === 1, 'pipeline: nuova azienda in Contatto');
  await q.selectOption('[data-vendita="2"] select', 'vinto'); await q.waitForSelector('.toast:has-text("Ottica Ungari")');
  ok(await q.locator('[data-fase="vinto"] [data-vendita="2"]').count() === 1, 'pipeline: cambio di fase');
  await q.keyboard.press('Escape'); await q.click('.porta:has-text("Amministrazione")'); await q.waitForSelector('[aria-label="Scadenze (30 giorni)"]');
  ok(await q.locator('[data-scadenza="2"] .pill.crit').count() === 1, 'scadenze: quella passata è rossa');
  await q.click('[data-scadenza="2"] button:has-text("Fatta")'); await q.waitForSelector('.toast:has-text("Fatta")');
  ok(await q.locator('[data-scadenza="2"]').count() === 0, 'scadenze: segnata come fatta, sparisce');
  const prima = await q.locator('[aria-label="Costi"] .porta-numeri b').first().textContent();
  await q.click('[aria-label="Costi"] button:has-text("Aggiungi")');
  await q.fill('[aria-label="Costi"] .field:has-text("Descrizione") input', 'Canva Pro'); await q.fill('[aria-label="Costi"] .field:has-text("Importo") input', '11');
  await q.click('[aria-label="Costi"] button[type=submit]'); await q.waitForSelector('.toast.err');
  ok((await q.locator('.toast.err').last().textContent()).includes('fonte') || await q.locator('[aria-label="Costi"] input:invalid').count() > 0, 'costi: senza fonte non si salva');
  await q.fill('[aria-label="Costi"] input[placeholder^="es. fattura"]', 'estratto conto'); await q.click('[aria-label="Costi"] button[type=submit]');
  await q.waitForSelector('.toast:has-text("Costo salvato")');
  const dopo = await q.locator('[aria-label="Costi"] .porta-numeri b').first().textContent();
  ok(prima !== dopo, `costi: totale del mese aggiornato (${prima} → ${dopo})`);
  await q.fill('.dock input', 'quanto spendiamo questo mese?'); await q.press('.dock input', 'Enter'); await q.waitForTimeout(250);
  await q.click('.dock button:has-text("Conversazione (")').catch(() => {});
  ok(await q.locator('.msg.guardian:has-text("Questo mese")').count() >= 1, 'domanda a Guardian sui costi: risposta dai dati');
  ok(e4.length === 0, `vendite e amministrazione senza errori in console ${e4.slice(0, 2).join(' | ')}`);
  await q.screenshot({ path: `${OUT}amministrazione.png`, fullPage: true });
  await q.close();
}

// 8e. Ondata 9: suoni (spenti di default) e modalità parete
{
  const { p: q, errori: e5 } = await entra(1440, 1000, '?voce=finta');
  const suoni = () => q.evaluate(() => window.__guardianSuoni ?? []);
  await q.click('.conv-btn'); await q.waitForSelector('.conv-barra[data-fase="ascolto"]'); await q.keyboard.press('Escape'); await q.waitForTimeout(150);
  ok((await suoni()).length === 0, 'suoni spenti di default: nessun suono');
  await q.click('.rail button:has-text("Impostazioni")'); await q.check('label:has-text("Suoni discreti") input');
  ok((await suoni()).join() === 'notifica', 'attivando i suoni se ne sente uno di prova');
  await q.click('.drawer button[aria-label="Chiudi pannello"]');
  await q.click('.conv-btn'); await q.waitForSelector('.conv-barra[data-fase="ascolto"]'); await q.keyboard.press('Escape'); await q.waitForTimeout(150);
  ok((await suoni()).join() === 'notifica,ascolto,fine', 'conversazione: suono di inizio e di fine');
  ok(e5.length === 0, `suoni senza errori in console ${e5.slice(0, 2).join(' | ')}`);
  await q.close();
  const { p: w, errori: e6 } = await entra(1920, 1080, '?parete=1');
  ok(await w.locator('.parete-stanza').count() === 3 && await w.locator('.rail').count() === 0 && await w.locator('.dock').count() === 0, 'parete: tre stanze, niente menu né chat');
  ok(new globalThis.URL(w.url()).searchParams.get('parete') === '1', 'parete: resta nell\'indirizzo (condivisibile)');
  await w.addScriptTag({ content: axe });
  const vp = await w.evaluate(async () => (await window.axe.run(document, { resultTypes: ['violations'] })).violations.filter((v) => ['serious', 'critical'].includes(v.impact)).map((v) => v.id));
  ok(vp.length === 0, `parete: axe senza violazioni serie ${vp.join(', ')}`);
  await w.screenshot({ path: `${OUT}parete-1920.png` });
  await w.keyboard.press('Escape'); await w.waitForSelector('.hero');
  ok(new globalThis.URL(w.url()).searchParams.get('parete') === null, 'Esc: esce dalla parete e torna al centro');
  ok(e6.length === 0, `parete senza errori in console ${e6.slice(0, 2).join(' | ')}`);
  await w.close();
  const { p: m } = await entra(390, 844, '?parete=1');
  const swp = await m.evaluate(() => document.documentElement.scrollWidth);
  ok(swp <= 390, `parete a 390 px senza scroll orizzontale (${swp})`);
  await m.close();
}

// 8f. Ondata 10: app installabile (manifest + service worker della sola shell)
{
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 } });
  const q = await ctx.newPage();
  await q.goto(URL);
  const man = await q.evaluate(async () => { const l = document.querySelector('link[rel=manifest]'); return l ? (await fetch(l.href)).json() : null; });
  ok(man?.display === 'standalone' && man.icons.some((i) => i.purpose === 'maskable') && man.icons.some((i) => i.sizes === '512x512'), 'manifest: standalone, icone 192/512 e maskable');
  const icone = await q.evaluate(async (m) => Promise.all(m.icons.map(async (i) => (await fetch(i.src)).ok)), man);
  ok(icone.every(Boolean), 'manifest: tutte le icone esistono');
  const attivo = await q.evaluate(async () => { const r = await navigator.serviceWorker.ready; return !!r.active; });
  ok(attivo, 'service worker attivo');
  await q.reload(); await q.waitForTimeout(300); // la shell entra in cache
  await ctx.setOffline(true);
  await q.reload(); await q.waitForSelector('input', { timeout: 5000 }).catch(() => {});
  ok(await q.locator('button[type=submit]').count() === 1, 'senza rete si apre comunque (shell dalla cache)');
  const solo = await q.evaluate(async () => (await caches.keys()).length === 1 && (await (await caches.open((await caches.keys())[0])).keys()).every((r) => new URL(r.url).origin === location.origin));
  ok(solo, 'in cache solo file dello stesso sito (nessun dato)');
  await ctx.close();
}

// 10. larghezze: nessuno scroll orizzontale, screenshot
for (const [w, h] of [[390, 844], [768, 1024], [1280, 900], [1920, 1080]]) {
  const r = await entra(w, h);
  await r.p.screenshot({ path: `${OUT}centro-${w}.png`, fullPage: w === 390 });
  await r.p.click('.porta >> nth=1'); await r.p.waitForTimeout(450); await r.p.screenshot({ path: `${OUT}stanza-${w}.png` });
  const swS = await r.p.evaluate(() => document.documentElement.scrollWidth);
  ok(swS <= w, `${w}px: stanza senza scroll orizzontale (${swS})`);
  await r.p.keyboard.press('Escape');
  await r.p.click('.kpi >> nth=1'); await r.p.waitForSelector('.drawer'); await r.p.waitForTimeout(500); await r.p.screenshot({ path: `${OUT}pannello-${w}.png` });
  const sw = await r.p.evaluate(() => document.documentElement.scrollWidth);
  ok(sw <= w && r.errori.length === 0, `${w}px: nessuno scroll orizzontale (${sw}) e nessun errore`);
  await r.p.close();
}
await b.close();
console.log(falliti ? `\n${falliti} controlli FALLITI` : '\nTutti i controlli E2E superati');
process.exit(falliti ? 1 : 0);
