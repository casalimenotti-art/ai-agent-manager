import type { ComponentType } from 'react';
import type { Pannello } from '../../state';
import { ApprovalPanel, ApprovalsPanel, HandoffPanel, MemoriaPanel, TaskPanel, TasksPanel } from './lavoro';
import { AgentePanel, AgentiPanel, AttivitaPanel, AziendaPanel, AziendePanel, DispositiviPanel, ImpostazioniPanel, NotifichePanel, SalutePanel,
  StatistichePanel, WorkflowPanel } from './sistema';
import { MappaPanel } from './mappa';

export const PANNELLI: Record<string, { titolo: string; componente: ComponentType<Pannello>; largo?: boolean }> = {
  agenti: { titolo: 'Agenti', componente: AgentiPanel }, agente: { titolo: 'Agente', componente: AgentePanel, largo: true },
  aziende: { titolo: 'Aziende', componente: AziendePanel }, azienda: { titolo: 'Azienda', componente: AziendaPanel, largo: true },
  tasks: { titolo: 'Task', componente: TasksPanel, largo: true }, task: { titolo: 'Task', componente: TaskPanel, largo: true },
  approvazioni: { titolo: 'Approvazioni', componente: ApprovalsPanel }, approvazione: { titolo: 'Approvazione', componente: ApprovalPanel },
  handoff: { titolo: 'Handoff', componente: HandoffPanel }, memoria: { titolo: 'Memoria condivisa', componente: MemoriaPanel },
  notifiche: { titolo: 'Notifiche', componente: NotifichePanel }, attivita: { titolo: 'Attività', componente: AttivitaPanel, largo: true },
  statistiche: { titolo: 'Statistiche', componente: StatistichePanel, largo: true }, workflow: { titolo: 'Workflow', componente: WorkflowPanel },
  dispositivi: { titolo: 'PC collegati', componente: DispositiviPanel }, salute: { titolo: 'Salute del sistema', componente: SalutePanel },
  impostazioni: { titolo: 'Impostazioni', componente: ImpostazioniPanel },
  mappa: { titolo: 'Mappa operativa', componente: MappaPanel, largo: true },
};

export function titoloPannello(p: Pannello) {
  const base = PANNELLI[p.p]?.titolo ?? p.p;
  return p.id ? `${base} ${/^\d+$/.test(p.id) ? `#${p.id}` : p.id}` : base;
}
