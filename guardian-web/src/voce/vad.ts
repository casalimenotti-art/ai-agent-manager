// Logica pura della conversazione (testata): rilevamento della voce (VAD), frasi, comandi. Parametri da mic_continuo.
export const VAD = { soglia: 0.02, fineFraseMs: 1000, minParlatoMs: 400, maxParlatoMs: 25000, sogliaBargeIn: 0.06, bargeInMs: 250 };

export type EventoVad = 'inizio' | 'fine' | null;

/** Riceve livelli RMS (0..1) nel tempo e segnala inizio e fine di una frase. */
export class Vad {
  private parlando = false; private inizio = 0; private ultimaVoce = 0;
  constructor(private p = VAD) {}
  get attivo() { return this.parlando; }
  passo(livello: number, t: number): EventoVad {
    if (livello >= this.p.soglia) {
      this.ultimaVoce = t;
      if (!this.parlando) { this.parlando = true; this.inizio = t; return 'inizio'; }
    }
    if (this.parlando && (t - this.ultimaVoce > this.p.fineFraseMs || t - this.inizio > this.p.maxParlatoMs)) {
      this.parlando = false;
      return this.ultimaVoce - this.inizio >= this.p.minParlatoMs ? 'fine' : null; // troppo breve: rumore
    }
    return null;
  }
}

/** Barge-in: l'utente parla sopra Guardian (livello alto per un tempo minimo). */
export class BargeIn {
  private da = 0;
  constructor(private p = VAD) {}
  passo(livello: number, t: number): boolean {
    if (livello < this.p.sogliaBargeIn) { this.da = 0; return false; }
    if (!this.da) this.da = t;
    return t - this.da >= this.p.bargeInMs;
  }
  azzera() { this.da = 0; }
}

/** Divide una risposta in frasi da pronunciare una alla volta (la prima parte subito). */
export function dividiFrasi(testo: string): string[] {
  return (testo.replace(/\s+/g, ' ').match(/[^.!?\n]+[.!?]+|[^.!?\n]+$/g) ?? []).map((f) => f.trim()).filter((f) => f.length > 1);
}

/** Testo adatto alla voce: niente elenchi numerati lunghi, al massimo `max` frasi. */
export function perLaVoce(testo: string, max = 3): string {
  const frasi = dividiFrasi(testo.replace(/^\s*\d+\.\s*/gm, ''));
  return frasi.length > max ? `${frasi.slice(0, max).join(' ')} Vuoi che continui?` : frasi.join(' ');
}

export type ComandoConversazione = 'termina' | 'silenzio' | null;
export function comandoConversazione(testo: string): ComandoConversazione {
  const q = testo.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z\s]/g, ' ').trim();
  if (/^(guardian\s+)?(basta|stop|fine conversazione|chiudi conversazione|termina)(\s+cosi)?$/.test(q)) return 'termina';
  if (/^(guardian\s+)?(silenzio|zitto|stai zitto)$/.test(q)) return 'silenzio';
  return null;
}

/** RMS di un buffer audio (Float32 da AnalyserNode). */
export function rms(buf: ArrayLike<number>): number {
  let s = 0; for (let i = 0; i < buf.length; i++) s += buf[i] * buf[i];
  return buf.length ? Math.sqrt(s / buf.length) : 0;
}
