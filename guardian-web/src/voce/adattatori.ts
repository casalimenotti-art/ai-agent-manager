// Adattatori della conversazione: ascolto (trascrittori), parlato (TTS) e livello del microfono.
// Livello A (locale, privato) arriva con il bridge (ondata 3); livello B = Web Speech del browser; "finto" solo per i test in demo.
import { rms, Vad } from './vad';
import { ricampiona, unisci, wav16 } from './wav';

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

/** Livello A: trascrizione sul PC con il servizio del bridge (sherpa-onnx + Parakeet). L'audio non lascia il computer. */
export class LocaleTrascrittore implements Trascrittore {
  readonly nome = 'Ascolto locale (sherpa-onnx)'; readonly privato = true;
  static url = (import.meta.env.VITE_GUARDIAN_VOCE_URL as string | undefined) || 'http://127.0.0.1:8765';
  private ctx: AudioContext | null = null; private stream: MediaStream | null = null; private nodo: ScriptProcessorNode | null = null;
  private inPausa = false; private vad = new Vad(); private preRoll: Float32Array[] = []; private frase: Float32Array[] = [];
  static async disponibile(): Promise<boolean> {
    try {
      const c = new AbortController(); const t = setTimeout(() => c.abort(), 600);
      const r = await fetch(`${LocaleTrascrittore.url}/stato`, { signal: c.signal }); clearTimeout(t);
      return !!(await r.json()).pronto;
    } catch { return false; }
  }
  async avvia(cb: Parameters<Trascrittore['avvia']>[0]) {
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } });
    this.ctx = new AudioContext(); const sr = this.ctx.sampleRate;
    this.nodo = this.ctx.createScriptProcessor(4096, 1, 1);
    this.nodo.onaudioprocess = (e) => {
      if (this.inPausa) return;
      const x = new Float32Array(e.inputBuffer.getChannelData(0));
      const ev = this.vad.passo(rms(x), performance.now());
      if (ev === 'inizio') { this.frase = [...this.preRoll]; }
      if (this.vad.attivo || ev === 'fine') this.frase.push(x);
      this.preRoll = [...this.preRoll.slice(-3), x]; // ~300 ms prima della voce
      if (ev === 'fine') { const audio = unisci(this.frase); this.frase = []; void this.invia(audio, sr, cb); }
    };
    this.ctx.createMediaStreamSource(this.stream).connect(this.nodo); this.nodo.connect(this.ctx.destination);
  }
  private async invia(audio: Float32Array, sr: number, cb: Parameters<Trascrittore['avvia']>[0]) {
    cb.parziale('…');
    try {
      const r = await fetch(`${LocaleTrascrittore.url}/trascrivi`, { method: 'POST', headers: { 'Content-Type': 'audio/wav' }, body: wav16(ricampiona(audio, sr)) });
      const d = await r.json();
      if (!r.ok) { cb.errore(d.errore || 'Errore della voce locale'); return; }
      if (d.testo) cb.finale(d.testo); else cb.parziale('');
    } catch { cb.errore('Servizio vocale locale non raggiungibile.'); }
  }
  pausa() { this.inPausa = true; this.frase = []; } riprendi() { this.inPausa = false; }
  ferma() { this.nodo?.disconnect(); this.stream?.getTracks().forEach((t) => t.stop()); void this.ctx?.close(); this.ctx = null; this.nodo = null; this.stream = null; }
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
