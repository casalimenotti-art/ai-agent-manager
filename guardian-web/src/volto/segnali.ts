// Segnali reali per il volto: richieste (chat, voce, palette), eventi Realtime, ampiezza della voce di Guardian.
// Valori letti a ogni frame dal volto: nessun re-render di React.
export const segnali = { ultimaRichiesta: null as number | null, ultimoEvento: null as number | null, ampiezza: 0, ampiezzaStimata: true };

export const segnalaRichiesta = () => { segnali.ultimaRichiesta = performance.now(); };
export const segnalaEvento = () => { segnali.ultimoEvento = performance.now(); };

/** Con la voce del browser non c'è l'audio: l'evento `boundary` (inizio parola) dà un inviluppo stimato. */
export function parolaDetta(lunghezza = 5) {
  segnali.ampiezza = Math.min(1, 0.55 + lunghezza / 20);
  segnali.ampiezzaStimata = true;
}
/** Chiamata a ogni frame: l'ampiezza decade da sola tra una parola e l'altra. */
export function decadiAmpiezza(dt: number) { segnali.ampiezza *= Math.exp(-dt / 0.16); }
