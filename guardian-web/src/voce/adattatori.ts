// Adattatori della conversazione: ascolto (trascrittori), parlato (TTS) e livello del microfono.
// Livello A (locale, privato) arriva con il bridge (ondata 3); livello B = Web Speech del browser; "finto" solo per i test in demo.
import { rms } from './vad';

export interface Trascrittore {
  readonly nome: string; readonly privato: boolean;
  avvia(cb: { parziale: (t: string) => void; finale: (t: string) => void; errore: (m: string) => void }): Promise<void>;
  ferma(): void;
  /** Smette di ascoltare mentre Guardian parla (non si sente da solo); il barge-in usa il livello del microfono. */
  pausa(): void; riprendi(): void;
}
export interface Parlatore { parla(frase: string): Promise<void>; zitto(): void; readonly nome: string }

type Rec = { lang: string; interimResults: boolean; continuous: boolean; start(): void; stop(): void; abort(): void;
  onresult: ((e: { resultIndex: number; results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }> }) => void) | null;
  onend: (() => void) | null; onerror: ((e: { error: string }) => void) | null };
const W = typeof window !== 'undefined' ? (window as unknown as Record<string, unknown>) : {};
const RecCtor = (W.SpeechRecognition || W.webkitSpeechRecognition) as (new () => Rec) | undefined;

export class WebSpeechTrascrittore implements Trascrittore {
  readonly nome = 'Ascolto del browser'; readonly privato = false; // Chrome invia l'audio ai server di Google
  private rec: Rec | null = null; private attivo = false; private inPausa = false;
  static disponibile() { return !!RecCtor; }
  async avvia(cb: Parameters<Trascrittore['avvia']>[0]) {
    if (!RecCtor) throw new Error('Riconoscimento vocale non supportato da questo browser.');
    this.attivo = true;
    const r = new RecCtor(); this.rec = r;
    r.lang = 'it-IT'; r.interimResults = true; r.continuous = true;
    r.onresult = (e) => {
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const x = e.results[i]; const t = x[0].transcript.trim();
        if (t) (x.isFinal ? cb.finale : cb.parziale)(t);
      }
    };
    r.onerror = (e) => { if (e.error === 'not-allowed') { this.attivo = false; cb.errore('Permesso del microfono negato.'); }
      else if (e.error !== 'no-speech' && e.error !== 'aborted') cb.errore(`Errore di ascolto: ${e.error}`); };
    r.onend = () => { if (this.attivo && !this.inPausa) { try { r.start(); } catch { /* già avviato */ } } }; // Chrome si ferma da solo: riparte
    r.start();
  }
  pausa() { this.inPausa = true; try { this.rec?.abort(); } catch { /* */ } }
  riprendi() { this.inPausa = false; if (this.attivo) { try { this.rec?.start(); } catch { /* */ } } }
  ferma() { this.attivo = false; try { this.rec?.abort(); } catch { /* */ } this.rec = null; }
}

export class ParlatoreWeb implements Parlatore {
  readonly nome = 'Voce del sistema';
  static disponibile() { return typeof window !== 'undefined' && 'speechSynthesis' in window; }
  private voce(): SpeechSynthesisVoice | undefined {
    const v = window.speechSynthesis.getVoices().filter((x) => x.lang.toLowerCase().startsWith('it'));
    // preferisci una voce locale (non esce dal PC), es. «Microsoft Elsa»
    return v.find((x) => x.localService && /elsa|isabella|alice|federica/i.test(x.name)) ?? v.find((x) => x.localService) ?? v[0];
  }
  parla(frase: string) {
    return new Promise<void>((ok) => {
      const u = new SpeechSynthesisUtterance(frase); u.lang = 'it-IT'; const v = this.voce(); if (v) u.voice = v;
      u.onend = () => ok(); u.onerror = () => ok();
      window.speechSynthesis.speak(u);
    });
  }
  zitto() { window.speechSynthesis.cancel(); }
}

/** Livello reale del microfono (AnalyserNode): per i sottotitoli, il nucleo e il barge-in. Mai simulato nell'app. */
export class Microfono {
  private ctx: AudioContext | null = null; private stream: MediaStream | null = null; private an: AnalyserNode | null = null;
  private buf = new Float32Array(1024);
  async apri() {
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } });
    this.ctx = new AudioContext(); this.an = this.ctx.createAnalyser(); this.an.fftSize = 1024;
    this.ctx.createMediaStreamSource(this.stream).connect(this.an);
  }
  livello() { if (!this.an) return 0; this.an.getFloatTimeDomainData(this.buf); return rms(this.buf); }
  chiudi() { this.stream?.getTracks().forEach((t) => t.stop()); void this.ctx?.close(); this.ctx = null; this.an = null; this.stream = null; }
}

// ---------- solo test (VITE_DEMO=1 e ?voce=finta): il "microfono" è simulato dal test, mai nell'app reale ----------
type Finti = { __guardianDici?: (t: string) => void; __guardianParziale?: (t: string) => void; __guardianLivello?: number; __guardianParlato?: string[] };
const F = (typeof window !== 'undefined' ? window : {}) as Finti;
// letto UNA volta al caricamento (l'app poi riscrive l'URL); solo nella build demo
const FINTA = import.meta.env.VITE_DEMO === '1' && typeof location !== 'undefined' && new URLSearchParams(location.search).get('voce') === 'finta';
export const vocaFintaAttiva = () => FINTA;

export class FintoTrascrittore implements Trascrittore {
  readonly nome = 'Ascolto finto (test)'; readonly privato = true; private inPausa = false;
  async avvia(cb: Parameters<Trascrittore['avvia']>[0]) {
    F.__guardianDici = (t) => { if (!this.inPausa) cb.finale(t); };
    F.__guardianParziale = (t) => cb.parziale(t);
  }
  pausa() { this.inPausa = true; } riprendi() { this.inPausa = false; }
  ferma() { F.__guardianDici = undefined; }
}
export class FintoParlatore implements Parlatore {
  readonly nome = 'Voce finta (test)'; private stop: (() => void) | null = null;
  parla(frase: string) { (F.__guardianParlato ??= []).push(frase);
    return new Promise<void>((ok) => { const t = setTimeout(ok, 400); this.stop = () => { clearTimeout(t); ok(); }; }); }
  zitto() { this.stop?.(); }
}
export class FintoMicrofono { async apri() {} livello() { return F.__guardianLivello ?? 0; } chiudi() {} }
