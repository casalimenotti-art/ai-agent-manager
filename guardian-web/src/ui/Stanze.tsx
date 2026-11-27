// Le tre stanze dell'HQ attorno a Guardian: vista "orbita" (riepiloghi) e stanza espansa (lavoro), senza cambiare pagina.
import { ArrowLeft, Bot, MessageSquare, Plus, ShieldCheck } from 'lucide-react';
import { useState, type CSSProperties, type DragEvent } from 'react';
import { COLONNE_KANBAN, COLORI_SOFT, riepilogoStanza, taskDiStanza } from '../logic/stanze';
import { fa, statoAgente } from '../logic/status';
import { leggiPreferenze, useG } from '../state';
import { LavoroStanza } from './StanzeLavoro';
import type { Stanza, TaskStato } from '../types';
import { Sezione, StatoAgente, StatoTask, Vuoto } from './kit';

export function coloreStanza(st: Stanza) {
  return leggiPreferenze().coloriStanze === 'soft' ? (COLORI_SOFT[st.id] ?? st.colore) : st.colore;
}
const stile = (st: Stanza) => ({ '--stanza': coloreStanza(st) }) as CSSProperties;

export function OrbitaStanze() {
  const { snap, apriStanza } = useG();
  if (!snap) return null;
  if (snap.stanze.length === 0) return (
    <section className="card col-12" aria-label="Stanze"><Vuoto>Le stanze non sono ancora configurate: esegui la migrazione 005 (supabase/migrations/005_stanze.sql).</Vuoto></section>);
  return (
    <section className="orbita col-12" aria-label="Le stanze dell'HQ">
      {snap.stanze.map((st) => {
        const r = riepilogoStanza(st, snap);
        return (
          <button key={st.id} className="porta" style={stile(st)} onClick={() => apriStanza(st.id)} aria-label={`Apri la stanza ${st.nome}`}>
            <div className="row between"><span className="porta-nome">{st.nome}</span>
              <span className="dim" style={{ fontSize: 12 }}>{snap.users.find((u) => u.id === st.responsabile)?.nome ?? st.responsabile ?? '—'}</span></div>
            <div className="porta-agenti">
              {r.agenti.length === 0 ? <span className="dim" style={{ fontSize: 12 }}>Nessun agente collegato</span> :
                r.agenti.map((a) => <span key={a.id} className="row" style={{ gap: 6 }}><Bot size={14} aria-hidden />{a.nome}<StatoAgente s={statoAgente(a)} /></span>)}
            </div>
            <div className="porta-numeri">
              <span><b className="mono">{r.attivi}</b> attivi</span><span><b className="mono">{r.inEsecuzione}</b> in corso</span>
              <span className={r.fermi ? 'warn-t' : ''}><b className="mono">{r.fermi}</b> fermi</span>
              <span className={r.approvazioni ? 'warn-t' : ''}><b className="mono">{r.approvazioni}</b> da approvare</span>
            </div>
            <div className="dim porta-ultimo">{r.ultimoEvento ? `${fa(r.ultimoEvento.timestamp)} · ${r.ultimoEvento.message}` : 'Nessun evento recente'}</div>
          </button>);
      })}
    </section>
  );
}

export function VistaStanza({ id }: { id: string }) {
  const { snap, source, ottimistico, user, apri, apriStanza } = useG();
  const [trascinato, setTrascinato] = useState<number | null>(null);
  const [sopra, setSopra] = useState<string | null>(null);
  if (!snap) return null;
  const st = snap.stanze.find((x) => x.id === id);
  if (!st) return <Vuoto>Stanza non trovata. <button className="btn sm" onClick={() => apriStanza(null)}>Torna al centro</button></Vuoto>;
  const r = riepilogoStanza(st, snap); const ts = taskDiStanza(st, snap); const ids = new Set(ts.map((t) => t.id));
  const sposta = (taskId: number, stato: TaskStato) => {
    const t = ts.find((x) => x.id === taskId);
    if (t && t.stato !== stato) void ottimistico(
      (s) => ({ ...s, tasks: s.tasks.map((x) => (x.id === taskId ? { ...x, stato, updated_at: new Date().toISOString() } : x)) }),
      () => source.modificaTask(taskId, { stato }, user.id), `Task #${taskId} → ${stato}`);
  };
  const drop = (e: DragEvent, dest: TaskStato) => { e.preventDefault(); setSopra(null); if (trascinato) sposta(trascinato, dest); setTrascinato(null); };
  const approvazioni = snap.approvals.filter((a) => a.status === 'richiesta' && a.task_id && ids.has(a.task_id));
  const eventi = snap.events.filter((e) => (e.task_id && ids.has(e.task_id)) || r.agenti.some((a) => a.id === e.agent_id)).slice(0, 8);
  const chiedi = () => window.dispatchEvent(new CustomEvent('guardian:chiedi', { detail: `Cosa succede in questa stanza?` }));
  return (
    <div className="stanza" style={stile(st)} aria-label={`Stanza ${st.nome}`}>
      <header className="stanza-testa">
        <button className="btn ghost icon" onClick={() => apriStanza(null)} aria-label="Torna al centro"><ArrowLeft size={18} aria-hidden /></button>
        <div className="stanza-titolo"><h2>{st.nome}</h2><div className="dim" style={{ fontSize: 13 }}>{st.descrizione}</div></div>
        <button className="btn" onClick={chiedi}><MessageSquare size={16} aria-hidden />Chiedi a Guardian</button>
        <button className="btn primary" onClick={() => apri({ p: 'tasks', filtro: 'nuovo' })}><Plus size={16} aria-hidden />Nuovo task</button>
      </header>
      <div className="porta-numeri" style={{ marginBottom: 4 }}>
        <span><b className="mono">{r.attivi}</b> attivi</span><span><b className="mono">{r.inEsecuzione}</b> in corso</span>
        <span><b className="mono">{r.fermi}</b> fermi</span><span><b className="mono">{r.completati}</b> completati</span>
      </div>
      <div className="kanban" role="list" aria-label="Lavagna dei task">
        {COLONNE_KANBAN.map((c) => {
          const lista = ts.filter((t) => (c.stati as readonly string[]).includes(t.stato));
          return (
            <div key={c.id} role="listitem" className={`colonna ${sopra === c.id ? 'sopra' : ''}`} onDragOver={(e) => { e.preventDefault(); setSopra(c.id); }}
              onDragLeave={() => setSopra(null)} onDrop={(e) => drop(e, c.destinazione)} data-colonna={c.id}>
              <h3 className="section-title">{c.nome} <span className="count">{lista.length}</span></h3>
              {lista.length === 0 && <div className="dim" style={{ fontSize: 12, padding: 8 }}>Trascina qui</div>}
              {lista.map((t) => (
                <article key={t.id} className="scheda" draggable onDragStart={() => setTrascinato(t.id)} onDragEnd={() => setTrascinato(null)} data-task={t.id}>
                  <button className="link-t" onClick={() => apri({ p: 'task', id: String(t.id) })}>#{t.id} {t.titolo}</button>
                  <div className="row between" style={{ marginTop: 6 }}><StatoTask s={t.stato} /><span className="dim" style={{ fontSize: 11 }}>{t.priorita}</span></div>
                  <label className="sr-only" htmlFor={`sposta-${t.id}`}>Sposta il task {t.id}</label>
                  <select id={`sposta-${t.id}`} className="input sposta" value="" onChange={(e) => sposta(t.id, e.target.value as TaskStato)}>
                    <option value="">Sposta in…</option>
                    {COLONNE_KANBAN.filter((x) => x.id !== c.id).map((x) => <option key={x.id} value={x.destinazione}>{x.nome}</option>)}
                  </select>
                </article>))}
            </div>);
        })}
      </div>
      <p className="dim" style={{ fontSize: 12, margin: 0 }}>Trascinare un task cambia davvero il suo stato. Il database rifiuta i passaggi non validi (es. dipendenze aperte) e te lo dice.</p>
      <LavoroStanza st={st} />
      <div className="cc">
        <Sezione titolo="Agenti della stanza" icona={Bot} conta={r.agenti.length} className="col-4">
          {r.agenti.length === 0 ? <Vuoto icona={Bot}>Nessun agente collegato a {snap.users.find((u) => u.id === st.responsabile)?.nome ?? 'questa stanza'}.</Vuoto> :
            <div className="list">{r.agenti.map((a) => (
              <button key={a.id} className="item" onClick={() => apri({ p: 'agente', id: a.id })}><div style={{ flex: 1 }}><div className="t">{a.nome}</div>
                <div className="s">ultimo segnale {fa(a.last_heartbeat)}</div></div><StatoAgente s={statoAgente(a)} /></button>))}</div>}
        </Sezione>
        <Sezione titolo="Da approvare" icona={ShieldCheck} conta={approvazioni.length} className="col-4">
          {approvazioni.length === 0 ? <Vuoto icona={ShieldCheck}>Niente da approvare qui.</Vuoto> :
            <div className="list">{approvazioni.map((a) => (
              <button key={a.id} className="item" onClick={() => apri({ p: 'approvazione', id: String(a.id) })}><div className="t">{a.action}</div></button>))}</div>}
        </Sezione>
        <Sezione titolo="Attività della stanza" className="col-4">
          {eventi.length === 0 ? <Vuoto>Nessun evento.</Vuoto> :
            <div className="list">{eventi.map((e) => <div key={e.id} className="item static"><div><div className="t" style={{ fontWeight: 500 }}>{e.message}</div>
              <div className="s">{fa(e.timestamp)}</div></div></div>)}</div>}
        </Sezione>
      </div>
    </div>
  );
}
