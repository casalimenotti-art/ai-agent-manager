// Unico punto in cui Guardian risponde (chat scritta e conversazione a voce): comandi, intenti dai dati, cervello (ondata 4).
import { useCallback } from 'react';
import { comandoStanza, DOMANDE_ESEMPIO, rispondiConContesto } from '../logic/intents';
import { useG } from '../state';

const CLASSICO = import.meta.env.VITE_GUARDIAN_CLASSICO_URL as string | undefined;
const norm = (t: string) => t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');

export function useRispondi() {
  const { snap, pannello, aggiungiMessaggio, setPensa, apri, stanza, apriStanza, chiudi } = useG();
  return useCallback(async (q: string): Promise<string> => {
    const domanda = q.trim(); if (!domanda) return '';
    aggiungiMessaggio({ da: 'user', testo: domanda });
    const di = (testo: string, fonte?: string) => { aggiungiMessaggio({ da: 'guardian', testo, fonte }); return testo; };
    if (!snap) return di('I dati non sono ancora caricati: riprova tra un istante.');
    const cmd = comandoStanza(domanda, snap);
    if (cmd) { chiudi(); apriStanza(cmd.stanza); return di(cmd.testo, 'comando'); }
    if (/\bapprova\b/.test(norm(domanda))) { // mai approvazioni solo vocali: apre il pannello, serve il clic
      const attese = snap.approvals.filter((a) => a.status === 'richiesta');
      const parole = norm(domanda).replace(/.*\bapprova\b/, '').split(/\W+/).filter((p) => p.length > 3);
      const a = attese.find((x) => parole.some((p) => norm(x.action).includes(p))) ?? (attese.length === 1 ? attese[0] : undefined);
      if (!a) return di(attese.length ? `Ci sono ${attese.length} approvazioni in attesa: dimmi quale, o aprile dal centro.` : 'Non ci sono approvazioni in attesa.', 'approvals');
      apri({ p: 'approvazione', id: String(a.id) });
      return di(`Ho aperto «${a.action}». Per sicurezza conferma tu con un clic su Approva o Rifiuta.`, 'approvals');
    }
    setPensa(true);
    try {
      const r = rispondiConContesto(domanda, snap, pannello ?? (stanza ? { p: 'stanza', id: stanza } : null));
      if (r) { if (r.apri) apri({ p: r.apri.p, filtro: r.apri.filtro }); return di(r.testo, r.fonte); }
      return di(`Non ho una risposta dai dati per questa richiesta. Per richieste aperte serve il cervello di Guardian` +
        `${CLASSICO ? ' (o il planner nel Guardian classico)' : ''}. Prova: «${DOMANDE_ESEMPIO.slice(0, 3).join('», «')}».`, 'router di intenti');
    } finally { setPensa(false); }
  }, [snap, pannello, aggiungiMessaggio, setPensa, apri, stanza, apriStanza, chiudi]);
}
