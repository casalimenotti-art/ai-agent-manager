// Modalità conversazione: pulsante, barra dei sottotitoli e collegamento del motore alla risposta di Guardian.
import { AudioLines, Brain, Lock, PhoneOff, Square } from 'lucide-react';
import { cervelloOnline } from '../logic/status';
import { useEffect, useSyncExternalStore } from 'react';
import { conversazioneSupportata, motore } from '../voce/motore';
import { perLaVoce } from '../voce/vad';
import { useG } from '../state';
import { useRispondi } from './useRispondi';

export function useConversazione() {
  return useSyncExternalStore(motore.iscrivi, () => motore.stato, () => motore.stato);
}

const ETICHETTE = { spento: '', avvio: 'Accendo il microfono…', ascolto: 'Ti ascolto', elaborazione: 'Ci penso…', parla: 'Guardian parla' };

export function StatoCervello() {
  const { snap } = useG();
  const on = cervelloOnline(snap?.cervello);
  return (
    <span className={`pill ${on ? 'ok' : ''}`} title={on ? 'Le domande aperte vanno a Claude Code sul PC del titolare (sola risposta)'
      : 'Senza cervello Guardian risponde solo dai dati. Per attivarlo: sul PC del titolare «guardian_bridge.py cervello»'}>
      <Brain aria-hidden />{on ? `Cervello online · ${snap?.cervello?.modello ?? 'Claude Code'}` : 'Cervello offline · risposte dai dati'}</span>
  );
}

export function PulsanteConversazione({ compatto = false }: { compatto?: boolean }) {
  const s = useConversazione();
  const rispondi = useRispondi();
  const ok = conversazioneSupportata();
  const attiva = s.fase !== 'spento';
  const titolo = !ok ? 'Conversazione non disponibile: questo browser non supporta riconoscimento e sintesi vocale (prova Chrome o Edge)'
    : attiva ? 'Termina la conversazione' : 'Conversazione a voce: parli e Guardian ti risponde a voce (mani libere)';
  const avvia = () => void motore.avvia(async (t) => { const r = await rispondi(t); return typeof r === 'string' ? perLaVoce(r) : r; });
  return (
    <button type="button" className={`btn ${compatto ? 'icon' : 'primary conv-btn'} ${attiva ? 'conv-on' : ''}`} disabled={!ok} title={titolo}
      aria-label={attiva ? 'Termina la conversazione' : 'Avvia la conversazione a voce'} aria-pressed={attiva}
      onClick={() => (attiva ? motore.ferma() : avvia())}>
      {attiva ? <PhoneOff size={compatto ? 17 : 18} aria-hidden /> : <AudioLines size={compatto ? 17 : 18} aria-hidden />}
      {!compatto && (attiva ? 'Termina conversazione' : 'Conversazione')}
    </button>
  );
}

export function BarraConversazione() {
  const s = useConversazione();
  const { pannello, paletteAperta } = useG();
  useEffect(() => {
    const f = (e: KeyboardEvent) => { if (e.key === 'Escape' && motore.stato.fase !== 'spento' && !pannello && !paletteAperta) { e.stopImmediatePropagation(); motore.ferma(); } };
    window.addEventListener('keydown', f, true); return () => window.removeEventListener('keydown', f, true);
  }, [pannello, paletteAperta]);
  if (s.fase === 'spento') return s.errore ? <div className="err" role="alert" style={{ marginBottom: 6 }}>{s.errore}</div> : null;
  return (
    <div className="conv-barra" role="region" aria-label="Conversazione a voce" data-fase={s.fase}>
      <div className="row between">
        <span className="row" style={{ gap: 8 }}>
          <span className="conv-onde" aria-hidden><i /><i /><i /><i /></span>
          <b aria-live="polite">{ETICHETTE[s.fase]}</b>
          <span className={`pill ${s.privato ? 'ok' : ''}`} title={s.privato ? "L'audio resta sul tuo PC" : "Il browser può inviare l'audio ai suoi server per il riconoscimento"}>
            {s.privato && <Lock aria-hidden />}{s.trascrittore}{s.privato ? ' · privato' : ''}</span>
        </span>
        <span className="row" style={{ gap: 6 }}>
          {s.fase === 'parla' && <button className="btn sm" onClick={() => motore.interrompi(false)}><Square size={14} aria-hidden />Silenzio</button>}
          <button className="btn sm danger" onClick={() => motore.ferma()}><PhoneOff size={14} aria-hidden />Termina</button>
        </span>
      </div>
      <div className="conv-sub" aria-live="polite">
        {s.parziale ? <span className="tu">«{s.parziale}…»</span> : s.fase === 'ascolto' && s.detto ? <span className="tu dim">Hai detto: «{s.detto}»</span> : null}
        {s.fraseGuardian && <span className="lui">{s.fraseGuardian}</span>}
        {!s.parziale && !s.fraseGuardian && s.fase === 'ascolto' && !s.detto && <span className="dim">Parla pure. Di' «basta» per chiudere, «silenzio» per zittirmi. Puoi interrompermi parlando.</span>}
      </div>
      {s.errore && <div className="err" role="alert">{s.errore}</div>}
    </div>
  );
}
