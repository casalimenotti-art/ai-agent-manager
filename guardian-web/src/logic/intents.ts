// Router di intenti deterministico: risponde dai dati senza alcun modello AI. Ogni risposta dichiara la fonte.
import type { Snapshot } from '../types';
import { costoMese, euro, giorniA, pipelinePerFase, scadenzeDaGuardare } from './amministrazione';
import { agentiAlLavoro, completatiOggi, tassoCompletamento } from './metrics';
import { report } from './report';
import { statoAgente } from './status';

export interface Risposta { testo: string; fonte: string; apri?: { p: string; filtro?: string }; /** stanza da aprire (Vendite, Amministrazione) */ stanza?: string }

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
  if (ha(q, 'scadenz', 'scade')) {
    const v = scadenzeDaGuardare(s.scadenze ?? [], 14, ora ? new Date(ora) : undefined);
    return { testo: v.length ? `${v.length} scadenze nei prossimi 14 giorni: ${v.slice(0, 4).map((x) => {
      const g = giorniA(x.data, ora ? new Date(ora) : undefined); return `${x.titolo} (${g < 0 ? `scaduta da ${-g} g` : g === 0 ? 'oggi' : `tra ${g} g`})`; }).join('; ')}.`
      : 'Nessuna scadenza nei prossimi 14 giorni.', fonte: 'tabella scadenze (inserite a mano, con fonte)', stanza: 'amministrazione' };
  }
  if (ha(q, 'costi', 'spend', 'spesa', 'quanto paghiamo')) {
    const m = costoMese(s.costi ?? [], ora ? new Date(ora) : undefined);
    return { testo: s.costi?.length ? `Questo mese: ${euro(m.totale)} (${m.ricorrenti} costi ricorrenti).` : 'Nessun costo inserito: la stanza Amministrazione è vuota.',
      fonte: 'tabella costi: mensili + annuali/12 + una tantum del mese', stanza: 'amministrazione' };
  }
  if (ha(q, 'pipeline', 'preventiv', 'trattativ') || (ha(q, 'vendit') && ha(q, 'come va', 'andamento', 'quant'))) {
    const p = pipelinePerFase(s.vendite ?? []);
    return { testo: s.vendite?.length ? `Pipeline: ${p.aperte} aperte per ${euro(p.valoreAperto)}; ${p.fasi.proposta.numero} proposte e ${p.fasi.trattativa.numero} trattative; ${p.fasi.vinto.numero} vinte.`
      : 'La pipeline vendite è vuota.', fonte: 'tabella vendite_pipeline (senza dati personali)', stanza: 'vendite' };
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
  // "questo mese", "questa settimana" non parlano del pannello aperto
  const periodo = /quest[oa] (mese|settimana|anno)/.test(q);
  if (!ctx?.id || periodo || !ha(q, 'questo', 'questa', 'perche', 'cosa sta', 'cosa succede', 'spiega')) return rispondi(domanda, s, ora);
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
  if (ctx.p === 'stanza') {
    const st = s.stanze.find((x) => x.id === ctx.id);
    if (!st) return null;
    const ts = s.tasks.filter((t) => { const p = s.projects.find((x) => x.id === t.project_id);
      return p ? p.stanza_id === st.id : t.responsabile === st.responsabile; });
    const conta = (...stati: string[]) => ts.filter((t) => stati.includes(t.stato)).length;
    const ag = s.agents.filter((a) => a.user_id === st.responsabile);
    return { testo: `Stanza ${st.nome}: ${conta('running', 'waiting')} task in corso, ${conta('backlog', 'planned', 'ready')} da fare, ` +
      `${conta('blocked', 'failed', 'needs_approval')} fermi. Agenti: ${ag.length ? ag.map((a) => `${a.nome} (${statoAgente(a, ora)})`).join(', ') : 'nessuno collegato'}.`,
      fonte: 'stanze, tasks, agents' };
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

/** "apri vendite", "vai in amministrazione", "torna al centro": comandi di navigazione tra le stanze. */
export function comandoStanza(domanda: string, s: Snapshot): { stanza: string | null; testo: string } | null {
  const q = norm(domanda);
  if (/\b(torna|vai)\b.*\b(centro|orbita|home)\b/.test(q)) return { stanza: null, testo: 'Torno al centro.' };
  if (!/\b(apri|vai|entra|mostra|porta)\b/.test(q)) return null;
  const st = s.stanze.find((x) => q.includes(norm(x.id)) || q.includes(norm(x.nome).split(/[ &]+/)[0]));
  return st ? { stanza: st.id, testo: `Apro la stanza ${st.nome}.` } : null;
}
