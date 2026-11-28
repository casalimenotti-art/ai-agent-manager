// Pannelli di sistema: agenti, aziende, notifiche, attività, statistiche, workflow, PC, salute, impostazioni.
import { Activity, Bell, Bot, Building2, Cpu, GitBranchPlus, Plus } from 'lucide-react';
import { useEffect, useState } from 'react';
import { cervelloOnline, fa, statoAgente, statoDispositivo } from '../../logic/status';
import { leggiPreferenze, salvaPreferenze, useG, type Pannello, type Preferenze } from '../../state';
import { TASK_TERMINALI, type AgentLog, type Severita } from '../../types';
import { Gravita, Scheletro, StatoAgente, StatoTask, Vuoto } from '../kit';
import { supportoAscolto, supportoParlato } from '../voce';
import { suona } from '../suoni';
import { useConversazione } from '../Conversazione';
import { conversazioneSupportata } from '../../voce/motore';

export function AgentiPanel() {
  const { snap, apri } = useG();
  if (!snap) return <Scheletro />;
  return (<>
    <p className="note">Lo stato arriva solo da eventi reali (hook di Claude Code, notify di Codex) inviati dal Guardian Bridge.
      Un PC acceso non rende «online» il suo agente: senza segnali da 180 s lo stato è «sconosciuto».</p>
    {snap.agents.length === 0 ? <Vuoto icona={Bot}>Nessun agente. Sul PC: GUARDIAN_CLAUDE_AGENT_ID o GUARDIAN_CODEX_AGENT_ID in bridge/.env, poi «guardian_bridge.py run».</Vuoto> :
      <div className="list">{snap.agents.map((a) => (
        <button key={a.id} className="item" onClick={() => apri({ p: 'agente', id: a.id })}>
          <div style={{ flex: 1 }}><div className="t">{a.nome} <span className="dim mono" style={{ fontWeight: 400 }}>{a.id}</span></div>
            <div className="s">{snap.users.find((u) => u.id === a.user_id)?.nome} · ultimo segnale {fa(a.last_heartbeat)}{a.disponibile ? '' : ' · non disponibile'}</div></div>
          <StatoAgente s={statoAgente(a)} /></button>))}</div>}
  </>);
}

export function AgentePanel({ id }: Pannello) {
  const { snap, source, esegui, user, apri } = useG();
  const [log, setLog] = useState<AgentLog[] | null>(null);
  const [assegna, setAssegna] = useState('');
  useEffect(() => { if (id) source.logAgente(id, 50).then(setLog).catch(() => setLog([])); }, [source, id]);
  if (!snap) return <Scheletro />;
  const a = snap.agents.find((x) => x.id === id);
  if (!a) return <Vuoto>Agente non trovato.</Vuoto>;
  const s = statoAgente(a); const pc = snap.devices.find((d) => d.id === a.device_id);
  const suoi = snap.tasks.filter((t) => t.assigned_agent_id === a.id);
  const liberi = snap.tasks.filter((t) => !t.assigned_agent_id && ['ready', 'planned', 'backlog'].includes(t.stato));
  return (<>
    <div className="row"><StatoAgente s={s} /><span className="pill mono">{a.tipo}</span>{!a.disponibile && <span className="pill warn">non disponibile</span>}</div>
    <dl className="kv">
      <dt>Collaboratore</dt><dd>{snap.users.find((u) => u.id === a.user_id)?.nome ?? a.user_id}</dd>
      <dt>PC</dt><dd>{pc ? `${pc.nome} (${statoDispositivo(pc)})` : 'non indicato'}</dd>
      <dt>Ultimo segnale</dt><dd>{fa(a.last_heartbeat)}</dd><dt>Ultima attività</dt><dd>{fa(a.last_activity)}</dd>
      <dt>Capacità</dt><dd>{a.capabilities.length ? a.capabilities.join(', ') : '—'}</dd>
      {a.usage && <><dt>Utilizzo</dt><dd className="mono">{a.usage.five_hour ? `5 h ${Math.round(a.usage.five_hour.pct)}%` : ''}{a.usage.seven_day ? ` · 7 g ${Math.round(a.usage.seven_day.pct)}%` : ''}</dd></>}
      {a.error && <><dt>Errore</dt><dd style={{ color: 'var(--crit)' }}>{a.error}</dd></>}
    </dl>
    <div className="row">
      <button className="btn" onClick={() => void esegui(() => source.disponibilitaAgente(a.id, !a.disponibile, user.id), 'Disponibilità aggiornata')}>
        {a.disponibile ? 'Segna come non disponibile' : 'Segna come disponibile'}</button>
      <button className="btn" onClick={() => apri({ p: 'handoff' })}>Apri handoff</button>
    </div>
    <form className="row" onSubmit={(e) => { e.preventDefault(); if (assegna) void esegui(() => source.modificaTask(Number(assegna), { assigned_agent_id: a.id }, user.id), 'Task assegnato'); }}>
      <select className="input" style={{ flex: 1, minWidth: 180 }} value={assegna} onChange={(e) => setAssegna(e.target.value)} aria-label="Task da assegnare">
        <option value="">Assegna un task libero…</option>{liberi.map((t) => <option key={t.id} value={t.id}>#{t.id} {t.titolo}</option>)}</select>
      <button className="btn primary" type="submit" disabled={!assegna}>Assegna</button></form>
    <h3 className="section-title">Task <span className="count">{suoi.length}</span></h3>
    {suoi.length === 0 ? <Vuoto>Nessun task assegnato.</Vuoto> : <div className="list">{suoi.map((t) => (
      <button key={t.id} className="item" onClick={() => apri({ p: 'task', id: String(t.id) })}><div style={{ flex: 1 }} className="t">#{t.id} {t.titolo}</div><StatoTask s={t.stato} /></button>))}</div>}
    <h3 className="section-title">Log recenti</h3>
    <p className="dim" style={{ fontSize: 12, margin: 0 }}>Solo metadati e richieste troncate a 200 caratteri, mai l'output degli strumenti.</p>
    {log === null ? <Scheletro /> : log.length === 0 ? <Vuoto>Nessun log: arrivano dal bridge con gli hook attivi.</Vuoto> :
      <table className="data"><thead><tr><th>Quando</th><th>Livello</th><th>Fonte</th><th>Messaggio</th></tr></thead>
        <tbody>{log.map((l) => <tr key={l.id}><td className="mono">{fa(l.ts)}</td><td>{l.level}</td><td>{l.source}</td><td>{l.message}</td></tr>)}</tbody></table>}
  </>);
}

export function AziendePanel() {
  const { snap, source, esegui, user, apri } = useG();
  const [f, setF] = useState({ nome: '', descrizione: '' });
  if (!snap) return <Scheletro />;
  return (<>
    <p className="note">Le aziende sono i progetti di NEXO. Ricavi, spese e clienti non hanno ancora una fonte reale nel database: non vengono mostrati.</p>
    {snap.projects.length === 0 ? <Vuoto icona={Building2}>Nessuna azienda.</Vuoto> : <div className="list">{snap.projects.map((p) => (
      <button key={p.id} className="item" onClick={() => apri({ p: 'azienda', id: String(p.id) })}><Building2 size={16} aria-hidden />
        <div style={{ flex: 1 }}><div className="t">{p.nome}</div><div className="s">{p.stato} · {snap.tasks.filter((t) => t.project_id === p.id && !TASK_TERMINALI.includes(t.stato)).length} task aperti</div></div></button>))}</div>}
    <form className="card stack" onSubmit={async (e) => { e.preventDefault();
      const ok = await esegui(() => source.creaProgetto(f.nome, f.descrizione, user.id), 'Azienda creata'); if (ok !== undefined) setF({ nome: '', descrizione: '' }); }}>
      <h3 className="section-title" style={{ margin: 0 }}>Nuova azienda</h3>
      <label className="field">Nome *<input className="input" required value={f.nome} onChange={(e) => setF({ ...f, nome: e.target.value })} /></label>
      <label className="field">Descrizione<input className="input" value={f.descrizione} onChange={(e) => setF({ ...f, descrizione: e.target.value })} /></label>
      <button className="btn primary" type="submit"><Plus size={16} aria-hidden />Crea</button></form>
  </>);
}

export function AziendaPanel({ id }: Pannello) {
  const { snap, apri } = useG();
  if (!snap) return <Scheletro />;
  const p = snap.projects.find((x) => String(x.id) === id);
  if (!p) return <Vuoto>Azienda non trovata.</Vuoto>;
  const ts = snap.tasks.filter((t) => t.project_id === p.id);
  const agenti = [...new Set(ts.map((t) => t.assigned_agent_id).filter(Boolean))] as string[];
  const ev = snap.events.filter((e) => e.project_id === p.id || ts.some((t) => t.id === e.task_id)).slice(0, 10);
  const conta = (s: string) => ts.filter((t) => t.stato === s).length;
  return (<>
    {p.descrizione && <p style={{ margin: 0 }}>{p.descrizione}</p>}
    <div className="kpis">{[['In esecuzione', conta('running')], ['Pronti', conta('ready')], ['Bloccati/falliti', conta('blocked') + conta('failed')], ['Completati', conta('completed')]]
      .map(([l, v]) => <div key={l} className="kpi" style={{ cursor: 'default' }}><div className="v">{v}</div><div className="l">{l}</div></div>)}</div>
    <h3 className="section-title">Agenti coinvolti</h3>
    {agenti.length === 0 ? <Vuoto>Nessun agente assegnato ai task.</Vuoto> : <div className="row">{agenti.map((a) =>
      <button key={a} className="pill accent" style={{ border: 0, cursor: 'pointer' }} onClick={() => apri({ p: 'agente', id: a })}>{a}</button>)}</div>}
    <h3 className="section-title">Task <span className="count">{ts.length}</span></h3>
    {ts.length === 0 ? <Vuoto>Nessun task.</Vuoto> : <div className="list">{ts.map((t) => (
      <button key={t.id} className="item" onClick={() => apri({ p: 'task', id: String(t.id) })}><div style={{ flex: 1 }} className="t">#{t.id} {t.titolo}</div><StatoTask s={t.stato} /></button>))}</div>}
    <h3 className="section-title">Eventi recenti</h3>
    {ev.length === 0 ? <Vuoto>Nessun evento.</Vuoto> : ev.map((e) => <div key={e.id} className="item static"><div><div className="t" style={{ fontWeight: 500 }}>{e.message}</div><div className="s">{fa(e.timestamp)}</div></div></div>)}
  </>);
}

export function NotifichePanel() {
  const { snap, source, esegui, user, apri } = useG();
  if (!snap) return <Scheletro />;
  const destinazione = (t?: string | null, id?: string | null): Pannello | null =>
    !id ? null : t === 'tasks' ? { p: 'task', id } : t === 'agents' ? { p: 'agente', id } : t === 'approvals' ? { p: 'approvazione', id } : t === 'handoffs' ? { p: 'handoff' } : null;
  const nonLette = snap.notifications.filter((n) => !n.read_at).length;
  return (<>
    <div className="row between"><span className="muted">{nonLette} non lette</span>
      <button className="btn sm" disabled={!nonLette} onClick={() => void esegui(() => source.segnaLetta(user.id), 'Tutte lette')}>Segna tutte come lette</button></div>
    {snap.notifications.length === 0 ? <Vuoto icona={Bell}>Nessuna notifica. Arrivano per approvazioni, task falliti, agenti in errore e handoff verso di te.</Vuoto> :
      <div className="list">{snap.notifications.map((n) => {
        const dest = destinazione(n.ref_table, n.ref_id);
        return (
          <button key={n.id} className="item" onClick={() => { if (!n.read_at) void esegui(() => source.segnaLetta(user.id, n.id)); if (dest) apri(dest); }}>
            {!n.read_at && <span className="pill accent">nuova</span>}
            <div style={{ flex: 1 }}><div className="t">{n.message}</div><div className="s">{n.kind.replace(/_/g, ' ')} · {fa(n.created_at)}</div></div>
          </button>);
      })}</div>}
  </>);
}

export function AttivitaPanel() {
  const { snap } = useG();
  const [sev, setSev] = useState<'' | Severita>(''); const [tipo, setTipo] = useState(''); const [ag, setAg] = useState('');
  if (!snap) return <Scheletro />;
  const tipi = [...new Set(snap.events.map((e) => e.event_type))].sort();
  const lista = snap.events.filter((e) => (!sev || e.severity === sev) && (!tipo || e.event_type === tipo) && (!ag || e.agent_id === ag));
  return (<>
    <div className="row">
      <select className="input" style={{ maxWidth: 160 }} value={sev} onChange={(e) => setSev(e.target.value as Severita | '')} aria-label="Gravità">
        <option value="">Tutte le gravità</option><option value="info">info</option><option value="warning">attenzione</option><option value="error">errore</option><option value="critical">critico</option></select>
      <select className="input" style={{ maxWidth: 200 }} value={tipo} onChange={(e) => setTipo(e.target.value)} aria-label="Tipo"><option value="">Tutti i tipi</option>{tipi.map((t) => <option key={t}>{t}</option>)}</select>
      <select className="input" style={{ maxWidth: 200 }} value={ag} onChange={(e) => setAg(e.target.value)} aria-label="Agente"><option value="">Tutti gli agenti</option>{snap.agents.map((a) => <option key={a.id} value={a.id}>{a.id}</option>)}</select>
    </div>
    <p className="dim" style={{ fontSize: 12, margin: 0 }}>Ultimi {snap.events.length} eventi reali. I log dettagliati di ogni agente sono nel suo pannello.</p>
    {lista.length === 0 ? <Vuoto icona={Activity}>Nessun evento con questi filtri.</Vuoto> : <div className="list">{lista.map((e) => (
      <div key={e.id} className="item static"><div style={{ flex: 1 }}><div className="t" style={{ fontWeight: 500 }}>{e.message}</div>
        <div className="s mono">{fa(e.timestamp)} · {e.event_type}{e.user_id ? ` · ${e.user_id}` : ''}{e.task_id ? ` · task #${e.task_id}` : ''}</div></div><Gravita s={e.severity} /></div>))}</div>}
  </>);
}

export function StatistichePanel() {
  const { snap } = useG();
  if (!snap) return <Scheletro />;
  const aperti = snap.tasks.filter((t) => !TASK_TERMINALI.includes(t.stato));
  const running = snap.tasks.filter((t) => t.stato === 'running').length;
  const completati = snap.tasks.filter((t) => t.stato === 'completed').length;
  const falliti = snap.tasks.filter((t) => t.stato === 'failed').length;
  const attivi = snap.agents.filter((a) => ['working', 'waiting', 'needs_approval'].includes(statoAgente(a))).length;
  const approvazioni = snap.approvals.filter((a) => a.status === 'richiesta').length;
  const pcOnline = snap.devices.filter((d) => statoDispositivo(d) !== 'offline').length;
  const oggi = new Date(); oggi.setHours(0, 0, 0, 0);
  const inizio = new Date(oggi); inizio.setDate(oggi.getDate() - 13);
  const completatiGiornalieri = Array.from({ length: 14 }, (_, i) => {
    const giorno = new Date(inizio); giorno.setDate(inizio.getDate() + i);
    const fine = new Date(giorno); fine.setDate(giorno.getDate() + 1);
    const n = snap.events.filter((e) => e.event_type === 'task_completed' && Date.parse(e.timestamp) >= giorno.getTime() && Date.parse(e.timestamp) < fine.getTime()).length;
    return { giorno, n };
  });
  const massimo = Math.max(1, ...completatiGiornalieri.map((g) => g.n));
  const formatoGiorno = new Intl.DateTimeFormat('it-IT', { day: '2-digit', month: '2-digit' });
  const inizioSettimanaScorsa = new Date(oggi); inizioSettimanaScorsa.setDate(oggi.getDate() - 13);
  const inizioSettimanaCorrente = new Date(oggi); inizioSettimanaCorrente.setDate(oggi.getDate() - 6);
  const haSettimanaScorsa = snap.events.some((e) => e.event_type === 'task_completed' && Date.parse(e.timestamp) >= inizioSettimanaScorsa.getTime() && Date.parse(e.timestamp) < inizioSettimanaCorrente.getTime());
  const completatiSettimanaScorsa = completatiGiornalieri.slice(0, 7).reduce((n, g) => n + g.n, 0);
  const completatiSettimanaCorrente = completatiGiornalieri.slice(7).reduce((n, g) => n + g.n, 0);
  const righe: [string, number][] = [
    ['Agenti attivi', attivi], ['Task aperti', aperti.length], ['In esecuzione', running], ['Completati', completati],
    ['Falliti', falliti], ['Approvazioni in attesa', approvazioni], ['PC online', pcOnline],
  ];
  return <section className="stats-panel" aria-label="Statistiche Guardian">
    <dl className="stats-summary">{righe.map(([nome, valore]) => <div key={nome}><dt>{nome}</dt><dd>{valore}</dd></div>)}</dl>
    <section className="stats-chart" aria-labelledby="stats-completati-titolo">
      <h3 id="stats-completati-titolo">Task completati · ultimi 14 giorni</h3>
      {snap.events.length === 0 ? <p className="dim">Non disponibile: non ci sono eventi registrati.</p> : <svg viewBox="0 0 560 190" role="img" aria-label="Barre dei task completati al giorno negli ultimi 14 giorni">
        <line x1="24" y1="150" x2="548" y2="150" stroke="rgba(242,246,255,.24)" />
        {completatiGiornalieri.map(({ giorno, n }, i) => {
          const x = 30 + i * 37; const altezza = n ? Math.max(2, n / massimo * 112) : 1;
          return <g key={giorno.toISOString()}><rect x={x} y={150 - altezza} width="22" height={altezza} rx="3" fill="#F2F6FF" fillOpacity=".78" />
            {i % 2 === 0 && <text x={x + 11} y="173" textAnchor="middle" fill="rgba(242,246,255,.72)" fontSize="12">{formatoGiorno.format(giorno)}</text>}</g>;
        })}
      </svg>}
      {haSettimanaScorsa && <p className="stats-compare">Settimana scorsa: {completatiSettimanaScorsa} · ultimi 7 giorni: {completatiSettimanaCorrente}</p>}
    </section>
    <section className="stats-recent" aria-labelledby="stats-attivita-titolo">
      <h3 id="stats-attivita-titolo">Attività recente</h3>
      {snap.events.length === 0 ? <p>Nessuna attività registrata.</p> : <ul>{snap.events.slice(0, 8).map((evento) => <li key={evento.id}>
        <span>{evento.message}</span><time>{fa(evento.timestamp)}</time>
      </li>)}</ul>}
    </section>
    <p className="stats-footnote">I numeri arrivano dallo snapshot Guardian. Un dato assente viene indicato come non disponibile.</p>
  </section>;
}

export function WorkflowPanel() {
  return (<Vuoto icona={GitBranchPlus}>
    <b>Workflow non disponibile.</b><br />In Guardian non c'è ancora un motore di workflow: non mostriamo flussi finti.
    I lavori ricorrenti si gestiscono come task; un motore minimo (task ricorrenti con approvazione) è una fase futura da approvare.
  </Vuoto>);
}

export function DispositiviPanel() {
  const { snap } = useG();
  const classico = import.meta.env.VITE_GUARDIAN_CLASSICO_URL as string | undefined;
  if (!snap) return <Scheletro />;
  return (<>
    <p className="note">Un PC è online se il bridge ha inviato un segnale negli ultimi 120 s. La registrazione di un PC (con il token mostrato una sola volta)
      e la revoca si fanno dal Guardian classico{classico ? <> (<a href={classico} target="_blank" rel="noreferrer">apri</a>)</> : ''}.</p>
    {snap.devices.length === 0 ? <Vuoto icona={Cpu}>Nessun PC registrato.</Vuoto> : <div className="list">{snap.devices.map((d) => {
      const s = statoDispositivo(d);
      return (<div key={d.id} className="item static"><Cpu size={18} aria-hidden /><div style={{ flex: 1 }}><div className="t">{d.nome}</div>
        <div className="s">{snap.users.find((u) => u.id === d.user_id)?.nome} · ultimo segnale {fa(d.last_seen)} · checkpoint {fa(d.last_checkpoint)}</div></div>
        <span className={`pill ${s === 'offline' ? '' : s === 'online' || s === 'occupato' ? 'ok' : 'warn'}`}>{s}</span></div>);
    })}</div>}
  </>);
}

export function SalutePanel() {
  const { snap, source, pingOk, pingMs, pingAl, diretta, caricato, errore } = useG();
  const pcOn = snap?.devices.filter((d) => statoDispositivo(d) !== 'offline').length ?? 0;
  const conSegnale = snap?.agents.filter((a) => !['unknown', 'offline'].includes(statoAgente(a))).length ?? 0;
  const righe: [string, string, string, string][] = [
    ['App', 'ok', 'in esecuzione in questo browser', 'ora'],
    ['Database', pingOk === false ? 'crit' : pingOk ? 'ok' : '', pingOk === false ? 'non raggiungibile' : pingMs !== null ? `${Math.round(pingMs)} ms` : 'verifica…', pingAl ? fa(new Date(pingAl).toISOString()) : '—'],
    ['Dati', errore ? 'crit' : caricato ? 'ok' : '', errore ?? (caricato ? 'caricati' : 'in caricamento'), caricato ? fa(new Date(caricato).toISOString()) : '—'],
    ['Aggiornamenti', diretta === 'live' ? 'ok' : '', source.modo === 'demo' ? 'dati locali (nessuna diretta)' : diretta === 'live' ? 'Realtime attivo' : 'polling ogni 20 s', '—'],
    ['Bridge dei PC', pcOn ? 'ok' : 'warn', `${pcOn}/${snap?.devices.length ?? 0} PC online`, 'heartbeat < 120 s'],
    ['Agenti', conSegnale ? 'ok' : 'warn', `${conSegnale}/${snap?.agents.length ?? 0} con segnale`, 'bridge < 180 s'],
    ['Cervello (PC del titolare)', cervelloOnline(snap?.cervello) ? 'ok' : '', cervelloOnline(snap?.cervello) ? `online · ${snap?.cervello?.modello ?? ''}` : 'offline: risposte solo dai dati',
      snap?.cervello?.ultimo_battito ? fa(snap.cervello.ultimo_battito) : '—'],
    ['Planner AI', '', 'nel Guardian classico (le chiavi non stanno nel browser)', '—'],
  ];
  return (<table className="data"><thead><tr><th>Componente</th><th>Stato</th><th>Ultimo controllo</th></tr></thead>
    <tbody>{righe.map(([n, c, t, q]) => <tr key={n}><td>{n}</td><td><span className={`pill ${c}`}>{t}</span></td><td className="dim">{q}</td></tr>)}</tbody></table>);
}

function DiagnosticaVoce() {
  const s = useConversazione();
  const media = (v: number[]) => (v.length ? `${Math.round(v.reduce((a, b) => a + b, 0) / v.length)} ms (${v.length} misure)` : 'nessuna misura');
  return (
    <div className="card stack">
      <h3 className="section-title" style={{ margin: 0 }}>Diagnostica voce</h3>
      <dl className="kv">
        <dt>Conversazione</dt><dd>{conversazioneSupportata() ? 'disponibile in questo browser' : 'non disponibile in questo browser'}</dd>
        <dt>Ascolto in uso</dt><dd>{s.trascrittore || '—'}{s.privato ? ' (privato, sul PC)' : s.trascrittore ? ' (audio al browser)' : ''}</dd>
        <dt>Fine frase → testo</dt><dd className="mono">{media(s.misure.fineToTesto)} · obiettivo &lt; 1200 ms</dd>
        <dt>Testo → prima frase</dt><dd className="mono">{media(s.misure.testoToVoce)} · obiettivo &lt; 1500 ms</dd>
        <dt>Interruzione → silenzio</dt><dd className="mono">{media(s.misure.bargeInToSilenzio)} · obiettivo &lt; 200 ms</dd>
        <dt>Ampiezza della voce (volto)</dt><dd>stimata dalle parole: la voce del browser non dà l'audio</dd>
      </dl>
      <p className="dim" style={{ fontSize: 12, margin: 0 }}>Misure di questa sessione, prese durante le conversazioni reali.</p>
    </div>
  );
}

export function ImpostazioniPanel() {
  const { toast, setParete } = useG();
  const [p, setP] = useState<Preferenze>(leggiPreferenze());
  const salva = (n: Preferenze) => { setP(n); salvaPreferenze(n); toast('Preferenze salvate su questo dispositivo'); };
  return (<>
    <div className="card stack">
      <h3 className="section-title" style={{ margin: 0 }}>Voce</h3>
      {!supportoParlato && <p className="note">Questo browser non supporta la sintesi vocale: la voce resta disattivata.</p>}
      <label className="row"><input type="checkbox" checked={p.voce} disabled={!supportoParlato} onChange={(e) => salva({ ...p, voce: e.target.checked })} />
        Guardian legge ad alta voce risposte e annunci</label>
      <p className="dim" style={{ fontSize: 12, margin: 0 }}>Microfono: {supportoAscolto ? 'disponibile (il riconoscimento può passare dai server del browser).' : 'non supportato da questo browser.'}</p>
    </div>
    <DiagnosticaVoce />
    <div className="card stack">
      <h3 className="section-title" style={{ margin: 0 }}>Annunci</h3>
      <label className="field">Livello<select className="input" value={p.livello} onChange={(e) => salva({ ...p, livello: e.target.value as Preferenze['livello'] })}>
        <option value="silenzio">Silenzio</option><option value="critici">Solo critici (task falliti, agenti in errore)</option>
        <option value="importanti">Importanti (+ approvazioni, handoff verso di me)</option><option value="tutti">Tutti</option></select></label>
      <div className="grid2">
        <label className="field">Silenzio dalle<input className="input" type="time" value={p.silenzioDa} onChange={(e) => salva({ ...p, silenzioDa: e.target.value })} /></label>
        <label className="field">alle<input className="input" type="time" value={p.silenzioA} onChange={(e) => salva({ ...p, silenzioA: e.target.value })} /></label>
      </div>
      <p className="dim" style={{ fontSize: 12, margin: 0 }}>Al massimo 6 annunci vocali all'ora. Le preferenze restano su questo dispositivo.</p>
    </div>
    <div className="card stack">
      <h3 className="section-title" style={{ margin: 0 }}>Sfondo</h3>
      <div className="row" role="group" aria-label="Sfondo del Centro">{([['atlas', 'Atlas'], ['volto', 'Volto']] as const).map(([v, n]) => (
        <button key={v} className={`btn sm ${p.sfondo === v ? 'primary' : ''}`} aria-pressed={p.sfondo === v} onClick={() => salva({ ...p, sfondo: v })}>{n}</button>))}</div>
      <p className="dim" style={{ fontSize: 12, margin: 0 }}>Atlas: nucleo, stanze, agenti e task disegnati dai dati veri. Volto: l'immagine di NEXO Sentinel (le opzioni qui sotto valgono per il Volto).</p>
      <div className="row" role="group" aria-label="Volto 3D">{([['acceso', 'Animato'], ['immagine', 'Solo immagine'], ['spento', 'Spento']] as const).map(([v, n]) => (
        <button key={v} className={`btn sm ${p.volto === v ? 'primary' : ''}`} aria-pressed={p.volto === v} onClick={() => salva({ ...p, volto: v })}>{n}</button>))}</div>
      <div className="row" role="group" aria-label="Vetro dei pannelli">{([['forte', 'Vetro forte'], ['leggero', 'Vetro leggero'], ['spento', 'Pannelli opachi']] as const).map(([v, n]) => (
        <button key={v} className={`btn sm ${p.vetro === v ? 'primary' : ''}`} aria-pressed={p.vetro === v} onClick={() => salva({ ...p, vetro: v })}>{n}</button>))}</div>
      <p className="dim" style={{ fontSize: 12, margin: 0 }}>Il volto si anima solo con cose vere: richieste, voce, eventi. Sul telefono e con «riduci movimento» resta un'immagine con l'occhio che si illumina.</p>
    </div>
    <div className="card stack">
      <h3 className="section-title" style={{ margin: 0 }}>Suoni e parete</h3>
      <label className="row"><input type="checkbox" checked={p.suoni} onChange={(e) => { salva({ ...p, suoni: e.target.checked }); if (e.target.checked) suona('notifica', true); }} />
        Suoni discreti (notifiche, inizio e fine della conversazione)</label>
      <p className="dim" style={{ fontSize: 12, margin: 0 }}>Tacciono nell'orario di silenzio. Nessun file audio: sono note brevi generate dal browser.</p>
      <div><button className="btn sm" onClick={() => setParete(true)}>Apri la modalità parete</button></div>
      <p className="dim" style={{ fontSize: 12, margin: 0 }}>Per uno schermo grande in ufficio: solo lettura, scritte grandi. Indirizzo: <code>?parete=1</code>. Esc per uscire.</p>
    </div>
    <div className="card stack">
      <h3 className="section-title" style={{ margin: 0 }}>Colori delle stanze</h3>
      <div className="row">{(['accesa', 'soft'] as const).map((v) => (
        <button key={v} className={`btn sm ${p.coloriStanze === v ? 'primary' : ''}`} aria-pressed={p.coloriStanze === v}
          onClick={() => salva({ ...p, coloriStanze: v })}>{v === 'accesa' ? 'Accesa (dal database)' : 'Soft (più chiara)'}</button>))}</div>
      <p className="dim" style={{ fontSize: 12, margin: 0 }}>Solo su questo dispositivo. I colori «Accesa» li cambia l'admin nella tabella stanze.</p>
    </div>
    <p className="note">Provider AI, utenti e chiavi non si gestiscono da qui: nessuna chiave viene mai mostrata nel browser.</p>
  </>);
}
