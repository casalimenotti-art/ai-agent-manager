// Grafici SVG secondo la skill dataviz: un solo asse Y, colori per entità in ordine fisso (palette validata),
// segni sottili, testi nei colori del testo, tooltip al passaggio, legenda con >= 2 serie, vista tabellare alternativa.
import { useState, type ReactNode } from 'react';

export const SERIE = ['var(--series-1)', 'var(--series-2)', 'var(--series-3)', 'var(--series-4)', 'var(--series-5)', 'var(--series-6)',
  'var(--series-7)', 'var(--series-8)'];

function ConTabella({ titolo, tabella, children }: { titolo: string; tabella: ReactNode; children: ReactNode }) {
  const [vista, setVista] = useState<'grafico' | 'tabella'>('grafico');
  return (
    <figure style={{ margin: 0 }} aria-label={titolo}>
      <div className="row between" style={{ marginBottom: 8 }}>
        <figcaption style={{ fontSize: 13, fontWeight: 600 }}>{titolo}</figcaption>
        <button className="btn ghost sm" onClick={() => setVista((v) => (v === 'grafico' ? 'tabella' : 'grafico'))} aria-pressed={vista === 'tabella'}>
          {vista === 'grafico' ? 'Vista tabella' : 'Vista grafico'}</button>
      </div>
      {vista === 'grafico' ? children : tabella}
    </figure>
  );
}

export interface SerieLinea { nome: string; valori: number[] }
export function GraficoLinee({ titolo, etichette, serie }: { titolo: string; etichette: string[]; serie: SerieLinea[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const W = 440, H = 170, L = 30, R = 8, T = 10, B = 24;
  const max = Math.max(1, ...serie.flatMap((s) => s.valori));
  const passo = Math.max(1, Math.ceil(max / 4));
  const tickY = Array.from({ length: Math.floor(max / passo) + 1 }, (_, i) => i * passo);
  const top = tickY[tickY.length - 1] || 1;
  const x = (i: number) => L + (i * (W - L - R)) / Math.max(1, etichette.length - 1);
  const y = (v: number) => T + (H - T - B) * (1 - v / top);
  const tabella = (
    <table className="data"><thead><tr><th>Giorno</th>{serie.map((s) => <th key={s.nome}>{s.nome}</th>)}</tr></thead>
      <tbody>{etichette.map((e, i) => <tr key={e}><td>{e}</td>{serie.map((s) => <td key={s.nome} className="mono">{s.valori[i]}</td>)}</tr>)}</tbody></table>);
  return (
    <ConTabella titolo={titolo} tabella={tabella}>
      <div className="rel">
        <svg className="chart" viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={`${titolo}: ${serie.map((s) => `${s.nome} totale ${s.valori.reduce((a, b) => a + b, 0)}`).join(', ')}`}
          onMouseLeave={() => setHover(null)}>
          <g className="grid">{tickY.map((v) => <line key={v} x1={L} x2={W - R} y1={y(v)} y2={y(v)} />)}</g>
          {tickY.map((v) => <text key={v} x={L - 6} y={y(v) + 4} textAnchor="end">{v}</text>)}
          {etichette.map((e, i) => (i % Math.ceil(etichette.length / 7) === 0 || i === etichette.length - 1) &&
            <text key={e} x={x(i)} y={H - 6} textAnchor="middle">{e}</text>)}
          {serie.map((s, k) => <polyline key={s.nome} fill="none" stroke={SERIE[k]} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round"
            points={s.valori.map((v, i) => `${x(i)},${y(v)}`).join(' ')} />)}
          {hover !== null && <line x1={x(hover)} x2={x(hover)} y1={T} y2={H - B} stroke="var(--border-2)" />}
          {hover !== null && serie.map((s, k) => <circle key={s.nome} cx={x(hover)} cy={y(s.valori[hover])} r="4.5" fill={SERIE[k]} stroke="var(--surface-1)" strokeWidth="2" />)}
          {etichette.map((e, i) => <rect key={e} x={x(i) - (W - L - R) / etichette.length / 2} y={T} width={(W - L - R) / etichette.length} height={H - T - B}
            fill="transparent" onMouseEnter={() => setHover(i)} />)}
        </svg>
        {hover !== null && (
          <div className="tip" style={{ left: `${(x(hover) / W) * 100}%`, top: 0, transform: 'translateX(-50%)' }}>
            <b>{etichette[hover]}</b>{serie.map((s, k) => <div key={s.nome}><i style={{ display: 'inline-block', width: 8, height: 8, background: SERIE[k], marginRight: 4 }} />
              {s.nome}: <span className="mono">{s.valori[hover]}</span></div>)}
          </div>)}
      </div>
      {serie.length > 1 && <div className="legend">{serie.map((s, k) => <span key={s.nome}><i style={{ background: SERIE[k] }} />{s.nome}</span>)}</div>}
    </ConTabella>
  );
}

export interface Barra { id: string; nome: string; valore: number; extra?: string }
/** Barre orizzontali: il colore segue l'entità (indice stabile per id), non la posizione dopo un ordinamento. */
export function GraficoBarre({ titolo, barre, ordineColori, unita = '' }: { titolo: string; barre: Barra[]; ordineColori: string[]; unita?: string }) {
  const max = Math.max(1, ...barre.map((b) => b.valore));
  const colore = (id: string) => SERIE[Math.max(0, ordineColori.indexOf(id)) % SERIE.length];
  const tabella = <table className="data"><thead><tr><th>Nome</th><th>Valore</th></tr></thead>
    <tbody>{barre.map((b) => <tr key={b.id}><td>{b.nome}</td><td className="mono">{b.valore}{unita}</td></tr>)}</tbody></table>;
  return (
    <ConTabella titolo={titolo} tabella={tabella}>
      <div className="stack" style={{ gap: 8 }} role="list">
        {barre.map((b) => (
          <div key={b.id} role="listitem" title={`${b.nome}: ${b.valore}${unita}${b.extra ? ` · ${b.extra}` : ''}`}>
            <div className="row between" style={{ fontSize: 12, marginBottom: 3 }}><span>{b.nome}</span><span className="mono muted">{b.valore}{unita}</span></div>
            <div style={{ height: 10, background: 'var(--surface-3)', borderRadius: 4 }}>
              <div style={{ width: `${(b.valore / max) * 100}%`, minWidth: b.valore ? 4 : 0, height: '100%', background: colore(b.id), borderRadius: '0 4px 4px 0' }} />
            </div>
          </div>))}
      </div>
    </ConTabella>
  );
}
