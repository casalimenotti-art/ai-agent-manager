import { Activity, ArrowLeft, Bell, Bot, BookOpen, Building2, Cpu, GitBranchPlus, HeartPulse, LayoutDashboard, ListTodo, LogOut, Mic,
  MicOff, Network, Search, Send, Settings, ShieldCheck, Shuffle, Square, X, type LucideIcon } from 'lucide-react';
import { useEffect, useMemo, useRef, useState, type KeyboardEvent as KE } from 'react';
import { fa } from '../logic/status';
import { leggiPreferenze, useG, type Pannello } from '../state';
import { CommandCenter } from './CommandCenter';
import { BarraConversazione, PulsanteConversazione, useConversazione } from './Conversazione';
import { useRispondi } from './useRispondi';
import { PANNELLI, titoloPannello } from './panels';
import { ascolta, inSilenzio, parla, smettiDiAscoltare, supportoAscolto, supportoParlato, useVoce, zitto } from './voce';

export const NAV: { p: string; nome: string; icona: LucideIcon }[] = [
  { p: 'mappa', nome: 'Mappa', icona: Network }, { p: 'agenti', nome: 'Agenti', icona: Bot }, { p: 'aziende', nome: 'Aziende', icona: Building2 }, { p: 'tasks', nome: 'Task', icona: ListTodo },
  { p: 'approvazioni', nome: 'Approva', icona: ShieldCheck }, { p: 'memoria', nome: 'Memoria', icona: BookOpen },
  { p: 'handoff', nome: 'Handoff', icona: Shuffle }, { p: 'attivita', nome: 'Attività', icona: Activity },
  { p: 'statistiche', nome: 'Statistiche', icona: HeartPulse }, { p: 'workflow', nome: 'Workflow', icona: GitBranchPlus },
  { p: 'dispositivi', nome: 'PC', icona: Cpu }, { p: 'impostazioni', nome: 'Impostazioni', icona: Settings },
];

function Header() {
  const { user, snap, diretta, pingOk, pingMs, pingAl, caricato, apri, setPalette, esci, source } = useG();
  const nonLette = snap?.notifications.filter((n) => !n.read_at).length ?? 0;
  const salute = pingOk === false ? ['crit', 'Database non raggiungibile'] : pingOk ? ['ok', `Database ${Math.round(pingMs ?? 0)} ms`] : ['', 'Verifica…'];
  const aggiornamento = source.modo === 'demo' ? 'Dati locali' : diretta === 'live' ? 'Live' : `Polling 20 s${caricato ? ` · ${fa(new Date(caricato).toISOString())}` : ''}`;
  return (
    <header className="header">
      <div className="brand"><svg width="22" height="22" viewBox="0 0 32 32" aria-hidden><circle cx="16" cy="16" r="11" fill="none" stroke="#22d3ee" strokeWidth="2.5" />
        <circle cx="16" cy="16" r="4" fill="#22d3ee" /></svg>Guardian <small className="hide-sm">NEXO Command Center</small></div>
      <span className="spacer" />
      <button className={`pill ${salute[0]} hide-sm`} style={{ border: 0, cursor: 'pointer' }} onClick={() => apri({ p: 'salute' })}
        title={pingAl ? `Controllato ${fa(new Date(pingAl).toISOString())}` : undefined}><HeartPulse aria-hidden />{salute[1]}</button>
      <span className={`pill ${diretta === 'live' ? 'ok' : ''} hide-sm`} title="Come arrivano gli aggiornamenti">{aggiornamento}</span>
      <button className="btn ghost sm" onClick={() => setPalette(true)} aria-label="Cerca e comandi (Ctrl+K)"><Search size={16} aria-hidden />
        <span className="hide-sm">Cerca</span> <kbd className="hide-sm">Ctrl K</kbd></button>
      <button className="btn ghost icon rel" onClick={() => apri({ p: 'notifiche' })} aria-label={`Notifiche, ${nonLette} non lette`}>
        <Bell size={18} aria-hidden />{nonLette > 0 && <span className="badge">{nonLette}</span>}</button>
      <Presenti />
      <span className="hide-sm dim" style={{ fontSize: 13 }}>{user.nome}</span>
      <button className="btn ghost icon" onClick={esci} aria-label="Esci"><LogOut size={17} aria-hidden /></button>
    </header>
  );
}

function Presenti() {
  const { presenti, snap, user } = useG();
  if (!presenti.length) return null;
  const nomeStanza = (id: string | null) => (id ? snap?.stanze.find((s) => s.id === id)?.nome ?? id : 'Centro');
  const testo = presenti.map((p) => `${p.id === user.id ? 'Tu' : p.nome} (${nomeStanza(p.stanza)})`).join(', ');
  return (
    <span className="presenti hide-sm" role="status" aria-label={`Nell'HQ ora: ${testo}`} title={`Nell'HQ ora: ${testo}`}>
      {presenti.slice(0, 4).map((p) => <span key={p.id} className={`avatar${p.id === user.id ? ' io' : ''}`} aria-hidden>{p.nome.slice(0, 1).toUpperCase()}</span>)}
      {presenti.length > 4 && <span className="avatar" aria-hidden>+{presenti.length - 4}</span>}
    </span>
  );
}

function Rail() {
  const { pannello, apri, chiudi, stanza, apriStanza } = useG();
  useEffect(() => {
    const f = (e: KeyboardEvent) => { if (e.key === 'Escape' && !pannello && stanza && !document.querySelector('.palette')) apriStanza(null); };
    window.addEventListener('keydown', f); return () => window.removeEventListener('keydown', f);
  }, [pannello, stanza, apriStanza]);
  return (
    <nav className="rail" aria-label="Navigazione">
      <button onClick={() => { chiudi(); apriStanza(null); }} aria-current={!pannello && !stanza}><LayoutDashboard size={20} aria-hidden />Centro</button>
      {NAV.map((n) => (
        <button key={n.p} onClick={() => apri({ p: n.p })} aria-current={pannello?.p === n.p}><n.icona size={20} aria-hidden />{n.nome}</button>
      ))}
    </nav>
  );
}

function DrawerHost() {
  const { pannello, traccia, chiudi, indietro } = useG();
  const ritorno = useRef<HTMLElement | null>(null);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (pannello && !ritorno.current) ritorno.current = document.activeElement as HTMLElement;
    if (pannello) ref.current?.focus();
    if (!pannello && ritorno.current) { ritorno.current.focus?.(); ritorno.current = null; }
  }, [pannello]);
  useEffect(() => {
    const f = (e: KeyboardEvent) => { if (e.key === 'Escape' && pannello && !document.querySelector('.palette')) chiudi(); };
    window.addEventListener('keydown', f); return () => window.removeEventListener('keydown', f);
  }, [pannello, chiudi]);
  if (!pannello) return null;
  const def = PANNELLI[pannello.p];
  if (!def) return null;
  const Corpo = def.componente;
  const largo = window.matchMedia?.('(min-width: 1280px)').matches ?? false;
  return (<>
    <div className="scrim desk-hidden" onClick={chiudi} aria-hidden />
    <div className={`drawer ${def.largo ? 'lg' : ''}`} role="dialog" aria-modal={!largo} aria-label={titoloPannello(pannello)} tabIndex={-1} ref={ref}>
      <header>
        {traccia.length > 1 && <button className="btn ghost icon" onClick={indietro} aria-label="Indietro"><ArrowLeft size={18} aria-hidden /></button>}
        <h2>{titoloPannello(pannello)}</h2>
        <button className="btn ghost icon" onClick={chiudi} aria-label="Chiudi pannello"><X size={18} aria-hidden /></button>
      </header>
      {traccia.length > 1 && <div className="crumbs">{traccia.map((t) => titoloPannello(t)).join(' › ')}</div>}
      <div className="body"><Corpo {...pannello} key={`${pannello.p}-${pannello.id}-${pannello.filtro}`} /></div>
    </div>
  </>);
}

function Dock() {
  const { pannello, messaggi, stanza } = useG();
  const voce = useVoce();
  const [testo, setTesto] = useState('');
  const [aperta, setAperta] = useState(false);
  const fine = useRef<HTMLDivElement>(null);
  useEffect(() => { fine.current?.scrollIntoView({ block: 'end' }); }, [messaggi.length]);

  const rispondi = useRispondi();
  const conv = useConversazione();
  const chiedi = async (q: string) => {
    if (!q.trim()) return;
    setAperta(true); setTesto('');
    const r = await rispondi(q);
    let t = '';
    if (typeof r === 'string') t = r; else { const parti: string[] = []; for await (const f of r) parti.push(f); t = parti.join(' '); }
    if (t && conv.fase === 'spento' && leggiPreferenze().voce) parla(t);
  };
  useEffect(() => {
    const f = (e: Event) => chiedi((e as CustomEvent<string>).detail);
    window.addEventListener('guardian:chiedi', f); return () => window.removeEventListener('guardian:chiedi', f);
  });

  return (
    <div className="dock">
      <BarraConversazione />
      {aperta && messaggi.length > 0 && (
        <div className="convo" role="log" aria-label="Conversazione con Guardian">
          {messaggi.map((m, i) => <div key={i} className={`msg ${m.da}`}>{m.testo}{m.fonte && <span className="src">Fonte: {m.fonte}</span>}</div>)}
          <div ref={fine} />
        </div>)}
      <form className="bar" onSubmit={(e) => { e.preventDefault(); chiedi(testo); }}>
        <input value={testo} onChange={(e) => setTesto(e.target.value)} placeholder={pannello ? 'Chiedi a Guardian su questo pannello…' : stanza ? 'Chiedi a Guardian su questa stanza…' : 'Chiedi a Guardian: «apri vendite», «cosa è bloccato?»'}
          aria-label="Messaggio per Guardian" onFocus={() => setAperta(true)} />
        {messaggi.length > 0 && <button type="button" className="btn ghost sm" onClick={() => setAperta((a) => !a)} aria-expanded={aperta}>
          {aperta ? 'Nascondi' : `Conversazione (${messaggi.length})`}</button>}
        {voce.parla && <button type="button" className="btn ghost icon" onClick={zitto} aria-label="Interrompi la voce"><Square size={16} aria-hidden /></button>}
        <PulsanteConversazione compatto />
        <button type="button" className={`btn icon ${voce.ascolta ? 'mic-on' : ''}`} disabled={!supportoAscolto}
          title={supportoAscolto ? (voce.ascolta ? 'Smetti di ascoltare' : 'Parla con Guardian (il riconoscimento può passare dai server del browser)')
            : 'Voce non disponibile: questo browser non supporta il riconoscimento vocale'}
          aria-label={voce.ascolta ? 'Smetti di ascoltare' : 'Parla con Guardian'} aria-pressed={voce.ascolta}
          onClick={() => (voce.ascolta ? smettiDiAscoltare() : ascolta(chiedi))}>
          {voce.ascolta ? <MicOff size={18} aria-hidden /> : <Mic size={18} aria-hidden />}</button>
        <button type="submit" className="btn primary icon" aria-label="Invia" disabled={!testo.trim()}><Send size={17} aria-hidden /></button>
      </form>
      {voce.errore && <div className="err" style={{ marginTop: 6 }}>{voce.errore}</div>}
    </div>
  );
}

interface Voce { gruppo: string; nome: string; azione: () => void; icona: LucideIcon }
function Palette() {
  const { snap, paletteAperta, setPalette, apri, chiudi, apriStanza } = useG();
  const [q, setQ] = useState(''); const [sel, setSel] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const f = (e: KeyboardEvent) => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setPalette(true); } };
    window.addEventListener('keydown', f); return () => window.removeEventListener('keydown', f);
  }, [setPalette]);
  useEffect(() => { if (paletteAperta) { setQ(''); setSel(0); } }, [paletteAperta]);
  const voci = useMemo<Voce[]>(() => {
    const v: Voce[] = [
      { gruppo: 'Azioni', nome: 'Torna al Command Center', azione: () => { chiudi(); apriStanza(null); }, icona: LayoutDashboard },
      { gruppo: 'Azioni', nome: 'Nuovo task', azione: () => apri({ p: 'tasks', filtro: 'nuovo' }), icona: ListTodo },
      { gruppo: 'Azioni', nome: 'Task bloccati o falliti', azione: () => apri({ p: 'tasks', filtro: 'fermi' }), icona: ListTodo },
      { gruppo: 'Azioni', nome: 'Riepilogo di oggi', azione: () => window.dispatchEvent(new CustomEvent('guardian:chiedi', { detail: 'Fammi un riepilogo della giornata' })), icona: HeartPulse },
      ...NAV.map((n) => ({ gruppo: 'Sezioni', nome: n.nome === 'Approva' ? 'Approvazioni' : n.nome === 'PC' ? 'Dispositivi (PC)' : n.nome, azione: () => apri({ p: n.p }), icona: n.icona })),
    ];
    if (snap) {
      v.push(...snap.stanze.map((st) => ({ gruppo: 'Stanze', nome: `Stanza ${st.nome}`, azione: () => { chiudi(); apriStanza(st.id); }, icona: LayoutDashboard })));
      v.push(...snap.agents.map((a) => ({ gruppo: 'Agenti', nome: `${a.nome} · ${a.id}`, azione: () => apri({ p: 'agente', id: a.id }), icona: Bot })));
      v.push(...snap.projects.map((p) => ({ gruppo: 'Aziende', nome: p.nome, azione: () => apri({ p: 'azienda', id: String(p.id) }), icona: Building2 })));
      v.push(...snap.tasks.slice(0, 200).map((t) => ({ gruppo: 'Task', nome: `#${t.id} ${t.titolo}`, azione: () => apri({ p: 'task', id: String(t.id) }), icona: ListTodo })));
      v.push(...snap.approvals.filter((a) => a.status === 'richiesta').map((a) => ({ gruppo: 'Approvazioni', nome: a.action,
        azione: () => apri({ p: 'approvazione', id: String(a.id) }), icona: ShieldCheck })));
    }
    return v;
  }, [snap, apri, chiudi, apriStanza]);
  if (!paletteAperta) return null;
  const parole = q.toLowerCase().split(/\s+/).filter(Boolean);
  const trovate = voci.filter((v) => parole.every((p) => `${v.gruppo} ${v.nome}`.toLowerCase().includes(p))).slice(0, 30);
  const tutte: Voce[] = q.trim() ? [...trovate, { gruppo: 'Guardian', nome: `Chiedi a Guardian: «${q.trim()}»`, icona: Search,
    azione: () => window.dispatchEvent(new CustomEvent('guardian:chiedi', { detail: q.trim() })) }] : trovate;
  const esegui = (v?: Voce) => { if (!v) return; setPalette(false); v.azione(); };
  const tasti = (e: KE) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setSel((s) => Math.min(s + 1, tutte.length - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setSel((s) => Math.max(s - 1, 0)); }
    if (e.key === 'Enter') { e.preventDefault(); esegui(tutte[sel]); }
    if (e.key === 'Escape') { e.preventDefault(); setPalette(false); }
  };
  let gruppo = '';
  return (<>
    <div className="scrim" style={{ zIndex: 69 }} onClick={() => setPalette(false)} aria-hidden />
    <div className="palette" role="dialog" aria-modal="true" aria-label="Cerca e comandi">
      <input ref={input} autoFocus value={q} onChange={(e) => { setQ(e.target.value); setSel(0); }} onKeyDown={tasti} placeholder="Cerca agenti, task, aziende… o scrivi una domanda"
        role="combobox" aria-expanded="true" aria-controls="palette-lista" aria-activedescendant={`pv-${sel}`} />
      <ul id="palette-lista" role="listbox">
        {tutte.length === 0 && <li className="dim">Nessun risultato</li>}
        {tutte.map((v, i) => {
          const titolo = v.gruppo !== gruppo ? v.gruppo : null; gruppo = v.gruppo;
          return (<div key={`${v.gruppo}-${v.nome}-${i}`}>{titolo && <div className="grp">{titolo}</div>}
            <li id={`pv-${i}`} role="option" aria-selected={i === sel} onMouseEnter={() => setSel(i)} onClick={() => esegui(v)}>
              <v.icona size={15} aria-hidden />{v.nome}</li></div>);
        })}
      </ul>
      <div className="row dim" style={{ padding: '8px 14px', fontSize: 11, borderTop: '1px solid var(--border-1)' }}>
        <kbd>↑</kbd><kbd>↓</kbd> scegli · <kbd>Invio</kbd> apri · <kbd>Esc</kbd> chiudi</div>
    </div>
  </>);
}

function Annunci() {
  const { snap, toast, apri } = useG();
  const visti = useRef<Set<number> | null>(null);
  const perOra = useRef<number[]>([]);
  useEffect(() => {
    if (!snap) return;
    const nonLette = snap.notifications.filter((n) => !n.read_at);
    if (visti.current === null) { visti.current = new Set(nonLette.map((n) => n.id)); return; }
    const pref = leggiPreferenze();
    for (const n of nonLette) {
      if (visti.current.has(n.id)) continue;
      visti.current.add(n.id);
      const critica = ['task_failed', 'agent_error'].includes(n.kind);
      const importante = critica || ['approval_requested', 'handoff_to_you'].includes(n.kind);
      const ok = pref.livello === 'tutti' || (pref.livello === 'importanti' && importante) || (pref.livello === 'critici' && critica);
      if (!ok) continue;
      toast(n.message, critica);
      perOra.current = perOra.current.filter((t) => Date.now() - t < 3_600_000);
      if (pref.voce && supportoParlato && !inSilenzio(pref.silenzioDa, pref.silenzioA) && perOra.current.length < 6) { perOra.current.push(Date.now()); parla(n.message); }
    }
  }, [snap, toast, apri]);
  return null;
}

function Toasts() {
  const { toasts } = useG();
  return <div className="toasts" role="status" aria-live="polite">{toasts.map((t) => <div key={t.id} className={`toast ${t.errore ? 'err' : ''}`}>{t.testo}</div>)}</div>;
}

export function Shell() {
  const { source, pannello } = useG();
  const classi = ['shell', pannello && PANNELLI[pannello.p] ? 'con-pannello' : '', pannello && PANNELLI[pannello.p]?.largo ? 'pannello-lg' : ''].join(' ');
  return (
    <div className={classi}>
      <Header />
      <Rail />
      <main className="main" id="centro"><CommandCenter /></main>
      {source.modo === 'demo' && <div className="demo-banner" role="note">Dati di esempio — solo locale</div>}
      <DrawerHost />
      <Dock />
      <Palette />
      <Annunci />
      <Toasts />
    </div>
  );
}

export type { Pannello };
