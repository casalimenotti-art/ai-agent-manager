// Voce con la Web Speech API del browser, solo se supportata. "In ascolto" solo a microfono davvero aperto.
import { useSyncExternalStore } from 'react';

type Rec = { lang: string; interimResults: boolean; continuous: boolean; start(): void; stop(): void;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onstart: (() => void) | null; onend: (() => void) | null; onerror: ((e: { error: string }) => void) | null };

const W = typeof window !== 'undefined' ? (window as unknown as Record<string, unknown>) : {};
const RecCtor = (W.SpeechRecognition || W.webkitSpeechRecognition) as (new () => Rec) | undefined;
export const supportoAscolto = !!RecCtor;
export const supportoParlato = typeof window !== 'undefined' && 'speechSynthesis' in window;

let stato = { ascolta: false, parla: false, errore: '' as string };
const subs = new Set<() => void>();
const set = (p: Partial<typeof stato>) => { stato = { ...stato, ...p }; subs.forEach((f) => f()); };
let rec: Rec | null = null;

export function ascolta(onTesto: (t: string) => void) {
  if (!RecCtor) return;
  rec = new RecCtor();
  rec.lang = 'it-IT'; rec.interimResults = false; rec.continuous = false;
  rec.onstart = () => set({ ascolta: true, errore: '' });
  rec.onend = () => set({ ascolta: false });
  rec.onerror = (e) => set({ ascolta: false, errore: e.error === 'not-allowed' ? 'Permesso del microfono negato.' : `Errore microfono: ${e.error}` });
  rec.onresult = (e) => { const t = e.results[0]?.[0]?.transcript; if (t) onTesto(t); };
  rec.start();
}
export function smettiDiAscoltare() { rec?.stop(); }

export function parla(testo: string) {
  if (!supportoParlato) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(testo.slice(0, 400));
  u.lang = 'it-IT';
  u.onstart = () => set({ parla: true }); u.onend = () => set({ parla: false }); u.onerror = () => set({ parla: false });
  window.speechSynthesis.speak(u);
}
export function zitto() { if (supportoParlato) window.speechSynthesis.cancel(); set({ parla: false }); }

export function useVoce() {
  return useSyncExternalStore((f) => { subs.add(f); return () => subs.delete(f); }, () => stato, () => stato);
}

/** Orario di silenzio "HH:MM"-"HH:MM" (anche a cavallo della mezzanotte). */
export function inSilenzio(da: string, a: string, ora = new Date()): boolean {
  const m = (s: string) => { const [h, mi] = s.split(':').map(Number); return h * 60 + (mi || 0); };
  const x = ora.getHours() * 60 + ora.getMinutes(); const s = m(da), e = m(a);
  return s <= e ? x >= s && x < e : x >= s || x < e;
}
