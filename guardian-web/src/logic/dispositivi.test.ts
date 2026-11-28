import { describe, expect, it } from 'vitest';
import { erroreNomePc, hashCodice, nuovoCodice, pcOnline, validaNomePc } from './dispositivi';

const ORA = Date.parse('2026-11-28T12:00:00Z');
describe('pcOnline', () => {
  it('online sotto i 5 minuti', () => expect(pcOnline('2026-11-28T11:56:00Z', ORA)).toBe(true));
  it('offline a 5 minuti o più', () => { expect(pcOnline('2026-11-28T11:55:00Z', ORA)).toBe(false); expect(pcOnline('2026-11-28T10:00:00Z', ORA)).toBe(false); });
  it('offline senza segnale o con data non valida', () => { expect(pcOnline(null, ORA)).toBe(false); expect(pcOnline('boh', ORA)).toBe(false); });
});
describe('validaNomePc', () => {
  it('accetta e normalizza', () => expect(validaNomePc('  PC   Menotti ')).toBe('PC Menotti'));
  it('rifiuta vuoto, troppo corto e troppo lungo', () => {
    expect(() => validaNomePc('')).toThrow(); expect(() => validaNomePc('a')).toThrow(); expect(() => validaNomePc('x'.repeat(81))).toThrow();
  });
  it('rifiuta segreti', () => expect(erroreNomePc('token=abc123')).not.toBeNull());
  it('erroreNomePc è null se valido', () => expect(erroreNomePc('PC-Menotti')).toBeNull());
});
describe('codice', () => {
  it('formato e unicità', () => { const a = nuovoCodice(); expect(a).toMatch(/^gdn_[A-Za-z0-9_-]{43}$/); expect(nuovoCodice()).not.toBe(a); });
  it('hash sha256 noto', async () => expect(await hashCodice('abc')).toBe('ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'));
});

import { REVOCATO, nomeRevocato, pcAttivi } from './dispositivi';
describe('PC revocati', () => {
  it('il nome viene segnato una volta sola e i segnati spariscono', () => {
    expect(nomeRevocato('PC-A')).toBe(`${REVOCATO}PC-A`);
    expect(nomeRevocato(nomeRevocato('PC-A'))).toBe(`${REVOCATO}PC-A`);
    expect(nomeRevocato('x'.repeat(80)).length).toBe(80);
    expect(pcAttivi([{ nome: 'PC-A' }, { nome: nomeRevocato('PC-B') }]).map((d) => d.nome)).toEqual(['PC-A']);
  });
});
