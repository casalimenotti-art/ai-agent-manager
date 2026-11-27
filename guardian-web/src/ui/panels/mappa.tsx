// Ondata 8: mappa operativa. Chi lavora con quale agente, su quali task, in quale stanza. Solo collegamenti reali.
import { useEffect, useState, type KeyboardEvent } from 'react';
import { COLONNE, costruisciMappa, type Nodo } from '../../logic/mappa';
import { useG } from '../../state';
import { coloreStanza } from '../Stanze';
import { ETICHETTE_AGENTE, ETICHETTE_TASK, Vuoto } from '../kit';

const COLORE: Record<string, string> = {
  working: 'var(--ok)', running: 'var(--ok)', idle: 'var(--accent-2)', ready: 'var(--accent-2)', waiting: 'var(--warn)', needs_approval: 'var(--warn)',
  blocked: 'var(--serious)', error: 'var(--crit)', failed: 'var(--crit)', offline: 'var(--text-3)', unknown: 'var(--text-3)',
};
const corto = (t: string, n = 24) => (t.length > n ? `${t.slice(0, n - 1)}…` : t);

export function MappaPanel() {
  const { snap, apri, apriStanza, chiudi, presenti } = useG();
  const [ora, setOra] = useState(Date.now());
  useEffect(() => { const t = setInterval(() => setOra(Date.now()), 15_000); return () => clearInterval(t); }, []);
  if (!snap) return null;
  const grezza = costruisciMappa(snap, ora);
  const etichetta = (n: Nodo) => (n.tipo === 'task' ? ETICHETTE_TASK[n.stato as keyof typeof ETICHETTE_TASK] : n.tipo === 'agente' ? ETICHETTE_AGENTE[n.stato as keyof typeof ETICHETTE_AGENTE] : undefined) ?? n.sotto;
  const m = { ...grezza, nodi: grezza.nodi.map((n) => ({ ...n, sotto: etichetta(n) })) };
  if (!m.nodi.length) return <Vuoto>Ancora niente da collegare: mancano persone, agenti o task.</Vuoto>;
  const pos = new Map(m.nodi.map((n) => [n.id, n]));
  const inHq = new Set(presenti.map((p) => p.id));
  const vai = (n: Nodo) => {
    if (n.tipo === 'agente') apri({ p: 'agente', id: n.rif });
    else if (n.tipo === 'task') apri({ p: 'task', id: n.rif });
    else if (n.tipo === 'stanza') { chiudi(); apriStanza(n.rif); }
    else apri({ p: 'agenti' });
  };
  const tasto = (e: KeyboardEvent, n: Nodo) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); vai(n); } };
  const colore = (n: Nodo) => n.tipo === 'stanza' ? coloreStanza(snap.stanze.find((s) => s.id === n.rif)!) : n.stato ? COLORE[n.stato] ?? 'var(--text-2)' : 'var(--accent)';
  return (
    <div className="mappa">
      <p className="dim" style={{ fontSize: 13, marginTop: 0 }}>
        Le linee sono collegamenti presenti nei dati (agente del collaboratore, task assegnato, progetto della stanza). Pulsa ciò che ha avuto
        attività negli ultimi 2 minuti. {m.nascosti > 0 && `Altri ${m.nascosti} task aperti non mostrati.`}
      </p>
      <svg className="mappa-svg" viewBox={`0 0 1000 ${m.altezza}`} role="group" aria-label="Mappa operativa">
        {COLONNE.map((c) => <text key={c.tipo} x={c.x} y={30} className="mappa-col" textAnchor="middle">{c.titolo}</text>)}
        {m.archi.map((a) => {
          const p = pos.get(a.da)!, q = pos.get(a.a)!; const mx = (p.x + q.x) / 2;
          return <path key={`${a.da}-${a.a}`} d={`M${p.x + 70},${p.y} C${mx},${p.y} ${mx},${q.y} ${q.x - 70},${q.y}`} className={`mappa-arco${a.attivo ? ' attivo' : ''}`} />;
        })}
        {m.nodi.map((n) => (
          <g key={n.id} transform={`translate(${n.x},${n.y})`} className={`mappa-nodo${n.impulso ? ' impulso' : ''}`} role="button" tabIndex={0}
            aria-label={`${n.etichetta}${n.sotto ? `, ${n.sotto}` : ''}`} onClick={() => vai(n)} onKeyDown={(e) => tasto(e, n)} style={{ '--c': colore(n) } as React.CSSProperties}>
            <rect x={-70} y={-22} width={140} height={44} rx={10} />
            <circle cx={-56} cy={0} r={5} className="mappa-punto" />
            {n.tipo === 'persona' && inHq.has(n.rif) && <circle cx={60} cy={-14} r={4} className="mappa-hq"><title>Nell'HQ ora</title></circle>}
            <text x={-44} y={n.sotto ? -3 : 5} className="mappa-etichetta">{corto(n.etichetta, 17)}</text>
            {n.sotto && <text x={-44} y={13} className="mappa-sotto">{corto(n.sotto, 20)}</text>}
          </g>
        ))}
      </svg>
      <ul className="mappa-lista" aria-label="Mappa operativa in elenco">
        {m.nodi.filter((n) => n.tipo !== 'stanza').map((n) => {
          const verso = m.archi.filter((a) => a.da === n.id).map((a) => pos.get(a.a)!.etichetta);
          return <li key={n.id}><button className="btn ghost sm" onClick={() => vai(n)}>{n.etichetta}</button>
            {n.sotto && <span className="dim"> · {n.sotto}</span>}{verso.length > 0 && <span className="dim"> → {verso.join(', ')}</span>}</li>;
        })}
      </ul>
    </div>
  );
}
