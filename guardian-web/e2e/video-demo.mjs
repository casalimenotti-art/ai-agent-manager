// Video dimostrativo della dashboard (build demo su localhost:4173) con didascalie e cursore visibile.
// Uso: VITE_DEMO=1 npx vite build && npm run preview &  poi  node e2e/video-demo.mjs CARTELLA  (esce un .webm; ffmpeg per l'mp4)
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const OUT = process.argv[2];
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, recordVideo: { dir: OUT, size: { width: 1440, height: 900 } } });
const p = await ctx.newPage();
const pausa = (ms) => p.waitForTimeout(ms);
const preparaOverlay = () => p.evaluate(() => {
  if (document.getElementById('demo-cap')) return;
  const st = document.createElement('style');
  st.textContent = `#demo-cap{position:fixed;left:50%;bottom:110px;transform:translateX(-50%);z-index:99999;max-width:900px;padding:14px 22px;border-radius:14px;
    background:rgba(5,9,15,.92);border:1px solid #22d3ee;color:#e8eef6;font:600 22px/1.35 Inter,system-ui,sans-serif;text-align:center;box-shadow:0 10px 40px rgba(0,0,0,.6);transition:opacity .25s}
    #demo-cap small{display:block;font-weight:400;font-size:16px;color:#a8b6c8;margin-top:4px}
    #demo-cur{position:fixed;z-index:100000;width:22px;height:22px;border-radius:50%;border:3px solid #fbbf24;background:rgba(251,191,36,.25);pointer-events:none;transform:translate(-50%,-50%);transition:width .1s,height .1s;left:-50px;top:-50px}
    #demo-cur.giu{width:14px;height:14px;background:#fbbf24}
    #demo-titolo{position:fixed;inset:0;z-index:99998;display:grid;place-items:center;background:#070b12;color:#e8eef6;font:700 46px Inter,system-ui,sans-serif;text-align:center}
    #demo-titolo small{display:block;font-size:22px;font-weight:400;color:#7dd3fc;margin-top:14px}`;
  document.head.appendChild(st);
  const c = document.createElement('div'); c.id = 'demo-cap'; c.style.opacity = '0'; document.body.appendChild(c);
  const k = document.createElement('div'); k.id = 'demo-cur'; document.body.appendChild(k);
  addEventListener('mousemove', (e) => { k.style.left = e.clientX + 'px'; k.style.top = e.clientY + 'px'; }, true);
  addEventListener('mousedown', () => k.classList.add('giu'), true); addEventListener('mouseup', () => k.classList.remove('giu'), true);
});
const dici = async (t, s = '', ms = 2600) => { await preparaOverlay(); await p.evaluate(([t, s]) => { const c = document.getElementById('demo-cap'); c.innerHTML = t + (s ? `<small>${s}</small>` : ''); c.style.opacity = '1'; }, [t, s]); await pausa(Math.round(ms * 0.85)); };
const titolo = async (t, s, ms = 2400) => { await preparaOverlay(); await p.evaluate(([t, s]) => { document.getElementById('demo-cap').style.opacity = '0'; const d = document.createElement('div'); d.id = 'demo-titolo'; d.innerHTML = `<div>${t}<small>${s}</small></div>`; document.body.appendChild(d); }, [t, s]); await pausa(ms); await p.evaluate(() => document.getElementById('demo-titolo')?.remove()); };
let mx = 720, my = 450;
const vai = async (sel) => { const el = p.locator(sel).first(); await el.scrollIntoViewIfNeeded(); const bb = await el.boundingBox(); const x = bb.x + bb.width / 2, y = bb.y + bb.height / 2;
  await p.mouse.move(x, y, { steps: 18 }); mx = x; my = y; await pausa(250); return el; };
const clicca = async (sel, dopo = 700) => { await vai(sel); await p.mouse.down(); await pausa(80); await p.mouse.up(); await p.locator(sel).first().click({ trial: true }).catch(() => {}); await pausa(dopo); };
const clic = async (sel, dopo = 700) => { await vai(sel); await p.locator(sel).first().click(); await pausa(dopo); };
const scegli = async (sel, valore, dopo = 900) => { await vai(sel); await p.locator(sel).first().selectOption(valore); await pausa(dopo); };
const scrivi = async (sel, testo) => { await clic(sel, 200); await p.locator(sel).first().pressSequentially(testo, { delay: 35 }); await pausa(300); };

// --- inizio
await p.goto('http://localhost:4173/?voce=finta');
await titolo('Guardian · NEXO HQ', 'Bozza della dashboard — dati di esempio, nessun dato reale', 3000);
await dici('Si entra con il proprio account', 'Solo i 3 collaboratori di NEXO possono vedere i dati');
await scrivi('input', 'menotti'); await clic('button[type=submit]', 1200);
await dici('Il centro: Guardian e le tre stanze', 'Sviluppo & Siti (Menotti · Claude Code) · Vendite (Niko · Codex) · Amministrazione (Francesco · Codex)', 4200);
await vai('.kpi >> nth=0'); await dici('Numeri dal vivo', 'Agenti al lavoro, task in corso, approvazioni, completati oggi', 3000);
await vai('text=Prossime azioni'); await dici('Prossime azioni', 'Guardian ti dice cosa fare adesso: approvazioni, task bloccati, scadenze', 3000);

// --- gli agenti
await titolo('1. Gli agenti', 'Claude Code di Menotti · Codex di Niko · Codex di Francesco');
await clic('.rail button:has-text("Agenti")', 1000);
await dici('Ogni agente gira sul PC del suo collaboratore', 'Lo stato (al lavoro, inattivo, sconosciuto) arriva dal bridge: niente stati inventati', 4000);
await clic('.drawer .item:has-text("menotti-claude"), .drawer button:has-text("Claude Code")', 1000);
await dici('Claude Code (PC di Menotti)', 'Cosa sta facendo, utilizzo 5h/7g, task assegnati', 3200);
await vai('.drawer select[aria-label="Task da assegnare"]');
await dici('Dare un lavoro a un agente', 'Scegli un task libero e premi Assegna: l\'agente lo prende sul suo PC', 3000);
await scegli('.drawer select[aria-label="Task da assegnare"]', { index: 1 }); await clic('.drawer button:has-text("Assegna")', 1400);
await clic('.drawer button[aria-label="Indietro"]', 900);
await clic('.drawer .item:has-text("amico1-codex"), .drawer button:has-text("amico1")', 1000);
await dici('Codex di Niko (Vendite)', 'Stesso pannello: puoi assegnargli lavoro o vedere cosa fa', 3000);
await clic('.drawer button:has-text("Segna come non disponibile")', 1200);
await dici('Attivare / disattivare un agente', '«Non disponibile» = Guardian non gli suggerisce più lavoro. Si riattiva con un clic', 3600);
await clic('.drawer button:has-text("Segna come disponibile")', 1000);
await clic('.drawer button[aria-label="Indietro"]', 900);
await clic('.drawer .item:has-text("amico2-codex"), .drawer button:has-text("amico2")', 1000);
await dici('Codex di Francesco (Amministrazione)', '«Sconosciuto» finché il suo bridge non manda segnali: lo diciamo, non lo inventiamo', 3400);
await clic('.drawer button[aria-label="Chiudi pannello"]', 600);

// --- scegliere chi lavora su un task
await titolo('2. Scegliere chi fa il lavoro', 'Claude Code, il Codex di Niko o il Codex di Francesco');
await clic('.rail button:has-text("Task")', 900);
await clic('.drawer button:has-text("Nuovo task")', 900);
await scrivi('.drawer .field:has-text("Titolo") input', 'Landing page per il nuovo cliente');
await scegli('.drawer .field:has-text("Azienda") select', { label: 'Siti web' });
await vai('.drawer .field:has-text("Agente") select');
await dici('Qui scegli l\'agente', 'Guardian suggerisce quello libero e adatto; puoi scegliere tu', 2800);
await scegli('.drawer .field:has-text("Agente") select', 'amico1-codex', 700);
await scegli('.drawer .field:has-text("Agente") select', 'amico2-codex', 700);
await scegli('.drawer .field:has-text("Agente") select', 'menotti-claude', 900);
await dici('Scelto: Claude Code', 'Il task arriva nella sua coda; sul PC lo prende con il bridge', 2600);
await clic('.drawer button[type=submit]:has-text("Crea")', 1400);
await clic('.drawer button[aria-label="Chiudi pannello"]', 600);

// --- stanze
await titolo('3. Le stanze', 'Ognuno ha la sua: lavagna, agenti, approvazioni');
await clic('.porta:has-text("Sviluppo")', 1200);
await dici('Stanza Sviluppo & Siti', 'Lavagna dei task: si trascina o si usa «Sposta in…»', 3000);
const primo = p.locator('[data-colonna="coda"] [data-task] select').first();
if (await primo.count()) { await vai('[data-colonna="coda"] [data-task] select'); await primo.selectOption({ label: 'In corso' }).catch(() => {}); await pausa(1300); }
await p.keyboard.press('Escape'); await pausa(600);
await clic('.porta:has-text("Vendite")', 1200);
await vai('.pipeline'); await dici('Stanza Vendite (Niko)', 'Pipeline in 6 fasi, senza telefoni né email dei clienti', 3400);
await scegli('[data-vendita="4"] select', 'vinto', 1200);
await dici('Una trattativa diventa «Vinto»', 'Guardian non contatta nessuno: le bozze le invia una persona', 2800);
await p.keyboard.press('Escape'); await pausa(500);
await clic('.porta:has-text("Amministrazione")', 1200);
await vai('[aria-label="Scadenze (30 giorni)"]'); await dici('Stanza Amministrazione (Francesco)', 'Scadenze (rosse se passate) e costi del mese, sempre con la fonte', 3600);
await vai('[aria-label="Costi"]'); await pausa(1500);
await p.keyboard.press('Escape'); await pausa(600);

// --- statistiche e mappa
await titolo('4. Statistiche e mappa', 'Solo numeri calcolati dai dati, con la fonte');
await clic('.rail button:has-text("Statistiche")', 1500);
await dici('Statistiche', 'Attività per giorno, carico per agente, tasso di completamento', 3600);
await p.locator('.drawer .body').evaluate((e) => e.scrollBy({ top: 500, behavior: 'smooth' })); await pausa(1800);
await clic('.rail button:has-text("Mappa")', 1500);
await dici('Mappa operativa', 'Persone → agenti → task → stanze. Pulsa ciò che si è appena mosso', 3800);
await clic('.drawer button[aria-label="Chiudi pannello"]', 500);

// --- approvazioni
await titolo('5. Approvazioni', 'Le azioni importanti le decide una persona');
await clic('.rail button:has-text("Approva")', 1000);
await clic('.drawer .item >> nth=0', 1000);
await dici('Invio di un preventivo: serve il tuo ok', 'Motivo, impatto, dati coinvolti. Guardian registra la decisione, non invia', 3400);
await clic('.drawer button:has-text("Approva")', 1400);
await clic('.drawer button[aria-label="Chiudi pannello"]', 500);

// --- parlare con Guardian
await titolo('6. Parlare con Guardian', 'Per scritto o a voce');
await scrivi('.dock input', 'Quanti agenti sono attivi?'); await p.keyboard.press('Enter'); await pausa(600);
await clic('.dock button:has-text("Conversazione (")', 600).catch(() => {});
await dici('Risponde dai dati, con la fonte', 'Funziona anche senza AI; con il «cervello» sul PC risponde a tutto', 3200);
await scrivi('.dock input', 'quanto spendiamo questo mese?'); await p.keyboard.press('Enter'); await pausa(2200);
await clic('.dock button:has-text("Nascondi")', 500).catch(() => {});
await clic('.rail button:has-text("Centro")', 600);
await clic('.conv-btn', 900);
await dici('Modalità conversazione', 'Parli e Guardian risponde a voce. In questo video la voce è simulata', 2200);
await p.evaluate(() => window.__guardianDici?.('Cosa mi consigli di fare?')); await pausa(3500);
await p.keyboard.press('Escape'); await pausa(600);

// --- extra
await titolo('7. Extra', 'Ricerca veloce, schermo da parete, app sul telefono');
await p.keyboard.press('Control+k'); await pausa(500); await p.keyboard.type('vend', { delay: 90 }); await pausa(1500);
await dici('Ctrl+K: cerca e apri tutto', 'Stanze, agenti, task, aziende', 2400);
await p.keyboard.press('Escape'); await pausa(400);
await p.goto('http://localhost:4173/?parete=1'); await p.fill('input', 'menotti'); await p.click('button[type=submit]'); await p.waitForSelector('.parete'); await pausa(500);
await dici('Modalità parete per lo schermo in ufficio', 'Scritte grandi, solo lettura, si aggiorna da sola', 3800);
await titolo('Guardian · NEXO HQ', 'Bozza: dati di esempio. Online servono Supabase e Cloudflare Pages (guida nel repo)', 3200);
await ctx.close(); await b.close();
