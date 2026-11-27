import { describe, expect, it } from 'vitest';
import { BargeIn, comandoConversazione, dividiFrasi, perLaVoce, rms, Vad } from './vad';

describe('VAD', () => {
  it('inizio e fine frase dopo 1 s di silenzio; ignora i rumori brevi', () => {
    const v = new Vad();
    expect(v.passo(0.05, 0)).toBe('inizio');
    expect(v.passo(0.05, 600)).toBeNull();
    expect(v.passo(0.0, 1500)).toBeNull();
    expect(v.passo(0.0, 1700)).toBe('fine');
    expect(v.passo(0.05, 3000)).toBe('inizio');
    expect(v.passo(0.0, 4100)).toBeNull(); // 0 ms di parlato: rumore
  });
  it('taglia le frasi troppo lunghe', () => {
    const v = new Vad(); v.passo(0.1, 0);
    for (let t = 100; t < 25000; t += 100) v.passo(0.1, t);
    expect(v.passo(0.1, 25100)).toBe('fine');
  });
  it('barge-in solo con voce forte per 250 ms', () => {
    const b = new BargeIn();
    expect(b.passo(0.1, 0)).toBe(false);
    expect(b.passo(0.03, 100)).toBe(false);
    expect(b.passo(0.1, 200)).toBe(false);
    expect(b.passo(0.1, 460)).toBe(true);
  });
});

describe('frasi e comandi', () => {
  it('divide in frasi e accorcia per la voce', () => {
    expect(dividiFrasi('Ciao. Tutto ok! Domanda? Ultima')).toEqual(['Ciao.', 'Tutto ok!', 'Domanda?', 'Ultima']);
    expect(perLaVoce('Uno. Due. Tre. Quattro.')).toBe('Uno. Due. Tre. Vuoi che continui?');
    expect(perLaVoce('Prossime azioni:\n1. Decidi X.\n2. Sblocca Y.')).toContain('Decidi X.');
  });
  it('riconosce basta e silenzio', () => {
    expect(comandoConversazione('Guardian, basta.')).toBe('termina');
    expect(comandoConversazione('stop')).toBe('termina');
    expect(comandoConversazione('Silenzio!')).toBe('silenzio');
    expect(comandoConversazione('basta con i task bloccati?')).toBeNull();
  });
  it('rms', () => { expect(rms([0.5, -0.5])).toBeCloseTo(0.5); expect(rms([])).toBe(0); });
});

describe('wav per la voce locale', () => {
  it('ricampiona a 16 kHz e scrive un WAV mono 16 bit valido', async () => {
    const { ricampiona, unisci, wav16 } = await import('./wav');
    const x = new Float32Array(48000).fill(0.5);
    const r = ricampiona(x, 48000);
    expect(r.length).toBe(16000); expect(r[100]).toBeCloseTo(0.5);
    const w = wav16(unisci([r.subarray(0, 8), r.subarray(8, 16)]));
    const v = new DataView(w.buffer);
    expect(String.fromCharCode(...w.subarray(0, 4))).toBe('RIFF');
    expect(v.getUint32(24, true)).toBe(16000); expect(v.getUint16(22, true)).toBe(1); expect(v.getUint16(34, true)).toBe(16);
    expect(w.length).toBe(44 + 16 * 2); expect(v.getInt16(44, true)).toBe(16383); // 0.5 * 32767 troncato
  });
});
