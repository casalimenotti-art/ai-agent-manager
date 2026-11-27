// Router di intenti deterministico: risponde dai dati senza alcun modello AI. Ogni risposta dichiara la fonte.
import type { Snapshot } from '../types';
import { agentiAlLavoro, completatiOggi, tassoCompletamento } from './metrics';
import { report } from './report';
import { statoAgente } from './status';

export interface Risposta { testo: string; fonte: string; apri?: { p: string; filtro?: string } }

const norm = (t: string) => t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
const ha = (t: string, ...parole: string[]) => parole.some((p) => t.includes(p));

export function rispondi(domanda: string, s: Snapshot, ora?: number): Risposta | null {
  const q = norm(domanda);
  if (ha(q, 'agent') && ha(q, 'attiv', 'lavor', 'online', 'quant')) {
    const lav = s.agents.filter((a) => ['working', 'waiting', 'needs_approval'].includes(statoAgente(a, ora)));
    const nomi = lav.map((a) => `${a.nome} (${statoAgente(a, ora)})`).join(', ');
    return { testo: `${agentiAlLavoro(s, ora)} agenti al lavoro su ${s.agents.length} registrati${nomi ? `: ${nomi}` : ''}.`,
      fonte: 'tabella agents, stato dal bridge (ultimi 180 s)', apri: { p: 'agenti' } };
  }
  if (ha(q, 'complet') && ha(q, 'oggi')) {
    return { testo: `Oggi sono stati completati ${completatiOggi(s, ora)} task.`, fonte: 'eventi task_completed di oggi', apri: { p: 'statistiche' } };
  }
  if (ha(q, 'tasso', 'percentual')) {
    const t = tassoCompletamento(s, 7, ora);
    return { testo: t === null ? 'Nessun task chiuso negli ultimi 7 giorni: il tasso non è calcolabile.' :
      `Tasso di completamento negli ultimi 7 giorni: ${Math.round(t * 100)}%.`, fonte: 'task chiusi negli ultimi 7 giorni', apri: { p: 'statistiche' } };
  }
  if (ha(q, 'blocc', 'fermi', 'fallit')) {
    const b = s.tasks.filter((t) => ['blocked', 'failed'].includes(t.stato));
    return { testo: b.length ? `${b.length} task bloccati o falliti: ${b.slice(0, 5).map((t) => `#${t.id} ${t.titolo}`).join('; ')}.` :
      'Nessun task bloccato o fallito.', fonte: 'tabella tasks', apri: { p: 'tasks', filtro: 'fermi' } };
  }
  if (ha(q, 'approva')) {
    const a = s.approvals.filter((x) => x.status === 'richiesta');
    return { testo: a.length ? `${a.length} approvazioni in attesa: ${a.slice(0, 5).map((x) => x.action).join('; ')}.` :
      'Nessuna approvazione in attesa.', fonte: 'tabella approvals', apri: { p: 'approvazioni' } };
  }
  if (ha(q, 'consigl', 'prossim', 'cosa faccio', 'cosa devo')) {
    const r = report(s, ora);
    return { testo: r.prossime.length ? `Prossime azioni:\n${r.prossime.slice(0, 5).map((a, i) => `${i + 1}. ${a.testo}`).join('\n')}` :
      'Nessuna azione urgente.', fonte: 'regole fisse sui dati (report)' };
  }
  if (ha(q, 'riepilog', 'riassun', 'giornata', 'situazione', 'cosa sta succedendo')) {
    const r = report(s, ora); const c = r.conteggi;
    return { testo: `Task aperti ${r.aperti} (in esecuzione ${c.running}, pronti ${c.ready}, bloccati ${c.blocked}, falliti ${c.failed}). ` +
      `Completati oggi ${completatiOggi(s, ora)}. Agenti al lavoro ${agentiAlLavoro(s, ora)}. Approvazioni in attesa ${r.approvazioni}.`,
      fonte: 'tasks, agents, approvals, activity_events', apri: { p: 'statistiche' } };
  }
  return null;
}

export const DOMANDE_ESEMPIO = ['Quanti agenti sono attivi?', 'Quanti task abbiamo completato oggi?', 'Cosa è bloccato?',
  'Ci sono approvazioni in attesa?', 'Cosa mi consigli di fare?', 'Fammi un riepilogo della giornata'];

/** Domande su "questo task / questo agente / questa azienda" usando solo il contesto minimo del pannello aperto. */
export function rispondiConContesto(domanda: string, s: Snapshot, ctx: { p: string; id?: string } | null, ora?: number): Risposta | null {
  const q = norm(domanda);
  if (!ctx?.id || !ha(q, 'questo', 'questa', 'perche', 'cosa sta', 'spiega')) return rispondi(domanda, s, ora);
  if (ctx.p === 'task') {
    const t = s.tasks.find((x) => String(x.id) === ctx.id);
    if (!t) return null;
    const dip = t.depends_on.map((d) => s.tasks.find((x) => x.id === d)).filter((x) => x && x.stato !== 'completed');
    const app = s.approvals.filter((a) => a.task_id === t.id && a.status === 'richiesta');
    const motivi = [
      ...dip.map((d) => `dipende dal task #${d!.id} «${d!.titolo}» (${d!.stato})`),
      ...app.map((a) => `aspetta l'approvazione «${a.action}»`),
      ...(t.error ? [`errore registrato: ${t.error}`] : []),
    ];
    return { testo: `Task #${t.id} «${t.titolo}» è ${t.stato}. ${motivi.length ? `Motivi: ${motivi.join('; ')}.` : 'Nessun blocco registrato.'}` +
      (t.next_step ? ` Prossimo passo: ${t.next_step}.` : ''), fonte: 'task, dipendenze e approvazioni collegate' };
  }
  if (ctx.p === 'agente') {
    const a = s.agents.find((x) => x.id === ctx.id);
    if (!a) return null;
    const t = s.tasks.find((x) => x.id === a.current_task_id);
    return { testo: `${a.nome} (${a.user_id}) è ${statoAgente(a, ora)}. ${t ? `Sta lavorando al task #${t.id} «${t.titolo}».` : 'Nessun task corrente registrato.'}` +
      (a.error ? ` Ultimo errore: ${a.error}.` : ''), fonte: 'agents (bridge) e tasks' };
  }
  if (ctx.p === 'azienda') {
    const p = s.projects.find((x) => String(x.id) === ctx.id);
    if (!p) return null;
    const ts = s.tasks.filter((t) => t.project_id === p.id);
    const conta = (st: string) => ts.filter((t) => t.stato === st).length;
    return { testo: `${p.nome}: ${ts.length} task (in esecuzione ${conta('running')}, bloccati ${conta('blocked')}, completati ${conta('completed')}).`,
      fonte: 'projects e tasks' };
  }
  return rispondi(domanda, s, ora);
}
