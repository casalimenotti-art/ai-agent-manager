// Vista centrale permanente: non viene mai sostituita dai pannelli.
import { Activity, BarChart3, Bot, Building2, ListTodo, ShieldCheck, Sparkles } from 'lucide-react';
import { useEffect, useState } from 'react';
import { statoNucleo, testoStato } from '../logic/guardian';
import { agentiAlLavoro, completatiOggi, errori24h } from '../logic/metrics';
import { report } from '../logic/report';
import { fa, statoAgente, statoDispositivo } from '../logic/status';
import { leggiPreferenze, salvaPreferenze, useG } from '../state';
import { TASK_TERMINALI, type Task } from '../types';
import { GuardianCore } from './GuardianCore';
import { Gravita, Scheletro, Sezione, StatoAgente, StatoTask, Vuoto } from './kit';
import { OrbitaStanze, VistaStanza } from './Stanze';
import { useVoce } from './voce';
import { PulsanteConversazione, StatoCervello, useConversazione } from './Conversazione';

const ORDINE: Task['stato'][] = ['running', 'needs_approval', 'blocked', 'failed', 'waiting', 'ready'];
const PESO_PRIO = { urgente: 0, alta: 1, media: 2, bassa: 3 };

export function taskImportanti(tasks: Task[], n = 7) {
  return tasks.filter((t) => ORDINE.includes(t.stato))
    .sort((a, b) => ORDINE.indexOf(a.stato) - ORDINE.indexOf(b.stato) || PESO_PRIO[a.priorita] - PESO_PRIO[b.priorita])
    .slice(0, n);
}

export function CommandCenter() {
  const { snap, pingOk, pensa, setVoce, apri, errore, stanza, apriStanza } = useG();
  const { ascolta: pushToTalk } = useVoce();
  const [dettagli, setDettagli] = useState(() => leggiPreferenze().dettagliAperti);
  const cambiaDettagli = () => { const v = !dettagli; setDettagli(v); salvaPreferenze({ ...leggiPreferenze(), dettagliAperti: v }); };
  const conv = useConversazione();
  const ascolta = pushToTalk || conv.fase === 'ascolto';
  const voce = conv.fase === 'parla' ? 'parla' : ascolta ? 'ascolto' : null;
  useEffect(() => setVoce(voce), [setVoce, voce]);
  const opz = { pingOk, ascolta, pensa: pensa || conv.fase === 'elaborazione', parla: conv.fase === 'parla' };
  const stato = statoNucleo(snap, opz);
  useEffect(() => { window.scrollTo({ top: 0 }); }, [stanza]);
  if (stanza) return (
    <div className="stack">
      <button className="nucleo-compatto" onClick={() => apriStanza(null)} aria-label="Guardian: torna al centro">
        <GuardianCore stato={stato} />
        <span><b>Guardian</b><span className="stato-c" aria-live="polite">{testoStato(snap, opz)}</span></span>
      </button>
      <VistaStanza id={stanza} />
    </div>
  );
  const r = snap ? report(snap) : null;
  const nome = (uid?: string | null) => snap?.users.find((u) => u.id === uid)?.nome ?? uid ?? '—';
  const agente = (id?: string | null) => snap?.agents.find((a) => a.id === id)?.nome;

  return (
    <div className="cc">
      <section className="hero" aria-label="Guardian">
        <GuardianCore stato={stato} />
        <div>
          <h1>Guardian</h1>
          <p className="stato" aria-live="polite">{testoStato(snap, opz)}</p>
          <div className="row hero-comandi"><PulsanteConversazione /><StatoCervello />
            <button type="button" className="btn ghost sm tendina-btn" aria-expanded={dettagli} aria-controls="dettagli-centro" onClick={cambiaDettagli}>
              <BarChart3 size={14} aria-hidden /> {dettagli ? 'Chiudi dettagli' : 'Dettagli'}</button></div>
          <div className="stellar-status" aria-label="Stato dei collegamenti">
            <button type="button" onClick={() => apri({ p: 'email' })}>Email non collegata</button>
            <button type="button" onClick={() => apri({ p: 'dispositivi' })}>PC {snap ? `${snap.devices.slice(0, 3).filter((d) => statoDispositivo(d) === 'online').length}/3` : '—/3'}</button>
          </div>
          {errore && <p className="err" role="alert">{errore}</p>}
          <div className="kpis tendina stellar-kpis" id="numeri-centro">
            {snap ? (<>
              <button className="kpi" onClick={() => apri({ p: 'agenti' })}>
                <div className="v">{agentiAlLavoro(snap)}<span className="dim" style={{ fontSize: '1rem' }}>/{snap.agents.length}</span></div>
                <div className="l">Agenti al lavoro</div><div className="f">dal bridge, ultimi 180 s</div></button>
              <button className="kpi" onClick={() => apri({ p: 'tasks', filtro: 'attivi' })}>
                <div className="v">{r!.conteggi.running}</div><div className="l">Task in esecuzione</div><div className="f">{r!.aperti} aperti in totale</div></button>
              <button className="kpi" onClick={() => apri({ p: 'approvazioni' })}>
                <div className="v" style={{ color: r!.approvazioni ? 'var(--warn)' : undefined }}>{r!.approvazioni}</div>
                <div className="l">Approvazioni in attesa</div><div className="f">decide una persona</div></button>
              <button className="kpi" onClick={() => apri({ p: 'statistiche' })}>
                <div className="v">{completatiOggi(snap)}</div><div className="l">Completati oggi</div>
                <div className="f">{errori24h(snap)} errori nelle ultime 24 h</div></button>
            </>) : Array.from({ length: 4 }, (_, i) => <div key={i} className="kpi"><Scheletro righe={2} /></div>)}
          </div>
        </div>
      </section>

      {dettagli && <aside className="dettagli-centro" id="dettagli-centro" aria-labelledby="titolo-dettagli">
      <h2 id="titolo-dettagli" className="details-heading">Dettagli del Centro</h2>
      <OrbitaStanze />

      <Sezione titolo="Prossime azioni" icona={Sparkles} conta={r?.prossime.length} className="col-5">
        {!r ? <Scheletro /> : r.prossime.length === 0 ? <Vuoto icona={Sparkles}>Nessuna azione urgente.</Vuoto> : (
          <div className="list">
            {r.prossime.slice(0, 6).map((a, i) => (
              <button key={i} className="item" onClick={() => a.ref.tipo === 'stanza' ? apriStanza(String(a.ref.id)) : apri(a.ref.tipo === 'task' ? { p: 'task', id: String(a.ref.id) }
                : a.ref.tipo === 'agent' ? { p: 'agente', id: String(a.ref.id) } : { p: 'approvazione', id: String(a.ref.id) })}>
                <span className={`pill ${a.priorita === 1 ? 'crit' : a.priorita === 2 ? 'warn' : 'accent'}`}>{a.priorita === 1 ? 'Ora' : a.priorita === 2 ? 'Presto' : 'Poi'}</span>
                <span className="t" style={{ fontWeight: 500 }}>{a.testo}</span>
              </button>
            ))}
          </div>)}
        <p className="dim" style={{ fontSize: 11, margin: '8px 0 0' }}>Calcolate dai dati con regole fisse, senza modelli AI.</p>
      </Sezione>

      <Sezione titolo="Flotta agenti" icona={Bot} conta={snap?.agents.length} className="col-7"
        azione={<button className="btn ghost sm" onClick={() => apri({ p: 'agenti' })}>Tutti</button>}>
        {!snap ? <Scheletro /> : snap.agents.length === 0 ? <Vuoto icona={Bot}>Nessun agente registrato. Avvia il Guardian Bridge sui PC.</Vuoto> : (
          <div className="agent-grid">
            {snap.agents.map((a) => {
              const s = statoAgente(a); const t = snap.tasks.find((x) => x.id === a.current_task_id);
              const uso = a.usage?.five_hour?.pct;
              return (
                <button key={a.id} className="card click agent" onClick={() => apri({ p: 'agente', id: a.id })} aria-label={`Agente ${a.nome} di ${nome(a.user_id)}`}>
                  <div className="row between"><div className="row"><span className={`dot ${s}`} aria-hidden /><b>{a.nome}</b></div><StatoAgente s={s} /></div>
                  <div className="dim mono" style={{ fontSize: 11, margin: '4px 0 8px' }}>{a.id} · {nome(a.user_id)}</div>
                  <div style={{ fontSize: 13 }}>{t ? `#${t.id} ${t.titolo}` : <span className="dim">Nessun task corrente</span>}</div>
                  <div className="dim" style={{ fontSize: 11, marginTop: 6 }}>Ultimo segnale {fa(a.last_heartbeat)}</div>
                  {typeof uso === 'number' && <div style={{ marginTop: 8 }}><div className="meter" title={`Utilizzo 5 ore: ${Math.round(uso)}%`}>
                    <span className={uso >= 90 ? 'hi' : ''} style={{ width: `${Math.min(100, uso)}%` }} /></div>
                    <div className="dim" style={{ fontSize: 11, marginTop: 2 }}>Utilizzo 5 h {Math.round(uso)}%</div></div>}
                </button>);
            })}
          </div>)}
      </Sezione>

      <Sezione titolo="Task attivi" icona={ListTodo} conta={snap?.tasks.filter((t) => !TASK_TERMINALI.includes(t.stato)).length} className="col-7"
        azione={<button className="btn ghost sm" onClick={() => apri({ p: 'tasks' })}>Vedi tutti</button>}>
        {!snap ? <Scheletro /> : taskImportanti(snap.tasks).length === 0 ? <Vuoto icona={ListTodo}>Nessun task attivo.</Vuoto> : (
          <div className="list">
            {taskImportanti(snap.tasks).map((t) => (
              <button key={t.id} className="item" onClick={() => apri({ p: 'task', id: String(t.id) })}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="t">#{t.id} {t.titolo}</div>
                  <div className="s">{agente(t.assigned_agent_id) ?? nome(t.responsabile)} · {snap.projects.find((p) => p.id === t.project_id)?.nome ?? 'senza azienda'} · {fa(t.updated_at)}</div>
                  {t.next_step && <div className="s" style={{ color: 'var(--text-2)' }}>→ {t.next_step}</div>}
                </div>
                <div className="stack" style={{ alignItems: 'flex-end', gap: 4 }}><StatoTask s={t.stato} /><span className="dim" style={{ fontSize: 11 }}>{t.priorita}</span></div>
              </button>))}
          </div>)}
      </Sezione>

      <Sezione titolo="Approvazioni in attesa" icona={ShieldCheck} conta={r?.approvazioni} className="col-5"
        azione={<button className="btn ghost sm" onClick={() => apri({ p: 'approvazioni' })}>Centro approvazioni</button>}>
        {!snap ? <Scheletro /> : !snap.approvals.some((a) => a.status === 'richiesta') ? <Vuoto icona={ShieldCheck}>Niente da approvare.</Vuoto> : (
          <div className="list">
            {snap.approvals.filter((a) => a.status === 'richiesta').slice(0, 5).map((a) => (
              <button key={a.id} className="item" onClick={() => apri({ p: 'approvazione', id: String(a.id) })}>
                <ShieldCheck size={18} color="var(--warn)" aria-hidden />
                <div><div className="t">{a.action}</div><div className="s">{a.action_type} · da {agente(a.agent_id) ?? nome(a.requested_by)} · {fa(a.created_at)}</div></div>
              </button>))}
          </div>)}
      </Sezione>

      <Sezione titolo="Attività recente" icona={Activity} className="col-7"
        azione={<button className="btn ghost sm" onClick={() => apri({ p: 'attivita' })}>Timeline</button>}>
        {!snap ? <Scheletro /> : snap.events.length === 0 ? <Vuoto icona={Activity}>Nessuna attività registrata.</Vuoto> : (
          <div className="list">
            {snap.events.slice(0, 6).map((e) => (
              <div key={e.id} className="item static">
                <div style={{ flex: 1 }}><div className="t" style={{ fontWeight: 500 }}>{e.message}</div>
                  <div className="s mono">{fa(e.timestamp)} · {e.event_type}{e.agent_name ? ` · ${e.agent_name}` : ''}</div></div>
                <Gravita s={e.severity} />
              </div>))}
          </div>)}
      </Sezione>

      <Sezione titolo="Aziende" icona={Building2} conta={snap?.projects.length} className="col-5"
        azione={<button className="btn ghost sm" onClick={() => apri({ p: 'aziende' })}>Gestisci</button>}>
        {!snap ? <Scheletro /> : snap.projects.length === 0 ? <Vuoto icona={Building2}>Nessuna azienda. Creane una da «Gestisci».</Vuoto> : (
          <div className="list">
            {snap.projects.filter((p) => p.stato === 'attivo').map((p) => {
              const ts = snap.tasks.filter((t) => t.project_id === p.id);
              const avvisi = ts.filter((t) => ['blocked', 'failed', 'needs_approval'].includes(t.stato)).length;
              return (
                <button key={p.id} className="item" onClick={() => apri({ p: 'azienda', id: String(p.id) })}>
                  <Building2 size={18} aria-hidden color="var(--accent-2)" />
                  <div style={{ flex: 1 }}><div className="t">{p.nome}</div>
                    <div className="s">{ts.filter((t) => !TASK_TERMINALI.includes(t.stato)).length} task aperti · {ts.filter((t) => t.stato === 'completed').length} completati</div></div>
                  {avvisi > 0 && <span className="pill warn">{avvisi} da guardare</span>}
                </button>);
            })}
          </div>)}
      </Sezione>
      </aside>}
    </div>
  );
}
