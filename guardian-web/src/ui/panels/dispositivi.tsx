// Pannello Dispositivi (solo admin): elenco PC, "Registra PC" con codice mostrato una volta, revoca.
import { Check, Copy, Cpu, KeyRound, Plus } from 'lucide-react';
import { useState } from 'react';
import { erroreNomePc, hashCodice, nuovoCodice, pcOnline, validaNomePc } from '../../logic/dispositivi';
import { fa, statoAgente, statoDispositivo } from '../../logic/status';
import { useG, type Pannello } from '../../state';
import { Scheletro, Vuoto } from '../kit';
import { DispositiviPanel } from './sistema';

// Il codice resta in memoria finché la persona non preme "Ho copiato": un aggiornamento dei dati o la riapertura del pannello non lo fa sparire
// (solo in memoria della scheda, mai salvato: un ricaricamento della pagina lo cancella).
let codiceInSospeso: { nome: string; valore: string } | null = null;

export function DispositiviAdminPanel() {
  const { snap, source, user, esegui, toast } = useG();
  const [nome, setNome] = useState('');
  const [persona, setPersona] = useState(user.id);
  const [toccato, setToccato] = useState(false);
  const [codice, setCodiceStato] = useState<{ nome: string; valore: string } | null>(() => codiceInSospeso);
  const setCodice = (c: { nome: string; valore: string } | null) => { codiceInSospeso = c; setCodiceStato(c); };
  const [copiato, setCopiato] = useState(false);
  const [occupato, setOccupato] = useState(false);
  const [daRevocare, setDaRevocare] = useState<number | null>(null);

  if (user.accesso !== 'admin') return <DispositiviPanel />; // i non admin vedono solo l'elenco
  if (!snap) return <Scheletro />;
  const errore = toccato ? erroreNomePc(nome) : null;

  async function registra(e: React.FormEvent) {
    e.preventDefault(); setToccato(true);
    if (erroreNomePc(nome) || occupato) return;
    setOccupato(true);
    const valore = nuovoCodice();
    const pulito = validaNomePc(nome);
    const ok = await esegui(async () => { await source.registraPc(persona, pulito, await hashCodice(valore), user.id); return true; }, 'PC registrato');
    setOccupato(false);
    if (ok) { setCodice({ nome: pulito, valore }); setCopiato(false); setNome(''); setToccato(false); }
  }
  async function copia() {
    if (!codice) return;
    try { await navigator.clipboard.writeText(codice.valore); setCopiato(true); toast('Codice copiato'); }
    catch { setCopiato(false); toast('Copia non riuscita: selezionalo a mano'); }
  }

  return (<div className="stack">
    {codice && <section className="card stack" role="alert" aria-label="Codice dispositivo">
      <h3 className="section-title"><KeyRound size={15} aria-hidden />Codice per «{codice.nome}»</h3>
      <code style={{ wordBreak: 'break-all', userSelect: 'all' }}>{codice.valore}</code>
      <p className="note"><strong>Copialo ora: non verrà più mostrato.</strong> Incollalo in <code>bridge/.env</code> come GUARDIAN_DEVICE_TOKEN (vedi docs/collega-pc.md).</p>
      <div className="row">
        <button className="btn primary" type="button" onClick={() => void copia()}>{copiato ? <Check size={15} aria-hidden /> : <Copy size={15} aria-hidden />} {copiato ? 'Copiato' : 'Copia'}</button>
        <button className="btn" type="button" onClick={() => setCodice(null)}>Ho copiato, chiudi</button>
      </div>
    </section>}

    <form className="card stack" onSubmit={(e) => void registra(e)} noValidate aria-label="Registra PC">
      <h3 className="section-title"><Plus size={15} aria-hidden />Registra PC</h3>
      <label className="field">Nome del PC *
        <input className="input" value={nome} maxLength={80} placeholder="es. PC-Menotti" aria-invalid={!!errore} aria-describedby={errore ? 'pc-err' : undefined}
          onChange={(e) => setNome(e.target.value)} onBlur={() => setToccato(true)} />
        {errore && <span id="pc-err" className="note" role="alert">{errore}</span>}
      </label>
      <label className="field">Persona
        <select className="input" value={persona} onChange={(e) => setPersona(e.target.value)}>
          {snap.users.filter((u) => u.stato === 'attivo').map((u) => <option key={u.id} value={u.id}>{u.nome}</option>)}
        </select>
      </label>
      <button className="btn primary" type="submit" disabled={occupato}>Registra PC</button>
    </form>

    {snap.devices.length === 0 ? <Vuoto icona={Cpu}>Nessun PC registrato.</Vuoto> : <div className="list">{snap.devices.map((d) => {
      const on = pcOnline(d.last_seen);
      return (<div key={d.id} className="item static"><Cpu size={18} aria-hidden /><div style={{ flex: 1 }}><div className="t">{d.nome}</div>
        <div className="s">{snap.users.find((u) => u.id === d.user_id)?.nome ?? d.user_id} · ultimo segnale {fa(d.last_seen)}</div></div>
        <span className={`pill ${on ? 'ok' : ''}`}>{on ? 'online' : 'offline'}</span>
        {daRevocare === d.id
          ? <><button className="btn" type="button" onClick={async () => { await esegui(async () => { await source.revocaPc(d.id, await hashCodice(nuovoCodice()), user.id, d.nome); return true; }, 'PC revocato'); setDaRevocare(null); }}>Conferma revoca</button>
            <button className="btn" type="button" onClick={() => setDaRevocare(null)}>Annulla</button></>
          : <button className="btn" type="button" aria-label={`Revoca ${d.nome}`} onClick={() => setDaRevocare(d.id)}>Revoca</button>}
      </div>);
    })}</div>}
  </div>);
}

/** Scheda in sola lettura del PC selezionato dalla scena. Mostra solo campi presenti nello snapshot. */
export function MacchinaPanel({ id }: Pannello) {
  const { snap, apri } = useG();
  if (!snap) return <Scheletro />;
  const device = snap.devices.find((d) => String(d.id) === id);
  if (!device) return <Vuoto icona={Cpu}>Questo PC non è più registrato.</Vuoto>;
  const unSoloPc = snap.devices.filter((d) => d.user_id === device.user_id).length === 1;
  const agents = snap.agents.filter((a) => a.device_id === device.id || (!a.device_id && unSoloPc && a.user_id === device.user_id));
  const taskId = device.current_task_id ?? agents.find((a) => a.current_task_id != null)?.current_task_id;
  const task = taskId == null ? undefined : snap.tasks.find((t) => t.id === taskId);
  const attivita = agents.map((a) => a.last_activity).filter((s): s is string => !!s).sort((a, b) => Date.parse(b) - Date.parse(a))[0] ?? device.last_seen;
  const stato = statoDispositivo(device);
  return <section className="stack machine-detail" aria-label={`Dettagli ${device.nome}`}>
    <div className="machine-detail-status"><span className="machine-star-point" aria-hidden="true" /><strong>{stato === 'online' ? 'Collegato' : stato === 'offline' ? 'Scollegato' : stato === 'error' || stato === 'errore' ? 'Errore' : stato}</strong></div>
    <dl>
      <div><dt>PC</dt><dd>{device.nome}</dd></div>
      <div><dt>Persona</dt><dd>{snap.users.find((u) => u.id === device.user_id)?.nome ?? device.user_id}</dd></div>
      <div><dt>Agenti</dt><dd>{agents.length ? agents.map((a) => <button key={a.id} className="link-t" type="button" onClick={() => apri({ p: 'agente', id: a.id })}>{a.nome} · {statoAgente(a)}</button>) : 'Nessun agente associato'}</dd></div>
      <div><dt>Task corrente</dt><dd>{task ? <button className="link-t" type="button" onClick={() => apri({ p: 'task', id: String(task.id) })}>#{task.id} {task.titolo}</button> : 'Nessun task associato'}</dd></div>
      <div><dt>Ultima attività</dt><dd>{attivita ? fa(attivita) : 'Non disponibile'}</dd></div>
      {device.last_checkpoint && <div><dt>Ultimo checkpoint</dt><dd>{fa(device.last_checkpoint)}</dd></div>}
    </dl>
  </section>;
}
