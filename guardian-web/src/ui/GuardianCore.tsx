// Nucleo visivo di Guardian: anelli concentrici SVG. Le animazioni dipendono solo dallo stato reale.
import type { StatoNucleo } from '../logic/guardian';

const NOMI: Record<StatoNucleo, string> = { offline: 'Non collegato', error: 'Errore', listening: 'In ascolto', speaking: 'Sta parlando', thinking: 'Sto pensando',
  approval: 'In attesa di approvazione', working: 'Coordino gli agenti', completed: 'Attività completata', idle: 'Online' };

export function GuardianCore({ stato }: { stato: StatoNucleo }) {
  const tick = Array.from({ length: 60 }, (_, i) => i);
  return (
    <svg className="core" viewBox="0 0 200 200" data-stato={stato} role="img" aria-label={`Guardian: ${NOMI[stato]}`}>
      <defs>
        <radialGradient id="gn" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#e0fbff" /><stop offset="45%" stopColor="#22d3ee" /><stop offset="100%" stopColor="#0e7490" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="100" cy="100" r="94" fill="none" stroke="#1b2637" strokeWidth="1" />
      <g className="ring r1">
        {tick.map((i) => (
          <line key={i} x1="100" y1="10" x2="100" y2={i % 5 ? 15 : 19} stroke={i % 5 ? '#2d3d57' : '#22d3ee'} strokeWidth={i % 5 ? 1 : 1.6}
            transform={`rotate(${i * 6} 100 100)`} />
        ))}
      </g>
      <g className="ring r2">
        <circle cx="100" cy="100" r="70" fill="none" stroke="#22d3ee" strokeOpacity="0.55" strokeWidth="2" strokeDasharray="60 22 8 22" />
        <circle cx="100" cy="100" r="58" fill="none" stroke="#7dd3fc" strokeOpacity="0.25" strokeWidth="1" strokeDasharray="2 6" />
      </g>
      <circle cx="100" cy="100" r="44" fill="none" stroke="#22d3ee" strokeOpacity="0.35" strokeWidth="1" />
      <circle className="nucleo" cx="100" cy="100" r="26" fill="url(#gn)" />
      <circle cx="100" cy="100" r="9" fill="#e0fbff" opacity="0.9" />
    </svg>
  );
}
