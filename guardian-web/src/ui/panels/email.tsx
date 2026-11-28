import { Inbox, Mail, Search } from 'lucide-react';
import { emailNonCollegata } from '../../data/email';

export function EmailPanel() {
  const casella = emailNonCollegata.stato();
  return <section className="email-panel" aria-label="Centro email">
    <div className="email-toolbar" aria-hidden="true"><button type="button" disabled><Inbox size={16} />Posta in arrivo</button>
      <button type="button" disabled>Bozze</button><label><Search size={15} /><input aria-label="Cerca nella posta" disabled placeholder="Cerca nella posta…" /></label></div>
    <div className="email-empty" role="status" aria-live="polite">
      <Mail size={28} aria-hidden="true" />
      <h3>{casella.collegata ? 'Posta disponibile' : 'Email non collegata'}</h3>
      <p>{casella.collegata ? 'La posta è pronta.' : 'Collega Gmail per vedere la posta.'}</p>
      {!casella.collegata && <span>Nessun messaggio viene mostrato finché Gmail non è collegato.</span>}
    </div>
    <p className="email-approval-note">Ogni invio futuro passerà da una bozza e richiederà approvazione.</p>
  </section>;
}
