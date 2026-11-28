// Compositore WebGL2 degli strati del volto (renderizzati in Blender): un solo fragment shader a schermo intero.
import type { Uscite } from './stati';

export interface Meta {
  larghezza: number; altezza: number;
  occhio: { centro: [number, number]; asse_x: [number, number]; asse_y: [number, number] };
  iride: { rettangolo: [number, number, number, number]; colonne: number; righe: number; fotogrammi: number };
}
export const STRATI = ['base', 'luce', 'anelli', 'bocca', 'iride', 'profondita'] as const;
export type Strato = (typeof STRATI)[number];

const VS = `#version 300 es
in vec2 p; out vec2 v;
void main() { v = p * 0.5 + 0.5; gl_Position = vec4(p, 0.0, 1.0); }`;

const FS = `#version 300 es
precision highp float;
in vec2 v; out vec4 o;
uniform sampler2D tBase, tLuce, tAnelli, tBocca, tIride, tProf;
uniform vec2 schermo, img, sposta; uniform float scala;
uniform vec2 centro, ax, ay; uniform vec4 rIride; uniform vec2 griglia;
uniform float occhio, anelli, rotazione, iride, bocca, flash, scansione, tempo, esposizione;
uniform vec3 colOcchio, colAnelli; uniform vec2 parallasse;
float hash(vec2 q) { return fract(sin(dot(q, vec2(12.9898, 78.233))) * 43758.5453); }
vec3 tex(sampler2D t, vec2 px) { return texture(t, px / img).rgb; }
void main() {
  vec2 frag = vec2(v.x, 1.0 - v.y) * schermo;                    // pixel dello schermo, y verso il basso
  vec2 px = (frag - sposta) / scala;                              // pixel dell'immagine
  float d = texture(tProf, px / img).r;
  px -= parallasse * (d - 0.35) / scala * 1.6;                    // il vicino si muove più del lontano
  vec3 base = tex(tBase, px) * esposizione;
  vec3 luce = tex(tLuce, px);
  // coordinate dell'occhio: cerchio unitario = raggio 0.30 m nel mondo
  mat2 M = mat2(ax, ay); vec2 q = inverse(M) * (px - centro); float r = length(q);
  float maschera = 1.0 - smoothstep(1.05, 1.32, r);
  // iride a flipbook (fotogrammi dell'occhio acceso con l'iride sempre più aperta)
  vec2 loc = (px - rIride.xy) / rIride.zw;
  vec3 occhioAcceso = base + luce;
  if (loc.x > 0.0 && loc.y > 0.0 && loc.x < 1.0 && loc.y < 1.0) {
    float f = iride * (griglia.x * griglia.y - 1.0); float f0 = floor(f); float f1 = min(f0 + 1.0, griglia.x * griglia.y - 1.0);
    vec2 c0 = vec2(mod(f0, griglia.x), floor(f0 / griglia.x)), c1 = vec2(mod(f1, griglia.x), floor(f1 / griglia.x));
    vec3 i0 = texture(tIride, (c0 + loc) / griglia).rgb, i1 = texture(tIride, (c1 + loc) / griglia).rgb;
    occhioAcceso = mix(occhioAcceso, mix(i0, i1, fract(f)) * esposizione + luce * (1.0 - esposizione), maschera);
  }
  float sfarfallio = 1.0 + 0.025 * sin(tempo * 7.3) * sin(tempo * 3.1 + 1.7);
  float I = occhio * sfarfallio;
  vec3 col = base + (occhioAcceso - base) * I * colOcchio + luce * flash * 0.8;
  // anelli ruotati nello spazio dell'occhio
  float cs = cos(rotazione), sn = sin(rotazione);
  vec2 pr = centro + M * (mat2(cs, sn, -sn, cs) * q);
  col += tex(tAnelli, pr) * anelli * colAnelli * 0.75;
  col += tex(tBocca, px) * bocca;
  // scansione mentre pensa: una banda che scorre nell'occhio
  float banda = exp(-pow((q.y - (fract(tempo * 0.6) * 2.4 - 1.2)) * 9.0, 2.0)) * (1.0 - smoothstep(0.8, 1.0, r));
  col += vec3(0.25, 0.6, 1.0) * banda * scansione * 0.35;
  // vignettatura e grana
  vec2 c = (v - 0.5) * vec2(schermo.x / schermo.y, 1.0);
  col *= mix(1.0, smoothstep(1.15, 0.25, length(c)), 0.75);
  col += (hash(frag + fract(tempo) * 97.0) - 0.5) * 0.025;
  o = vec4(max(col, 0.0), 1.0);
}`;

export class Compositore {
  private gl: WebGL2RenderingContext;
  private u: Record<string, WebGLUniformLocation | null> = {};
  constructor(private canvas: HTMLCanvasElement, meta: Meta, immagini: Record<Strato, ImageBitmap | HTMLImageElement>) {
    const gl = canvas.getContext('webgl2', { antialias: false, alpha: false, premultipliedAlpha: false, powerPreference: 'low-power' });
    if (!gl) throw new Error('WebGL2 non disponibile');
    this.gl = gl;
    const sh = (tipo: number, src: string) => {
      const s = gl.createShader(tipo)!; gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s) ?? 'shader');
      return s;
    };
    const p = gl.createProgram()!;
    gl.attachShader(p, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(p, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p) ?? 'link');
    gl.useProgram(p);
    const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(p, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    const nomiT: Record<Strato, string> = { base: 'tBase', luce: 'tLuce', anelli: 'tAnelli', bocca: 'tBocca', iride: 'tIride', profondita: 'tProf' };
    STRATI.forEach((s, i) => {
      const t = gl.createTexture(); gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, immagini[s]);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.uniform1i(gl.getUniformLocation(p, nomiT[s]), i);
    });
    for (const n of ['schermo', 'img', 'sposta', 'scala', 'centro', 'ax', 'ay', 'rIride', 'griglia', 'occhio', 'anelli', 'rotazione', 'iride',
      'bocca', 'flash', 'scansione', 'tempo', 'esposizione', 'colOcchio', 'colAnelli', 'parallasse']) this.u[n] = gl.getUniformLocation(p, n);
    const m = meta;
    gl.uniform2f(this.u.img, m.larghezza, m.altezza);
    gl.uniform2f(this.u.centro, ...m.occhio.centro); gl.uniform2f(this.u.ax, ...m.occhio.asse_x); gl.uniform2f(this.u.ay, ...m.occhio.asse_y);
    gl.uniform4f(this.u.rIride, ...m.iride.rettangolo); gl.uniform2f(this.u.griglia, m.iride.colonne, m.iride.righe);
    gl.uniform1f(this.u.esposizione, 0.82);
  }

  disegna(s: Uscite, rotazione: number, tempo: number, sposta: { scala: number; x: number; y: number }) {
    const { gl, u, canvas } = this;
    gl.viewport(0, 0, canvas.width, canvas.height);
    const dpr = canvas.width / canvas.clientWidth || 1;
    gl.uniform2f(u.schermo, canvas.width, canvas.height);
    gl.uniform2f(u.sposta, sposta.x * dpr, sposta.y * dpr); gl.uniform1f(u.scala, sposta.scala * dpr);
    gl.uniform1f(u.occhio, s.intensitaOcchio); gl.uniform1f(u.anelli, s.intensitaAnelli); gl.uniform1f(u.rotazione, rotazione);
    gl.uniform1f(u.iride, s.aperturaIride); gl.uniform1f(u.bocca, s.intensitaBocca); gl.uniform1f(u.flash, s.flash);
    gl.uniform1f(u.scansione, s.scansione); gl.uniform1f(u.tempo, tempo);
    gl.uniform3f(u.colOcchio, ...s.coloreOcchio); gl.uniform3f(u.colAnelli, ...s.coloreAnelli);
    gl.uniform2f(u.parallasse, s.parallasse[0] * dpr, s.parallasse[1] * dpr);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }

  distruggi() { this.gl.getExtension('WEBGL_lose_context')?.loseContext(); }
}
