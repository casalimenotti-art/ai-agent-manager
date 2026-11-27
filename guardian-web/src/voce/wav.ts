// Audio per il servizio vocale locale: ricampionamento a 16 kHz e WAV PCM 16 bit mono (come mic_continuo).
export const SR_DESTINAZIONE = 16000;

export function ricampiona(campioni: Float32Array, srOrigine: number, srDest = SR_DESTINAZIONE): Float32Array {
  if (srOrigine === srDest) return campioni;
  const rapporto = srOrigine / srDest; const n = Math.floor(campioni.length / rapporto); const out = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const da = Math.floor(i * rapporto), a = Math.min(campioni.length, Math.floor((i + 1) * rapporto));
    let s = 0; for (let j = da; j < a; j++) s += campioni[j];
    out[i] = a > da ? s / (a - da) : 0;
  }
  return out;
}

export function wav16(campioni: Float32Array, sr = SR_DESTINAZIONE): Uint8Array {
  const buf = new ArrayBuffer(44 + campioni.length * 2); const v = new DataView(buf);
  const testo = (o: number, s: string) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
  testo(0, 'RIFF'); v.setUint32(4, 36 + campioni.length * 2, true); testo(8, 'WAVE'); testo(12, 'fmt ');
  v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true); v.setUint32(24, sr, true);
  v.setUint32(28, sr * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true); testo(36, 'data'); v.setUint32(40, campioni.length * 2, true);
  for (let i = 0; i < campioni.length; i++) { const x = Math.max(-1, Math.min(1, campioni[i])); v.setInt16(44 + i * 2, x < 0 ? x * 0x8000 : x * 0x7fff, true); }
  return new Uint8Array(buf);
}

export function unisci(parti: Float32Array[]): Float32Array {
  const out = new Float32Array(parti.reduce((n, p) => n + p.length, 0)); let o = 0;
  for (const p of parti) { out.set(p, o); o += p.length; }
  return out;
}
