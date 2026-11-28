// Pannello Dispositivi (solo admin): elenco PC, "Registra PC" con codice mostrato una volta, revoca.
import { Check, Copy, Cpu, KeyRound, Plus } from 'lucide-react';
import { useState } from 'react';
import { erroreNomePc, hashCodice, nuovoCodice, pcOnline, validaNomePc } from '../../logic/dispositivi';
import { fa } from '../../logic/status';
import { useG } from '../../state';
import { Scheletro, Vuoto } from '../kit';
import { DispositiviPanel } from './sistema';

export function DispositiviAdminPanel() {
  const { snap, source, user, esegui, toast } = useG();
  const [nome, setNome] = useState('');
  const [persona, setPersona] = useState(user.id);
  const [toccato, setToccato] = useState(false);
  const [codice, setCodice] = useState<{ nome: string; valore: string } | null>(null);
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
          ? <><button className="btn" type="button" onClick={async () => { await esegui(async () => { await source.revocaPc(d.id, await hashCodice(nuovoCodice()), user.id); return true; }, 'PC revocato'); setDaRevocare(null); }}>Conferma revoca</button>
            <button className="btn" type="button" onClick={() => setDaRevocare(null)}>Annulla</button></>
          : <button className="btn" type="button" aria-label={`Revoca ${d.nome}`} onClick={() => setDaRevocare(d.id)}>Revoca</button>}
      </div>);
    })}</div>}
  </div>);
}
