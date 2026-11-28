// Pannello Dispositivi: logica pura (validazione, online/offline, codice dispositivo e suo hash).
// Nel database va solo l'hash sha256 del codice (devices.token_hash), come fa il Guardian classico.
import { ErroreDati, controllaTesto } from '../data/source';

export const ONLINE_MINUTI = 5;

/** Online se l'ultimo segnale ha meno di 5 minuti. Senza segnale (o data non valida) è offline. */
export function pcOnline(lastSeen: string | null | undefined, ora: number = Date.now()): boolean {
  if (!lastSeen) return false;
  const t = Date.parse(lastSeen);
  if (Number.isNaN(t)) return false;
  const eta = ora - t;
  return eta >= -60_000 && eta < ONLINE_MINUTI * 60_000; // tolleranza di 1 minuto per orologi non allineati
}

/** Nome del PC: obbligatorio, 2-80 caratteri, senza a capo, senza segreti. */
export function validaNomePc(nome: string | null | undefined): string {
  const v = (nome ?? '').trim().replace(/\s+/g, ' ');
  if (v.length < 2) throw new ErroreDati('Scrivi il nome del PC (almeno 2 caratteri, es. PC-Menotti).');
  if (v.length > 80) throw new ErroreDati('Il nome del PC è troppo lungo (massimo 80 caratteri).');
  return controllaTesto(v, 'nome del PC', 80);
}

/** Messaggio di errore oppure null se il nome va bene (comodo per la UI). */
export function erroreNomePc(nome: string): string | null {
  try { validaNomePc(nome); return null; } catch (e) { return e instanceof ErroreDati ? e.message : 'Nome non valido.'; }
}

/** La revoca non può cancellare la riga (nessuna policy di delete): segna il nome e i PC segnati spariscono dalla dashboard. */
export const REVOCATO = '[revocato] ';
export const nomeRevocato = (nome: string) => (nome.startsWith(REVOCATO) ? nome : `${REVOCATO}${nome}`.slice(0, 80));
export const pcAttivi = <T extends { nome: string }>(elenco: T[]): T[] => elenco.filter((d) => !d.nome.startsWith(REVOCATO));
const hex = (b: Uint8Array) => Array.from(b, (x) => x.toString(16).padStart(2, '0')).join('');

/** Stesso formato del classico: "gdn_" + 32 byte casuali in base64 url-safe. */
export function nuovoCodice(): string {
  const b = crypto.getRandomValues(new Uint8Array(32));
  const b64 = btoa(String.fromCharCode(...b)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  return `gdn_${b64}`;
}

/** sha256 esadecimale del codice: identico a hashlib.sha256(token.encode()).hexdigest() e a _device_da_token. */
export async function hashCodice(codice: string): Promise<string> {
  return hex(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(codice))));
}
