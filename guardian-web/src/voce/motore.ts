// Motore della modalità conversazione: ascolta, capisce, risponde a voce frase per frase, si zittisce se lo interrompi.
import { FintoMicrofono, FintoParlatore, FintoTrascrittore, Microfono, ParlatoreWeb, type Parlatore, type Trascrittore,
  vocaFintaAttiva, WebSpeechTrascrittore } from './adattatori';
import { BargeIn, comandoConversazione, dividiFrasi } from './vad';

export type Fase = 'spento' | 'avvio' | 'ascolto' | 'elaborazione' | 'parla';
export interface Misure { fineToTesto: number[]; testoToVoce: number[]; bargeInToSilenzio: number[] }
export interface StatoConv { fase: Fase; parziale: string; detto: string; fraseGuardian: string; livello: number; errore: string;
  trascrittore: string; privato: boolean; misure: Misure }
/** Risponde a una frase dell'utente. Può restituire un testo (subito) o un flusso di frasi (es. il cervello sul PC). */
export type Risponditore = (testo: string) => Promise<string | AsyncIterable<string>>;

export const SILENZIO_FINE_MS = 60_000;
let localeVisto = false;
/** La UI lo segnala quando il servizio vocale locale risponde (abilita la conversazione anche senza Web Speech). */
export function segnaLocaleDisponibile(v: boolean) { localeVisto = v; }
const VUOTO: StatoConv = { fase: 'spento', parziale: '', detto: '', fraseGuardian: '', livello: 0, errore: '', trascrittore: '', privato: false,
  misure: { fineToTesto: [], testoToVoce: [], bargeInToSilenzio: [] } };

class Motore {
  stato: StatoConv = VUOTO;
  private subs = new Set<() => void>();
  private tr: Trascrittore | null = null; private voce: Parlatore | null = null; private mic: Microfono | FintoMicrofono | null = null;
  private rispondi: Risponditore | null = null; private raf = 0; private turno = 0; private ultimaAttivita = 0;
  private barge = new BargeIn(); private tParziale = 0; private trascrittoreScelto: (() => Promise<Trascrittore | null>) | null = null;

  iscrivi = (f: () => void) => { this.subs.add(f); return () => { this.subs.delete(f); }; };
  private spento() { return this.stato.fase === 'spento'; }
  private set(p: Partial<StatoConv>) { this.stato = { ...this.stato, ...p }; this.subs.forEach((f) => f()); }
  private misura(k: keyof Misure, v: number) { const m = { ...this.stato.misure, [k]: [...this.stato.misure[k].slice(-9), Math.round(v)] }; this.set({ misure: m }); }

  /** Permette all'ondata 3 di proporre un trascrittore migliore (locale e privato) prima del browser. */
  preferisci(f: () => Promise<Trascrittore | null>) { this.trascrittoreScelto = f; }

  // con la voce locale serve solo la sintesi; senza, anche il riconoscimento del browser
  static supportata() { return vocaFintaAttiva() || (ParlatoreWeb.disponibile() && (WebSpeechTrascrittore.disponibile() || localeVisto)); }

  async avvia(rispondi: Risponditore) {
    if (this.stato.fase !== 'spento') return;
    this.rispondi = rispondi; this.set({ ...VUOTO, misure: this.stato.misure, fase: 'avvio' });
    const finto = vocaFintaAttiva();
    this.tr = (finto ? new FintoTrascrittore() : await this.trascrittoreScelto?.()) ?? new WebSpeechTrascrittore();
    this.voce = finto ? new FintoParlatore() : new ParlatoreWeb();
    this.mic = finto ? new FintoMicrofono() : new Microfono();
    try {
      await this.mic.apri();
      await this.tr.avvia({
        parziale: (t) => { this.tParziale = performance.now(); this.ultimaAttivita = Date.now(); this.set({ parziale: t }); },
        finale: (t) => void this.frase(t),
        errore: (m) => { this.set({ errore: m }); if (/permesso/i.test(m)) this.ferma(); },
      });
    } catch (e) {
      this.set({ errore: e instanceof Error && /denied|not allowed|permission/i.test(e.message) ? 'Permesso del microfono negato.' : 'Microfono non disponibile.' });
      this.ferma(); return;
    }
    this.ultimaAttivita = Date.now();
    this.set({ fase: 'ascolto', trascrittore: this.tr.nome, privato: this.tr.privato });
    const ciclo = () => {
      const liv = this.mic?.livello() ?? 0;
      if (Math.abs(liv - this.stato.livello) > 0.004) this.set({ livello: liv });
      document.documentElement.style.setProperty('--livello', String(Math.min(1, liv * 8)));
      if (this.stato.fase === 'parla' && this.barge.passo(liv, performance.now())) this.interrompi(true);
      if (this.stato.fase === 'ascolto' && Date.now() - this.ultimaAttivita > SILENZIO_FINE_MS) { this.ferma(); return; }
      this.raf = requestAnimationFrame(ciclo);
    };
    this.raf = requestAnimationFrame(ciclo);
  }

  private async frase(testo: string) {
    const fine = performance.now(); this.ultimaAttivita = Date.now();
    if (this.tParziale) this.misura('fineToTesto', fine - this.tParziale);
    this.set({ detto: testo, parziale: '' });
    const cmd = comandoConversazione(testo);
    if (cmd === 'termina') { await this.di('Va bene, chiudo la conversazione.'); this.ferma(); return; }
    if (cmd === 'silenzio') { this.interrompi(false); return; }
    if (this.stato.fase === 'parla') this.interrompi(true);
    const mio = ++this.turno;
    this.set({ fase: 'elaborazione' });
    try {
      const r = await this.rispondi!(testo);
      if (mio !== this.turno || this.spento()) return;
      let prima = true;
      const fonte = typeof r === 'string' ? dividiFrasi(r) : r;
      for await (const f of fonte) {
        if (mio !== this.turno || this.spento()) return;
        if (prima) { this.misura('testoToVoce', performance.now() - fine); prima = false; }
        await this.di(f, mio);
      }
    } catch { if (mio === this.turno) await this.di('Non sono riuscito a rispondere.', mio); }
    if (mio === this.turno && !this.spento()) { this.tr?.riprendi(); this.set({ fase: 'ascolto', fraseGuardian: '' }); }
  }

  private async di(frase: string, turno = this.turno) {
    if (!this.voce || this.stato.fase === 'spento' || turno !== this.turno) return;
    this.tr?.pausa(); this.barge.azzera();
    this.set({ fase: 'parla', fraseGuardian: frase });
    await this.voce.parla(frase);
  }

  /** Interrompe Guardian: per barge-in (l'utente parla) o per «silenzio». Torna subito ad ascoltare. */
  interrompi(barge: boolean) {
    const t0 = performance.now();
    this.turno++; this.voce?.zitto(); this.tr?.riprendi();
    if (this.stato.fase !== 'spento') this.set({ fase: 'ascolto', fraseGuardian: '' });
    if (barge) this.misura('bargeInToSilenzio', performance.now() - t0);
  }

  ferma() {
    cancelAnimationFrame(this.raf); this.turno++;
    this.voce?.zitto(); this.tr?.ferma(); this.mic?.chiudi();
    this.tr = null; this.voce = null; this.mic = null;
    document.documentElement.style.setProperty('--livello', '0');
    this.set({ fase: 'spento', livello: 0, parziale: '', fraseGuardian: '' });
  }
}

export const motore = new Motore();
export const conversazioneSupportata = () => (Motore as unknown as { supportata(): boolean }).supportata();
