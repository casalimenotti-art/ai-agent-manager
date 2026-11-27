import { useCallback, useEffect, useState } from 'react';
import { creaFonte } from './data';
import type { DataSource } from './data/source';
import { GuardianProvider } from './state';
import type { User } from './types';
import { Shell } from './ui/Shell';

const conf = creaFonte();

function Login({ source, onEntra }: { source: DataSource; onEntra: (u: User) => void }) {
  const [email, setEmail] = useState(''); const [pw, setPw] = useState(''); const [err, setErr] = useState(''); const [occupato, setOccupato] = useState(false);
  return (
    <div className="login"><form className="card" onSubmit={async (e) => {
      e.preventDefault(); setOccupato(true); setErr('');
      try { onEntra(await source.accedi(email, pw)); } catch (x) { setErr(x instanceof Error ? x.message : 'Accesso non riuscito'); } finally { setOccupato(false); }
    }}>
      <div className="brand" style={{ fontSize: 16 }}>Guardian <small>NEXO Command Center</small></div>
      <p className="muted" style={{ margin: 0 }}>Accesso riservato ai collaboratori di NEXO.</p>
      {source.modo === 'demo' && <p className="note">Modalità dati di esempio (solo locale): entra con qualsiasi email, es. «menotti».</p>}
      <label className="field">Email<input className="input" type={source.modo === 'demo' ? 'text' : 'email'} autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} /></label>
      {source.modo !== 'demo' && <label className="field">Password<input className="input" type="password" autoComplete="current-password" required value={pw} onChange={(e) => setPw(e.target.value)} /></label>}
      {err && <div className="err" role="alert">{err}</div>}
      <button className="btn primary" type="submit" disabled={occupato}>{occupato ? 'Accesso…' : 'Entra'}</button>
    </form></div>
  );
}

export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [pronto, setPronto] = useState(false);
  useEffect(() => {
    if ('errore' in conf) { setPronto(true); return; }
    conf.source.utente().then(setUser).catch(() => setUser(null)).finally(() => setPronto(true));
  }, []);
  const esci = useCallback(() => { if ('source' in conf) void conf.source.esci(); setUser(null); }, []);
  if ('errore' in conf) return <div className="login"><div className="card"><b>Guardian non configurato</b><p className="err">{conf.errore}</p></div></div>;
  if (!pronto) return <div className="login" aria-busy="true"><div className="skeleton" style={{ width: 200 }} /></div>;
  if (!user) return <Login source={conf.source} onEntra={setUser} />;
  return <GuardianProvider source={conf.source} user={user} onEsci={esci}><Shell /></GuardianProvider>;
}
