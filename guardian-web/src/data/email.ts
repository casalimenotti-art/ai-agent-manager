export type StatoInvioEmail = 'bozza' | 'in_attesa_di_approvazione' | 'invio' | 'inviata' | 'errore';

export interface BozzaEmail {
  id: string;
  destinatari: string[];
  oggetto: string;
  corpo: string;
  stato: StatoInvioEmail;
  approvazioneId?: number;
  errore?: string;
}

export type CasellaEmail =
  | { collegata: false; messaggi: []; errore: null }
  | { collegata: true; messaggi: readonly { id: string; mittente: string; oggetto: string; data: string; letta: boolean }[]; errore: string | null };

export interface GatewayEmail {
  stato(): CasellaEmail;
}

/** Integrazione intenzionalmente vuota: nessun contenuto di posta viene simulato. */
export const emailNonCollegata: GatewayEmail = {
  stato: () => ({ collegata: false, messaggi: [], errore: null }),
};
