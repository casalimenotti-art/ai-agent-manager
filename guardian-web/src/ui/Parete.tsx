// Ondata 9: modalità parete (?parete=1). Schermo grande in ufficio: solo lettura, scritte grandi, aggiornamento continuo.
import { Maximize, X } from 'lucide-react';
import { useEffect, useState, type CSSProperties } from 'react';
import { euro, scadenzeDaGuardare, pipelinePerFase } from '../logic/amministrazione';
import { statoNucleo, testoStato } from '../logic/guardian';
import { agentiAlLavoro, completatiOggi } from '../logic/metrics';
import { report } from '../logic/report';
import { riepilogoStanza } from '../logic/stanze';
import { fa } from '../logic/status';
import { useG } from '../state';
import { GuardianCore } from './GuardianCore';
import { useConversazione } from './Conversazione';
import { coloreStanza } from './Stanze';

export function Parete() {
  const { snap, pingOk, pensa, setParete, diretta, source, presenti } = useG();
  const conv = useConversazione();
  const [ora, setOra] = useState(new Date());
  useEffect(() => { const t = setInterval(() => setOra(new Date()), 15_000); return () => clearInterval(t); }, []);
  useEffect(() => {
    const f = (e: KeyboardEvent) => { if (e.key === 'Escape' && !document.fullscreenElement) setParete(false); };
    window.addEventListener('keydown', f); return () => window.removeEventListener('keydown', f);
  }, [setParete]);
  const opz = { pingOk, ascolta: conv.fase === 'ascolto', pensa: pensa || conv.fase === 'elaborazione', parla: conv.fase === 'parla' };
  const r = snap ? report(snap) : null;
  const scad = snap ? scadenzeDaGuardare(snap.scadenze, 7) : [];
  const pipe = snap ? pipelinePerFase(snap.vendite) : null;
  const schermoIntero = () => { void document.documentElement.requestFullscreen?.().catch(() => {}); };
  return (
    <main className="parete" aria-label="Guardian, modalità parete">
      <div className="parete-comandi">
        <button className="btn ghost sm" onClick={schermoIntero}><Maximize size={16} aria-hidden />Schermo intero</button>
        <button className="btn ghost sm" onClick={() => setParete(false)}><X size={16} aria-hidden />Esci dalla parete</button>
      </div>
      <section className="parete-nucleo">
        <GuardianCore stato={statoNucleo(snap, opz)} />
        <div>
          <div className="parete-ora mono">{ora.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })}</div>
          <h1>Guardian</h1>
          <p className="parete-stato" aria-live="polite">{testoStato(snap, opz)}</p>
          {snap && <div className="parete-numeri">
            <span><b className="mono">{agentiAlLavoro(snap)}</b>agenti al lavoro</span>
            <span><b className="mono">{snap.tasks.filter((t) => t.stato === 'running').length}</b>task in corso</span>
            <span><b className="mono">{completatiOggi(snap)}</b>completati oggi</span>
            <span><b className="mono">{r?.approvazioni ?? 0}</b>da approvare</span>
          </div>}
        </div>
      </section>
      <section className="parete-stanze" aria-label="Stanze">
        {snap?.stanze.map((st) => {
          const x = riepilogoStanza(st, snap);
          return (
            <div key={st.id} className="parete-stanza" style={{ '--stanza': coloreStanza(st) } as CSSProperties}>
              <h2>{st.nome}</h2>
              <div className="parete-numeri piccoli">
                <span><b className="mono">{x.attivi}</b>attivi</span><span><b className="mono">{x.inEsecuzione}</b>in corso</span>
                <span><b className="mono">{x.fermi}</b>fermi</span><span><b className="mono">{x.approvazioni}</b>da approvare</span>
              </div>
              {st.id === 'vendite' && pipe && pipe.aperte > 0 && <p className="dim">Pipeline: {pipe.aperte} aperte · {euro(pipe.valoreAperto)}</p>}
              {st.id === 'amministrazione' && scad.length > 0 && <p className="dim">{scad.length} scadenze entro 7 giorni</p>}
            </div>);
        })}
      </section>
      <section className="parete-colonna" aria-label="Prossime azioni">
        <h3>Prossime azioni</h3>
        {r && r.prossime.length ? <ol>{r.prossime.slice(0, 5).map((a, i) => <li key={i} className={a.priorita === 1 ? 'urgente' : ''}>{a.testo}</li>)}</ol>
          : <p className="dim">Nessuna azione urgente.</p>}
      </section>
      <section className="parete-colonna" aria-label="Ultime attività">
        <h3>Ultime attività</h3>
        <ul>{snap?.events.slice(0, 6).map((e) => <li key={e.id}><span className="dim mono">{fa(e.timestamp)}</span> {e.message}</li>)}</ul>
      </section>
      <footer className="parete-piede dim">
        {source.modo === 'demo' ? 'Dati di esempio — solo locale' : diretta === 'live' ? 'Aggiornamenti in diretta' : 'Aggiornamento ogni 20 s'}
        {presenti.length > 0 && ` · nell'HQ: ${presenti.map((p) => p.nome).join(', ')}`}
      </footer>
    </main>
  );
}
