// Ondate 5 e 7: pannelli di lavoro delle stanze Vendite (pipeline) e Amministrazione (scadenze, costi).
// Solo dati inseriti a mano con fonte; niente dati personali dei clienti (li rifiutano sia il browser sia il DB).
import { CalendarClock, Plus, Receipt, TrendingUp } from 'lucide-react';
import { useState } from 'react';
import { costoMese, euro, giorniA, pipelinePerFase, scadenzeDaGuardare } from '../logic/amministrazione';
import { useG } from '../state';
import { FASI_VENDITA, type CategoriaCosto, type FaseVendita, type Ricorrenza, type Stanza, type TipoScadenza } from '../types';
import { Sezione, Vuoto } from './kit';

export const NOMI_FASE: Record<FaseVendita, string> = { contatto: 'Contatto', visita: 'Visita', proposta: 'Proposta', trattativa: 'Trattativa', vinto: 'Vinto', perso: 'Perso' };
const NOMI_CATEGORIA: Record<CategoriaCosto, string> = { software: 'Software', abbonamenti_ai: 'Abbonamenti AI', hosting: 'Hosting e domini', marketing: 'Marketing', trasporti: 'Trasporti', altro: 'Altro' };
const NOMI_RICORRENZA: Record<Ricorrenza, string> = { una_tantum: 'Una tantum', mensile: 'Mensile', annuale: 'Annuale' };
const TIPI_SCADENZA: TipoScadenza[] = ['fiscale', 'contratto', 'pagamento', 'documento', 'altro'];
const AVVISO = 'Mai telefoni, email o nomi di persone: quelli restano nel CSV dei lead.';
const numero = (v: string) => (v.trim() ? Number(v.replace(',', '.')) : null);

export function LavoroStanza({ st }: { st: Stanza }) {
  if (st.id === 'vendite') return <Pipeline />;
  if (st.id === 'amministrazione') return <div className="cc"><Scadenze /><Costi /></div>;
  return null;
}

function Pipeline() {
  const { snap, source, esegui, user } = useG();
  const [nuova, setNuova] = useState(false);
  const [f, setF] = useState({ azienda: '', fase: 'contatto' as FaseVendita, valore: '', passo: '', fonte: '' });
  if (!snap) return null;
  const p = pipelinePerFase(snap.vendite);
  const salva = async () => {
    const ok = await esegui(async () => { await source.creaVendita({ azienda: f.azienda, fase: f.fase, valore_eur: numero(f.valore), prossimo_passo: f.passo, fonte: f.fonte }, user.id); return true; }, 'Aggiunta alla pipeline');
    if (ok) { setNuova(false); setF({ azienda: '', fase: 'contatto', valore: '', passo: '', fonte: '' }); }
  };
  return (
    <Sezione titolo="Pipeline vendite" icona={TrendingUp} conta={snap.vendite.length} className="col-12 pipeline"
      azione={<button className="btn sm" onClick={() => setNuova(!nuova)}><Plus size={14} aria-hidden />{nuova ? 'Chiudi' : 'Aggiungi'}</button>}>
      <div className="porta-numeri">
        <span><b className="mono">{p.aperte}</b> aperte</span><span><b className="mono">{euro(p.valoreAperto)}</b> in ballo</span>
        <span><b className="mono">{p.tassoVittoria === null ? '—' : `${p.tassoVittoria}%`}</b> vinte sulle chiuse</span>
      </div>
      {nuova && (
        <form className="stack" style={{ margin: '12px 0' }} onSubmit={(e) => { e.preventDefault(); void salva(); }}>
          <div className="grid2">
            <label className="field">Azienda o codice del lead *<input className="input" required value={f.azienda} onChange={(e) => setF({ ...f, azienda: e.target.value })} /></label>
            <label className="field">Fase<select className="input" value={f.fase} onChange={(e) => setF({ ...f, fase: e.target.value as FaseVendita })}>
              {FASI_VENDITA.map((x) => <option key={x} value={x}>{NOMI_FASE[x]}</option>)}</select></label>
            <label className="field">Valore stimato (€)<input className="input" inputMode="decimal" value={f.valore} onChange={(e) => setF({ ...f, valore: e.target.value })} /></label>
            <label className="field">Fonte *<input className="input" required placeholder="es. visita 26/11" value={f.fonte} onChange={(e) => setF({ ...f, fonte: e.target.value })} /></label>
          </div>
          <label className="field">Prossimo passo<input className="input" value={f.passo} onChange={(e) => setF({ ...f, passo: e.target.value })} /></label>
          <p className="dim" style={{ fontSize: 12, margin: 0 }}>{AVVISO}</p>
          <div><button className="btn primary" type="submit">Salva</button></div>
        </form>)}
      {snap.vendite.length === 0 ? <Vuoto icona={TrendingUp}>Pipeline vuota. Aggiungi le aziende man mano (l'import dal CSV dei lead arriverà con il branch vendite).</Vuoto> :
        <div className="pipeline-fasi" role="list" aria-label="Fasi della pipeline">
          {FASI_VENDITA.map((fase) => (
            <div key={fase} className="pipeline-fase" role="listitem" data-fase={fase}>
              <h4>{NOMI_FASE[fase]} <span className="count">{p.fasi[fase].numero}</span></h4>
              {p.fasi[fase].valore > 0 && <div className="dim mono" style={{ fontSize: 12 }}>{euro(p.fasi[fase].valore)}</div>}
              {snap.vendite.filter((v) => v.fase === fase).map((v) => (
                <div key={v.id} className="scheda-mini" data-vendita={v.id}>
                  <div className="t">{v.azienda}</div>
                  {v.prossimo_passo && <div className="s">{v.prossimo_passo}</div>}
                  <div className="s dim">fonte: {v.fonte}</div>
                  <label className="sr-only" htmlFor={`fase-${v.id}`}>Fase di {v.azienda}</label>
                  <select id={`fase-${v.id}`} className="input sposta" value={v.fase}
                    onChange={(e) => void esegui(() => source.aggiornaVendita(v.id, { fase: e.target.value as FaseVendita }, user.id), `${v.azienda} → ${NOMI_FASE[e.target.value as FaseVendita]}`)}>
                    {FASI_VENDITA.map((x) => <option key={x} value={x}>{NOMI_FASE[x]}</option>)}
                  </select>
                </div>))}
            </div>))}
        </div>}
      <p className="dim" style={{ fontSize: 12, margin: '8px 0 0' }}>Guardian non contatta nessuno: preventivi e messaggi li prepara un agente come bozza e li invia una persona.</p>
    </Sezione>
  );
}

function Scadenze() {
  const { snap, source, esegui, user } = useG();
  const [nuova, setNuova] = useState(false);
  const [f, setF] = useState({ titolo: '', data: '', tipo: 'fiscale' as TipoScadenza, importo: '', fonte: '' });
  if (!snap) return null;
  const vicine = scadenzeDaGuardare(snap.scadenze, 30);
  const altre = snap.scadenze.filter((s) => s.stato === 'aperta').length - vicine.length;
  const salva = async () => {
    const ok = await esegui(async () => { await source.creaScadenza({ titolo: f.titolo, data: f.data, tipo: f.tipo, importo_eur: numero(f.importo), fonte: f.fonte }, user.id); return true; }, 'Scadenza salvata');
    if (ok) { setNuova(false); setF({ titolo: '', data: '', tipo: 'fiscale', importo: '', fonte: '' }); }
  };
  return (
    <Sezione titolo="Scadenze (30 giorni)" icona={CalendarClock} conta={vicine.length} className="col-6"
      azione={<button className="btn sm" onClick={() => setNuova(!nuova)}><Plus size={14} aria-hidden />{nuova ? 'Chiudi' : 'Aggiungi'}</button>}>
      {nuova && (
        <form className="stack" style={{ marginBottom: 12 }} onSubmit={(e) => { e.preventDefault(); void salva(); }}>
          <label className="field">Cosa scade *<input className="input" required value={f.titolo} onChange={(e) => setF({ ...f, titolo: e.target.value })} /></label>
          <div className="grid2">
            <label className="field">Data *<input className="input" type="date" required value={f.data} onChange={(e) => setF({ ...f, data: e.target.value })} /></label>
            <label className="field">Tipo<select className="input" value={f.tipo} onChange={(e) => setF({ ...f, tipo: e.target.value as TipoScadenza })}>
              {TIPI_SCADENZA.map((x) => <option key={x}>{x}</option>)}</select></label>
            <label className="field">Importo (€)<input className="input" inputMode="decimal" value={f.importo} onChange={(e) => setF({ ...f, importo: e.target.value })} /></label>
            <label className="field">Fonte *<input className="input" required placeholder="es. commercialista 20/11" value={f.fonte} onChange={(e) => setF({ ...f, fonte: e.target.value })} /></label>
          </div>
          <div><button className="btn primary" type="submit">Salva</button></div>
        </form>)}
      {vicine.length === 0 ? <Vuoto icona={CalendarClock}>Nessuna scadenza nei prossimi 30 giorni.</Vuoto> :
        <div className="list">{vicine.map((s) => {
          const g = giorniA(s.data);
          const quando = g < 0 ? `scaduta da ${-g} g` : g === 0 ? 'oggi' : g === 1 ? 'domani' : `tra ${g} giorni`;
          return (
            <div key={s.id} className="item static" data-scadenza={s.id}>
              <div style={{ flex: 1 }}><div className="t">{s.titolo}{s.importo_eur ? ` · ${euro(s.importo_eur)}` : ''}</div>
                <div className="s">{new Date(`${s.data}T00:00:00`).toLocaleDateString('it-IT')} · {s.tipo} · fonte: {s.fonte}</div></div>
              <span className={`pill ${g < 0 ? 'crit' : g <= 7 ? 'warn' : ''}`}>{quando}</span>
              <button className="btn sm" onClick={() => void esegui(() => source.aggiornaScadenza(s.id, { stato: 'fatta' }, user.id), `Fatta: ${s.titolo}`)}
                aria-label={`Segna come fatta: ${s.titolo}`}>Fatta</button>
            </div>);
        })}</div>}
      {altre > 0 && <p className="dim" style={{ fontSize: 12, margin: '8px 0 0' }}>Altre {altre} scadenze aperte più avanti.</p>}
    </Sezione>
  );
}

function Costi() {
  const { snap, source, esegui, user } = useG();
  const [nuovo, setNuovo] = useState(false);
  const [f, setF] = useState({ descrizione: '', importo: '', categoria: 'software' as CategoriaCosto, ricorrenza: 'mensile' as Ricorrenza, fonte: '' });
  if (!snap) return null;
  const m = costoMese(snap.costi);
  const salva = async () => {
    const ok = await esegui(async () => { await source.creaCosto({ descrizione: f.descrizione, importo_eur: numero(f.importo) ?? 0, categoria: f.categoria, ricorrenza: f.ricorrenza, fonte: f.fonte }, user.id); return true; }, 'Costo salvato');
    if (ok) { setNuovo(false); setF({ descrizione: '', importo: '', categoria: 'software', ricorrenza: 'mensile', fonte: '' }); }
  };
  const categorie = Object.entries(m.perCategoria).sort((a, b) => b[1] - a[1]);
  return (
    <Sezione titolo="Costi" icona={Receipt} conta={snap.costi.length} className="col-6"
      azione={<button className="btn sm" onClick={() => setNuovo(!nuovo)}><Plus size={14} aria-hidden />{nuovo ? 'Chiudi' : 'Aggiungi'}</button>}>
      <div className="porta-numeri"><span><b className="mono">{euro(m.totale)}</b> questo mese</span><span><b className="mono">{m.ricorrenti}</b> ricorrenti</span></div>
      {nuovo && (
        <form className="stack" style={{ margin: '12px 0' }} onSubmit={(e) => { e.preventDefault(); void salva(); }}>
          <label className="field">Descrizione *<input className="input" required value={f.descrizione} onChange={(e) => setF({ ...f, descrizione: e.target.value })} /></label>
          <div className="grid2">
            <label className="field">Importo (€) *<input className="input" required inputMode="decimal" value={f.importo} onChange={(e) => setF({ ...f, importo: e.target.value })} /></label>
            <label className="field">Ricorrenza<select className="input" value={f.ricorrenza} onChange={(e) => setF({ ...f, ricorrenza: e.target.value as Ricorrenza })}>
              {Object.entries(NOMI_RICORRENZA).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
            <label className="field">Categoria<select className="input" value={f.categoria} onChange={(e) => setF({ ...f, categoria: e.target.value as CategoriaCosto })}>
              {Object.entries(NOMI_CATEGORIA).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
            <label className="field">Fonte *<input className="input" required placeholder="es. fattura n. 12" value={f.fonte} onChange={(e) => setF({ ...f, fonte: e.target.value })} /></label>
          </div>
          <div><button className="btn primary" type="submit">Salva</button></div>
        </form>)}
      {snap.costi.length === 0 ? <Vuoto icona={Receipt}>Nessun costo inserito. Ogni costo vuole una fonte (fattura, estratto conto).</Vuoto> : <>
        <div className="barre-costi" aria-label="Spesa del mese per categoria">
          {categorie.map(([k, v]) => (
            <div key={k} className="barra-costo"><span>{NOMI_CATEGORIA[k as CategoriaCosto]}</span>
              <span className="barra" aria-hidden><i style={{ width: `${Math.max(4, (v / (categorie[0][1] || 1)) * 100)}%` }} /></span>
              <b className="mono">{euro(Math.round(v * 100) / 100)}</b></div>))}
        </div>
        <div className="list" style={{ marginTop: 8 }}>{snap.costi.slice(0, 6).map((c) => (
          <div key={c.id} className="item static"><div style={{ flex: 1 }}><div className="t">{c.descrizione}</div>
            <div className="s">{NOMI_RICORRENZA[c.ricorrenza]} · {NOMI_CATEGORIA[c.categoria]} · fonte: {c.fonte}</div></div>
            <b className="mono">{euro(c.importo_eur)}</b></div>))}</div>
      </>}
      <p className="dim" style={{ fontSize: 12, margin: '8px 0 0' }}>Mese = ricorrenti mensili + annuali divisi per 12 + spese una tantum di questo mese.</p>
    </Sezione>
  );
}
