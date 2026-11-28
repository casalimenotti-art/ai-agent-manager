// Stato condiviso dell'app: dati, diretta/polling, salute, toast, pannelli (con URL) e conversazione con Guardian.
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import type { DataSource, Diretta, Presente, Presenza } from './data/source';
import { applicaCambio } from './logic/live';
import type { Snapshot, User } from './types';

export const POLLING_MS = 20_000;
const PING_MS = 30_000;

export interface Pannello { p: string; id?: string; filtro?: string }
export interface Messaggio { da: 'user' | 'guardian'; testo: string; fonte?: string }
interface Toast { id: number; testo: string; errore?: boolean }

interface Ctx {
  source: DataSource; user: User; snap: Snapshot | null; errore: string | null; caricato: number | null;
  diretta: Diretta; pingMs: number | null; pingOk: boolean | null; pingAl: number | null;
  ricarica: () => Promise<void>;
  esegui: <T>(fn: () => Promise<T>, ok?: string) => Promise<T | undefined>;
  toasts: Toast[]; toast: (testo: string, errore?: boolean) => void;
  pannello: Pannello | null; traccia: Pannello[]; apri: (p: Pannello) => void; indietro: () => void; chiudi: () => void;
  messaggi: Messaggio[]; aggiungiMessaggio: (m: Messaggio) => void; pensa: boolean; setPensa: (v: boolean) => void;
  paletteAperta: boolean; setPalette: (v: boolean) => void; esci: () => void;
  stanza: string | null; apriStanza: (id: string | null) => void;
  /** Applica subito la modifica a schermo; se il database la rifiuta torna com'era e lo dice. */
  ottimistico: <T>(cambia: (s: Snapshot) => Snapshot, fn: () => Promise<T>, ok?: string) => Promise<T | undefined>;
  presenti: Presente[];
  parete: boolean; setParete: (v: boolean) => void;
}
const C = createContext<Ctx | null>(null);
export const useG = () => { const c = useContext(C); if (!c) throw new Error('useG fuori dal provider'); return c; };

function leggiUrl(): Pannello | null {
  const q = new URLSearchParams(location.search); const p = q.get('p');
  return p ? { p, id: q.get('id') ?? undefined, filtro: q.get('f') ?? undefined } : null;
}
/** Modalità parete (?parete=1): letta all'avvio, mantenuta nell'URL finché non si esce. */
export const PARETE_INIZIALE = typeof location !== 'undefined' && new URLSearchParams(location.search).get('parete') === '1';
function scriviUrl(p: Pannello | null, stanza: string | null, parete = false) {
  const q = new URLSearchParams();
  if (parete) q.set('parete', '1');
  if (stanza) q.set('s', stanza);
  if (p) { q.set('p', p.p); if (p.id) q.set('id', p.id); if (p.filtro) q.set('f', p.filtro); }
  history.replaceState(null, '', `${location.pathname}${q.toString() ? `?${q}` : ''}`);
}

export function GuardianProvider({ source, user, onEsci, children }: { source: DataSource; user: User; onEsci: () => void; children: ReactNode }) {
  const [snap, setSnap] = useState<Snapshot | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [caricato, setCaricato] = useState<number | null>(null);
  const [diretta, setDiretta] = useState<Diretta>('off');
  const [ping, setPing] = useState<{ ms: number | null; ok: boolean | null; al: number | null }>({ ms: null, ok: null, al: null });
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [traccia, setTraccia] = useState<Pannello[]>(() => { const p = leggiUrl(); return p ? [p] : []; });
  const [messaggi, setMessaggi] = useState<Messaggio[]>([]);
  const [pensa, setPensa] = useState(false);
  const [paletteAperta, setPalette] = useState(false);
  const [stanza, apriStanza] = useState<string | null>(() => new URLSearchParams(location.search).get('s'));
  const inCorso = useRef(false);
  const snapRef = useRef<Snapshot | null>(null); snapRef.current = snap;
  const [presenti, setPresenti] = useState<Presente[]>([]);
  const [parete, setParete] = useState(PARETE_INIZIALE);
  const presenza = useRef<Presenza | null>(null);

  const toast = useCallback((testo: string, err = false) => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t.slice(-3), { id, testo, errore: err }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), err ? 7000 : 3500);
  }, []);

  const ricarica = useCallback(async () => {
    if (inCorso.current) return;
    inCorso.current = true;
    try { setSnap(await source.carica(user.id)); setErrore(null); setCaricato(Date.now()); }
    catch (e) { setErrore(e instanceof Error ? e.message : 'Errore di caricamento'); }
    finally { inCorso.current = false; }
  }, [source, user.id]);

  const esegui = useCallback(async <T,>(fn: () => Promise<T>, ok?: string) => {
    try { const r = await fn(); if (ok) toast(ok); await ricarica(); return r; }
    catch (e) { toast(e instanceof Error ? e.message : 'Operazione non riuscita', true); return undefined; }
  }, [ricarica, toast]);

  useEffect(() => { void ricarica(); }, [ricarica]);
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    // Il cambio arrivato in diretta si applica subito; il ricaricamento completo poco dopo riallinea il resto (PC, conteggi).
    const stop = source.ascolta((c) => {
      const n = c && snapRef.current ? applicaCambio(snapRef.current, c, user.id) : null;
      if (n) { snapRef.current = n; setSnap(n); }
      clearTimeout(timer); timer = setTimeout(() => void ricarica(), n ? 2500 : 400);
    }, setDiretta);
    return () => { clearTimeout(timer); stop(); };
  }, [source, ricarica, user.id]);
  useEffect(() => { // polling solo se la diretta non è attiva (e non in demo)
    if (diretta === 'live' || source.modo === 'demo') return;
    const t = setInterval(() => void ricarica(), POLLING_MS);
    return () => clearInterval(t);
  }, [diretta, source.modo, ricarica]);
  useEffect(() => {
    const misura = async () => {
      try { const ms = await source.ping(); setPing({ ms, ok: true, al: Date.now() }); }
      catch { setPing({ ms: null, ok: false, al: Date.now() }); }
    };
    void misura(); const t = setInterval(misura, PING_MS); return () => clearInterval(t);
  }, [source]);

  const ottimistico = useCallback(async <T,>(cambia: (s: Snapshot) => Snapshot, fn: () => Promise<T>, ok?: string) => {
    const prima = snapRef.current;
    if (prima) { snapRef.current = cambia(prima); setSnap(snapRef.current); }
    try { const r = await fn(); if (ok) toast(ok); void ricarica(); return r; }
    catch (e) {
      if (prima) setSnap(prima);
      toast(`${e instanceof Error ? e.message : 'Operazione non riuscita'} (modifica annullata)`, true); void ricarica(); return undefined;
    }
  }, [ricarica, toast]);

  useEffect(() => {
    const p = source.presenza(user, setPresenti); presenza.current = p;
    return () => { p.stop(); presenza.current = null; };
  }, [source, user]);
  useEffect(() => { presenza.current?.segnala(stanza); }, [stanza]);

  const pannello = traccia.length ? traccia[traccia.length - 1] : null;
  useEffect(() => { scriviUrl(pannello, stanza, parete); }, [pannello, stanza, parete]);
  const apri = useCallback((p: Pannello) => setTraccia((t) => {
    const ultimo = t[t.length - 1];
    if (ultimo && ultimo.p === p.p && ultimo.id === p.id && ultimo.filtro === p.filtro) return t;
    return [...t.slice(-5), p];
  }), []);
  const indietro = useCallback(() => setTraccia((t) => t.slice(0, -1)), []);
  const chiudi = useCallback(() => setTraccia([]), []);
  const aggiungiMessaggio = useCallback((m: Messaggio) => setMessaggi((x) => [...x.slice(-40), m]), []);

  const v = useMemo<Ctx>(() => ({
    source, user, snap, errore, caricato, diretta, pingMs: ping.ms, pingOk: ping.ok, pingAl: ping.al, ricarica, esegui, toasts, toast,
    pannello, traccia, apri, indietro, chiudi, messaggi, aggiungiMessaggio, pensa, setPensa, paletteAperta, setPalette, esci: onEsci, stanza, apriStanza, ottimistico, presenti, parete, setParete,
  }), [source, user, snap, errore, caricato, diretta, ping, ricarica, esegui, toasts, toast, pannello, traccia, apri, indietro, chiudi,
    messaggi, aggiungiMessaggio, pensa, paletteAperta, onEsci, stanza, ottimistico, presenti, parete]);
  return <C.Provider value={v}>{children}</C.Provider>;
}

/** Preferenze personali (solo interfaccia): localStorage, con fallback se non disponibile. */
export interface Preferenze { voce: boolean; livello: 'silenzio' | 'critici' | 'importanti' | 'tutti'; silenzioDa: string; silenzioA: string; animazioni: boolean; coloriStanze: 'accesa' | 'soft'; suoni: boolean;
  /** volto di NEXO Sentinel come sfondo: animato (WebGL), immagine ferma o spento */ volto: 'acceso' | 'immagine' | 'spento'; /** sfondo del Centro: Atlas (costellazione) o Volto */ sfondo: 'atlas' | 'volto'; vetro: 'forte' | 'leggero' | 'spento';
  /** tendina dei numeri del Centro: chiusa all'avvio */ numeriAperti: boolean; dettagliAperti: boolean }
const PREF_DEFAULT: Preferenze = { voce: false, livello: 'critici', silenzioDa: '22:00', silenzioA: '08:00', animazioni: true, coloriStanze: 'accesa', suoni: false, volto: 'acceso', sfondo: 'atlas', vetro: 'leggero', numeriAperti: false, dettagliAperti: false };
export function leggiPreferenze(): Preferenze {
  try { return { ...PREF_DEFAULT, ...JSON.parse(localStorage.getItem('guardian.pref') || '{}') }; } catch { return PREF_DEFAULT; }
}
export function salvaPreferenze(p: Preferenze) {
  try { localStorage.setItem('guardian.pref', JSON.stringify(p)); } catch { /* storage non disponibile */ }
  window.dispatchEvent(new CustomEvent('guardian:preferenze'));
}
