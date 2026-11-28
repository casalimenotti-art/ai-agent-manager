// Atlas: lo sfondo "cervello che lavora". Funzioni pure: dai dati veri (stanze, agenti, task, eventi) costruiscono
// nodi e link (nucleo Guardian > stanze > agenti > task), poi li dispongono con una piccola simulazione a forze
// scritta a mano e deterministica (stesso seed = stesso disegno). Nessun dato inventato.
import type { Agent, Snapshot, Stanza, Task } from '../types';
import { TASK_TERMINALI } from '../types';
import { AGENTI_AL_LAVORO, etaSecondi, statoAgente } from './status';
import { stanzaDiTask } from './stanze';

export type TipoNodo = 'nucleo' | 'stanza' | 'agente' | 'task' | 'evento';
/** attivo = lavora; fermo = tenue; bloccato = errore o ostacolo; ok = serve il via libera di una persona. */
export type StatoAtlas = 'attivo' | 'fermo' | 'bloccato' | 'ok';

export interface Nodo {
  id: string; tipo: TipoNodo; etichetta: string; stato: StatoAtlas;
  /** id della stanza di appartenenza (null per il nucleo e per ciò che non ha stanza) */
  stanza: string | null; colore: string; raggio: number; alpha: number;
  /** posizione normalizzata nel quadrato [-1, 1]; vale 0 prima del layout */
  x: number; y: number;
  /** solo agenti: cosa sta facendo (task corrente o ultimo evento), al massimo 40 caratteri */
  attivita?: string;
  /** solo agenti: serve il via libera di una persona (stato "ok" o approvazione in attesa) */
  okInAttesa?: boolean;
}
export interface Link { da: string; a: string; stato: StatoAtlas; stanza: string | null }
export interface Grafo { nodi: Nodo[]; link: Link[] }
export interface OpzioniGrafo { ora?: number; telefono?: boolean; maxTask?: number; maxEventi?: number }

export const COLORI_ATLAS = {
  nucleo: '#bfe6ff', // azzurro ghiaccio
  sviluppo: '#3fd0e8', // ciano
  vendite: '#f5a524', // ambra
  amministrazione: '#b79cff', // lilla
  fermo: '#8c97a8', // grigio tenue
  bloccato: '#ff6b4a', // rosso-arancio
  ok: '#ff7ac0', // rosa che chiama
  extra: ['#5eead4', '#fb7185', '#a3e635', '#7dd3fc'], // eventuali stanze in più
} as const;

/** Colore di una stanza: quelle note hanno il loro, le altre ne ricevono uno stabile in base all'ordine. */
export function coloreStanzaAtlas(st: Pick<Stanza, 'id' | 'ordine'>): string {
  if (st.id === 'sviluppo') return COLORI_ATLAS.sviluppo;
  if (st.id === 'vendite') return COLORI_ATLAS.vendite;
  if (st.id === 'amministrazione') return COLORI_ATLAS.amministrazione;
  return COLORI_ATLAS.extra[Math.abs(Math.round(st.ordine)) % COLORI_ATLAS.extra.length];
}

export function statoAgenteAtlas(a: Agent, ora?: number): StatoAtlas {
  const s = statoAgente(a, ora);
  if (s === 'needs_approval') return 'ok';
  if (s === 'error') return 'bloccato';
  return AGENTI_AL_LAVORO.includes(s) ? 'attivo' : 'fermo';
}
export function statoTaskAtlas(t: Pick<Task, 'stato'>): StatoAtlas {
  if (t.stato === 'running') return 'attivo';
  if (t.stato === 'blocked' || t.stato === 'failed') return 'bloccato';
  if (t.stato === 'needs_approval') return 'ok';
  return 'fermo';
}

export interface Stile { colore: string; alpha: number; anello: boolean; fiore: boolean; lampeggia: boolean }
/** Mappatura stato > stile: il colore della stanza vale solo per ciò che lavora. */
export function stileStato(stato: StatoAtlas, colorStanza: string): Stile {
  switch (stato) {
    case 'attivo': return { colore: colorStanza, alpha: 1, anello: false, fiore: true, lampeggia: false };
    case 'bloccato': return { colore: COLORI_ATLAS.bloccato, alpha: 0.95, anello: true, fiore: false, lampeggia: true };
    case 'ok': return { colore: COLORI_ATLAS.ok, alpha: 1, anello: true, fiore: false, lampeggia: true };
    default: return { colore: COLORI_ATLAS.fermo, alpha: 0.45, anello: false, fiore: false, lampeggia: false };
  }
}

const PESO: Record<StatoAtlas, number> = { bloccato: 0, ok: 1, attivo: 2, fermo: 3 };
const RAGGIO = { nucleo: 14, stanza: 7, agenteAttivo: 6, agente: 4.2, task: 1.8, evento: 1.3 };
const BREVE = (t: string, n = 40) => (t.length > n ? `${t.slice(0, n - 1)}…` : t);

/** Cosa sta facendo un agente: titolo del task corrente, altrimenti messaggio dell'ultimo evento. Massimo 40 caratteri, con ellissi. */
export function attivitaAgente(s: Snapshot, a: Agent): string | undefined {
  const t = a.current_task_id != null ? s.tasks.find((x) => x.id === a.current_task_id) : undefined;
  if (t?.titolo) return BREVE(t.titolo);
  let ultimo: { timestamp: string; message: string } | undefined;
  for (const e of s.events) if (e.agent_id === a.id && e.message && (!ultimo || e.timestamp > ultimo.timestamp)) ultimo = e;
  return ultimo ? BREVE(ultimo.message) : undefined;
}

export function costruisciGrafo(s: Snapshot, o: OpzioniGrafo = {}): Grafo {
  const ora = o.ora ?? Date.now();
  const maxTask = o.maxTask ?? 120; const maxEventi = o.maxEventi ?? 24;
  const nodi: Nodo[] = []; const link: Link[] = [];
  const nodo = (n: Omit<Nodo, 'x' | 'y'>) => nodi.push({ ...n, x: 0, y: 0 });
  nodo({ id: 'nucleo', tipo: 'nucleo', etichetta: 'Guardian', stato: 'attivo', stanza: null, colore: COLORI_ATLAS.nucleo, raggio: RAGGIO.nucleo, alpha: 1 });

  const stanze = [...s.stanze].filter((st) => st.attiva).sort((a, b) => a.ordine - b.ordine);
  const colore = new Map(stanze.map((st) => [st.id, coloreStanzaAtlas(st)]));
  for (const st of stanze) {
    nodo({ id: `s:${st.id}`, tipo: 'stanza', etichetta: st.nome, stato: 'attivo', stanza: st.id, colore: colore.get(st.id)!, raggio: RAGGIO.stanza, alpha: 1 });
    link.push({ da: 'nucleo', a: `s:${st.id}`, stato: 'fermo', stanza: st.id });
  }

  const agenteStanza = (a: Agent) => stanze.find((st) => st.responsabile === a.user_id)?.id ?? null;
  const idAgenti = new Set<string>();
  for (const a of s.agents) {
    const st = statoAgenteAtlas(a, ora); const sid = agenteStanza(a); const stile = stileStato(st, sid ? colore.get(sid)! : COLORI_ATLAS.nucleo);
    idAgenti.add(a.id);
    const okInAttesa = st === 'ok' || s.approvals.some((x) => x.status === 'richiesta' && x.agent_id === a.id);
    nodo({ id: `a:${a.id}`, tipo: 'agente', etichetta: a.nome, stato: st, stanza: sid, colore: stile.colore, alpha: stile.alpha,
      raggio: st === 'attivo' ? RAGGIO.agenteAttivo : RAGGIO.agente, okInAttesa, attivita: st === 'attivo' ? attivitaAgente(s, a) : undefined });
    link.push({ da: sid ? `s:${sid}` : 'nucleo', a: `a:${a.id}`, stato: st, stanza: sid });
  }

  if (!o.telefono) {
    const aperti = s.tasks.filter((t) => !TASK_TERMINALI.includes(t.stato))
      .sort((a, b) => PESO[statoTaskAtlas(a)] - PESO[statoTaskAtlas(b)] || b.id - a.id).slice(0, maxTask);
    for (const t of aperti) {
      const st = statoTaskAtlas(t); const sid = stanzaDiTask(t, s);
      const padre = t.assigned_agent_id && idAgenti.has(t.assigned_agent_id) ? `a:${t.assigned_agent_id}` : sid && colore.has(sid) ? `s:${sid}` : 'nucleo';
      const stile = stileStato(st, sid && colore.get(sid) ? colore.get(sid)! : COLORI_ATLAS.nucleo);
      nodo({ id: `t:${t.id}`, tipo: 'task', etichetta: BREVE(t.titolo), stato: st, stanza: sid, colore: stile.colore, alpha: stile.alpha, raggio: RAGGIO.task });
      link.push({ da: padre, a: `t:${t.id}`, stato: st, stanza: sid });
    }
    // eventi delle ultime 24 ore che hanno un agente noto: puntini minuscoli attorno a lui
    const eventi = s.events.filter((e) => e.agent_id && idAgenti.has(e.agent_id) && (etaSecondi(e.timestamp, ora) ?? Infinity) <= 86400).slice(0, maxEventi);
    for (const e of eventi) {
      const ag = nodi.find((n) => n.id === `a:${e.agent_id}`)!;
      nodo({ id: `e:${e.id}`, tipo: 'evento', etichetta: BREVE(e.message), stato: 'fermo', stanza: ag.stanza, colore: ag.colore, alpha: 0.5, raggio: RAGGIO.evento });
      link.push({ da: ag.id, a: `e:${e.id}`, stato: 'fermo', stanza: ag.stanza });
    }
  }
  return { nodi, link };
}

/** Numeri casuali con seed (mulberry32): stesso seed, stessa sequenza. */
export function casuale(seed: number) {
  let a = seed >>> 0;
  return () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}

export const RAGGIO_STANZE = 0.6;
const LUNGHEZZA: Record<TipoNodo, number> = { nucleo: 0, stanza: RAGGIO_STANZE, agente: 0.25, task: 0.1, evento: 0.07 };

/** Simulazione a forze: repulsione tra i nodi vicini, molle lungo i link; nucleo e stanze restano ai loro posti. Non modifica l'input. */
export function disponi(g: Grafo, o: { seed?: number; iterazioni?: number } = {}): Grafo {
  const rnd = casuale(o.seed ?? 7); const N = o.iterazioni ?? 140;
  const nodi = g.nodi.map((n) => ({ ...n })); const per = new Map(nodi.map((n) => [n.id, n]));
  const stanze = nodi.filter((n) => n.tipo === 'stanza'); const fissi = new Set<string>(['nucleo']);
  stanze.forEach((n, i) => {
    const ang = -Math.PI / 2 + (i * 2 * Math.PI) / stanze.length;
    n.x = Math.cos(ang) * RAGGIO_STANZE; n.y = Math.sin(ang) * RAGGIO_STANZE; fissi.add(n.id);
  });
  const nucleo = per.get('nucleo'); if (nucleo) { nucleo.x = 0; nucleo.y = 0; }
  const padre = new Map(g.link.map((l) => [l.a, l.da]));
  // partenza: vicino al padre, con un po' di scarto seedato (l'ordine dei nodi è quello dei dati, quindi stabile)
  for (const n of nodi) {
    if (fissi.has(n.id)) continue;
    const p = per.get(padre.get(n.id) ?? 'nucleo') ?? nucleo; const ang = rnd() * Math.PI * 2; const d = 0.05 + rnd() * 0.12;
    n.x = (p?.x ?? 0) + Math.cos(ang) * d; n.y = (p?.y ?? 0) + Math.sin(ang) * d;
  }
  const vx = new Map(nodi.map((n) => [n.id, 0])); const vy = new Map(nodi.map((n) => [n.id, 0]));
  for (let it = 0; it < N; it++) {
    const forza = 1 - it / N;
    for (let i = 0; i < nodi.length; i++) for (let j = i + 1; j < nodi.length; j++) {
      const a = nodi[i]; const b = nodi[j];
      let dx = a.x - b.x; let dy = a.y - b.y; const d2 = dx * dx + dy * dy + 1e-4;
      if (d2 > 0.35) continue;
      const peso = ((a.tipo === 'agente' || b.tipo === 'agente' ? 0.0016 : 0.0007) * forza) / d2; const d = Math.sqrt(d2);
      dx = (dx / d) * Math.min(peso, 0.02); dy = (dy / d) * Math.min(peso, 0.02);
      vx.set(a.id, vx.get(a.id)! + dx); vy.set(a.id, vy.get(a.id)! + dy); vx.set(b.id, vx.get(b.id)! - dx); vy.set(b.id, vy.get(b.id)! - dy);
    }
    for (const l of g.link) {
      const a = per.get(l.da)!; const b = per.get(l.a)!; const dx = b.x - a.x; const dy = b.y - a.y; const d = Math.sqrt(dx * dx + dy * dy) + 1e-6;
      const L = b.tipo === 'agente' && a.tipo === 'nucleo' ? 0.4 : b.tipo === 'task' && a.tipo === 'stanza' ? 0.28 : LUNGHEZZA[b.tipo];
      const f = (d - L) * 0.06; const fx = (dx / d) * f; const fy = (dy / d) * f;
      vx.set(b.id, vx.get(b.id)! - fx); vy.set(b.id, vy.get(b.id)! - fy); vx.set(a.id, vx.get(a.id)! + fx); vy.set(a.id, vy.get(a.id)! + fy);
    }
    for (const n of nodi) {
      if (fissi.has(n.id)) continue;
      n.x = Math.max(-0.97, Math.min(0.97, n.x + vx.get(n.id)! * 0.6)); n.y = Math.max(-0.97, Math.min(0.97, n.y + vy.get(n.id)! * 0.6));
      vx.set(n.id, vx.get(n.id)! * 0.5); vy.set(n.id, vy.get(n.id)! * 0.5);
    }
    for (const id of fissi) { vx.set(id, 0); vy.set(id, 0); }
  }
  return { nodi, link: g.link };
}

/** Riepilogo per chi non vede il disegno (lettori di schermo). */
export function riepilogoAtlas(s: Snapshot, ora: number = Date.now()): string {
  if (s.agents.length === 0) return 'Nessun agente collegato. Guardian e le stanze sono vuoti.';
  const al = s.agents.filter((a) => statoAgenteAtlas(a, ora) === 'attivo');
  const ok = s.agents.filter((a) => statoAgenteAtlas(a, ora) === 'ok').length; const bl = s.agents.filter((a) => statoAgenteAtlas(a, ora) === 'bloccato').length;
  const testo = al.length === 0 ? 'Nessun agente al lavoro' : `${al.length} ${al.length === 1 ? 'agente al lavoro' : 'agenti al lavoro'}: ${al.map((a) => a.nome).join(', ')}`;
  return `${testo} su ${s.agents.length}.${ok ? ` ${ok} in attesa del tuo OK.` : ''}${bl ? ` ${bl} bloccati.` : ''}`;
}

// ---------- ondata 2: vita (funzioni pure, il disegno sta in ui/Atlas.tsx) ----------
export const FPS_MAX = 30;
/** Si ridisegna solo se è passato almeno 1/fps secondi dall'ultimo disegno (tolleranza 1 ms per i salti di rAF). */
export function devoDisegnare(ultimoMs: number | null, oraMs: number, fps: number = FPS_MAX): boolean {
  return ultimoMs === null || oraMs - ultimoMs >= 1000 / fps - 1;
}
/** Animare solo se la scheda è visibile e la persona non ha chiesto meno movimento. */
export function possoAnimare(nascosta: boolean, ridotto: boolean): boolean { return !nascosta && !ridotto; }

export type Pt = readonly [number, number];
/** Punto a frazione u (0..1) lungo una spezzata. */
export function puntoSulPercorso(pts: readonly Pt[], u: number): Pt {
  if (pts.length === 0) return [0, 0];
  if (pts.length === 1) return pts[0];
  const seg: number[] = []; let tot = 0;
  for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); tot += d; }
  let r = Math.max(0, Math.min(1, u)) * tot;
  for (let i = 0; i < seg.length; i++) {
    if (r <= seg[i] || i === seg.length - 1) { const f = seg[i] === 0 ? 0 : Math.min(1, r / seg[i]); return [pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f]; }
    r -= seg[i];
  }
  return pts[pts.length - 1];
}
/** Posizione 0..1 di un impulso: ciclico, ogni agente con la propria fase. */
export function faseImpulso(tMs: number, indice: number, durataMs = 2600): number {
  return (((tMs / durataMs + indice * 0.37) % 1) + 1) % 1;
}
/** Respiro del nucleo: 0..1 sinusoidale. Più rapido e ampio mentre il cervello risponde. */
export function respiro(tMs: number, rispondendo: boolean): { fase: number; ampiezza: number } {
  const periodo = rispondendo ? 1400 : 4200;
  return { fase: 0.5 + 0.5 * Math.sin((tMs / periodo) * Math.PI * 2), ampiezza: rispondendo ? 0.22 : 0.07 };
}
/** Lampeggio on/off morbido 0..1 (anello bloccato). */
export function lampeggio(tMs: number, periodoMs = 1200): number { return 0.5 + 0.5 * Math.sin((tMs / periodoMs) * Math.PI * 2); }

export interface Rett { x: number; y: number; w: number; h: number }
/**
 * Zona libera in cui disegnare l'Atlas: il più grande dei rettangoli attorno al pannello (destra, sinistra, sopra, sotto)
 * dentro i limiti dati. Senza pannello vale tutta l'area. Così nessun nodo finisce sotto il pannello del Centro.
 */
export function zonaLibera(area: Rett, pannello: Rett | null): Rett {
  if (!pannello) return area;
  const a1 = { x: area.x, y: area.y, r: area.x + area.w, b: area.y + area.h };
  const p = { x: Math.max(a1.x, pannello.x), y: Math.max(a1.y, pannello.y), r: Math.min(a1.r, pannello.x + pannello.w), b: Math.min(a1.b, pannello.y + pannello.h) };
  if (p.r <= p.x || p.b <= p.y) return area; // il pannello non tocca l'area
  const cand: Rett[] = [
    { x: p.r, y: a1.y, w: a1.r - p.r, h: area.h }, { x: a1.x, y: a1.y, w: p.x - a1.x, h: area.h },
    { x: a1.x, y: a1.y, w: area.w, h: p.y - a1.y }, { x: a1.x, y: p.b, w: area.w, h: a1.b - p.b },
  ].filter((r) => r.w > 0 && r.h > 0);
  if (cand.length === 0) return area;
  return cand.reduce((m, r) => (r.w * r.h > m.w * m.h ? r : m));
}
