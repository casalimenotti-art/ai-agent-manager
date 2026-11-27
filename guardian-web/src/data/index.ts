import { DemoSource } from './demo';
import type { DataSource } from './source';
import { SupabaseSource } from './supabase';

export type Configurazione = { source: DataSource } | { errore: string };

/** Sceglie la fonte dati. In produzione serve Supabase; la demo esiste solo se VITE_DEMO=1 (mai di default). */
export function creaFonte(): Configurazione {
  const env = import.meta.env;
  if (env.VITE_DEMO === '1') return { source: new DemoSource() };
  if (env.VITE_SUPABASE_URL && env.VITE_SUPABASE_ANON_KEY) return { source: new SupabaseSource(env.VITE_SUPABASE_URL, env.VITE_SUPABASE_ANON_KEY) };
  return { errore: 'Configurazione mancante: imposta VITE_SUPABASE_URL e VITE_SUPABASE_ANON_KEY (vedi guardian-web/.env.example).' };
}
