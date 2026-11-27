// Ondata 9: microsuoni sintetizzati con WebAudio (nessun file audio). Spenti di default; rispettano l'orario di silenzio.
import { leggiPreferenze } from '../state';
import { inSilenzio } from './voce';

export type Suono = 'notifica' | 'critico' | 'ascolto' | 'fine';
// frequenze (Hz), durata di ogni nota (s), volume: brevi e bassi, per non disturbare
const NOTE: Record<Suono, { f: number[]; d: number; v: number; onda: OscillatorType }> = {
  notifica: { f: [880, 1320], d: 0.07, v: 0.05, onda: 'sine' },
  critico: { f: [440, 330], d: 0.14, v: 0.07, onda: 'triangle' },
  ascolto: { f: [660, 990], d: 0.06, v: 0.04, onda: 'sine' },
  fine: { f: [990, 660], d: 0.06, v: 0.04, onda: 'sine' },
};
let ctx: AudioContext | null = null;
const DEMO = import.meta.env.VITE_DEMO === '1';

export function suona(s: Suono, forza = false): boolean {
  const p = leggiPreferenze();
  if (!forza && (!p.suoni || inSilenzio(p.silenzioDa, p.silenzioA))) return false;
  if (DEMO) ((window as unknown as { __guardianSuoni?: Suono[] }).__guardianSuoni ??= []).push(s); // solo per i test
  const AC = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AC) return false;
  try {
    ctx ??= new AC();
    if (ctx.state === 'suspended') void ctx.resume();
    const n = NOTE[s]; let t = ctx.currentTime + 0.01;
    for (const f of n.f) {
      const o = ctx.createOscillator(); const g = ctx.createGain();
      o.type = n.onda; o.frequency.value = f;
      g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(n.v, t + 0.01); g.gain.exponentialRampToValueAtTime(0.0001, t + n.d);
      o.connect(g).connect(ctx.destination); o.start(t); o.stop(t + n.d + 0.02); t += n.d * 0.9;
    }
    return true;
  } catch { return false; }
}
