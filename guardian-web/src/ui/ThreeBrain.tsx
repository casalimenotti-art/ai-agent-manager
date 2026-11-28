import { useEffect, useMemo, useRef } from 'react';
import type { MeshBasicMaterial, Points, PointsMaterial } from 'three';
import type { StatoNucleo } from '../logic/guardian';
import { macchinePerScena, puntoPercorso3D, statoAgenteVisuale, statoMacchinaVisuale, type PercorsoSpazio } from '../logic/spazio';
import type { ActivityEvent, Agent, Device } from '../types';

const PALETTE: Record<StatoNucleo, number> = {
  offline: 0x8a93a6, error: 0xffb4a8, listening: 0xdceBff, speaking: 0xdceBff,
  thinking: 0xf2f6ff, approval: 0xffd9a0, working: 0xf2f6ff, completed: 0xf2f6ff, idle: 0xf2f6ff,
};

/** Cervello Three.js caricato solo quando Atlas è già visibile; il Canvas 2D resta il fallback. */
export function ThreeBrain({ stato, ridotto = false, dispositivi = [], agenti = [], eventi = [], pannelloAperto = false,
  onReady, onFallback, onApriDispositivi, onApriAgente }: {
  stato: StatoNucleo; ridotto?: boolean; dispositivi?: Device[]; agenti?: Agent[]; eventi?: ActivityEvent[]; pannelloAperto?: boolean;
  onReady?: () => void; onFallback?: () => void; onApriDispositivi?: (id: number | null) => void; onApriAgente?: (id: string) => void;
}) {
  const host = useRef<HTMLDivElement>(null);
  const statoRef = useRef(stato); statoRef.current = stato;
  const ridottoRef = useRef(ridotto); ridottoRef.current = ridotto;
  const pannelloRef = useRef(pannelloAperto); pannelloRef.current = pannelloAperto;
  const materialiStato = useRef<(MeshBasicMaterial | PointsMaterial)[]>([]);
  const ridisegna = useRef<() => void>(() => {});
  const haloRef = useRef<MeshBasicMaterial | null>(null);
  const machineData = useMemo(() => macchinePerScena(dispositivi, agenti), [dispositivi, agenti]);

  useEffect(() => {
    let chiuso = false;
    let frame = 0;
    let stop: (() => void) | undefined;
    let renderer: import('three').WebGLRenderer | undefined;
    const fallback = () => { host.current?.closest('.atlas-sfondo')?.setAttribute('data-three-ready', 'false'); onFallback?.(); };

    void import('three').then((THREE) => {
      if (chiuso || !host.current) return;
      try {
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
        camera.position.z = 7.2;
        renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' });
        renderer.setPixelRatio(Math.min(1.5, window.devicePixelRatio || 1));
        renderer.setClearColor(0x000000, 0);
        renderer.domElement.setAttribute('aria-hidden', 'true');
        host.current.appendChild(renderer.domElement);

        const root = new THREE.Group(); scene.add(root);
        const neural = new THREE.Group(); root.add(neural);
        const core = new THREE.Mesh(new THREE.IcosahedronGeometry(0.64, 4), new THREE.MeshBasicMaterial({
          color: 0xf2f6ff, transparent: true, opacity: 0.94, blending: THREE.AdditiveBlending,
        }));
        materialiStato.current = [core.material as MeshBasicMaterial];
        neural.add(core);
        const haloMaterial = new THREE.MeshBasicMaterial({ color: 0xffd9a0, transparent: true, opacity: 0.08,
          side: THREE.BackSide, blending: THREE.AdditiveBlending, depthWrite: false });
        const halo = new THREE.Mesh(new THREE.SphereGeometry(0.96, 36, 28), haloMaterial);
        halo.visible = false; neural.add(halo); haloRef.current = haloMaterial;
        const inner = new THREE.Mesh(new THREE.SphereGeometry(0.34, 32, 24), new THREE.MeshBasicMaterial({
          color: 0xffffff, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending,
        }));
        neural.add(inner);

        const shellGeometry = new THREE.SphereGeometry(1.04, 58, 44);
        const shellPositions = shellGeometry.attributes.position.array as Float32Array;
        const shell = new THREE.BufferGeometry();
        shell.setAttribute('position', new THREE.BufferAttribute(shellPositions.slice(), 3));
        const shellPoints = new THREE.Points(shell, new THREE.PointsMaterial({ color: 0xdceBff, size: 0.026, transparent: true,
          opacity: 0.62, blending: THREE.AdditiveBlending, depthWrite: false, sizeAttenuation: true }));
        materialiStato.current.push(shellPoints.material as PointsMaterial);
        neural.add(shellPoints);

        const filaments = new Float32Array(78 * 6);
        for (let i = 0; i < 78; i++) {
          const a = Math.floor((i * 37) % (shellPositions.length / 3)) * 3;
          const b = Math.floor((i * 83 + 29) % (shellPositions.length / 3)) * 3;
          filaments.set(shellPositions.slice(a, a + 3), i * 6);
          filaments.set(shellPositions.slice(b, b + 3), i * 6 + 3);
        }
        const filamentGeometry = new THREE.BufferGeometry();
        filamentGeometry.setAttribute('position', new THREE.BufferAttribute(filaments, 3));
        neural.add(new THREE.LineSegments(filamentGeometry, new THREE.LineBasicMaterial({ color: 0xdceBff, transparent: true,
          opacity: 0.075, blending: THREE.AdditiveBlending, depthWrite: false })));
        shellGeometry.dispose();

        const machinePositions = [new THREE.Vector3(-2.65, 1.45, -0.25), new THREE.Vector3(2.65, 1.45, -0.25), new THREE.Vector3(0, -1.55, 0.12)];
        const activeMarkers: { mesh: import('three').Mesh; curve: PercorsoSpazio; phase: number;
          beganAt: number | null; direction: 'out' | 'back' | 'hold' }[] = [];
        const machineGroup = new THREE.Group(); scene.add(machineGroup);
        machineData.forEach((machine, index) => {
          const point = machinePositions[index];
          const curve: PercorsoSpazio = { inizio: { x: 0, y: 0, z: 0 },
            controllo: { x: point.x * 0.44 + (index - 1) * 0.18, y: point.y * 0.42, z: 0.18 },
            fine: { x: point.x, y: point.y, z: point.z } };
          const pathPoints = Array.from({ length: 43 }, (_, i) => {
            const p = puntoPercorso3D(curve, i / 42); return new THREE.Vector3(p.x, p.y, p.z);
          });
          const pathGeometry = new THREE.BufferGeometry().setFromPoints(pathPoints);
          const activeCount = machine.agenti.filter((agent) => statoAgenteVisuale(agent) === 'working').length;
          const pathMaterial = new THREE.LineBasicMaterial({ color: activeCount ? 0xdceBff : 0xb3c1d8,
            transparent: true, opacity: activeCount ? 0.34 : 0.13, blending: THREE.AdditiveBlending, depthWrite: false });
          machineGroup.add(new THREE.Line(pathGeometry, pathMaterial));

          const node = new THREE.Group(); node.position.copy(point); machineGroup.add(node);
          const tint = machine.id === null ? 0x8a93a6 : machine.stato === 'online' ? 0xf2f6ff : 0x8a93a6;
          const orbit = new THREE.Points(new THREE.BufferGeometry(), new THREE.PointsMaterial({ color: tint, size: 0.025,
            transparent: true, opacity: machine.id === null ? 0.25 : 0.7, blending: THREE.AdditiveBlending }));
          const orbitPositions = new Float32Array(48 * 3);
          for (let i = 0; i < 48; i++) { const a = i / 48 * Math.PI * 2; orbitPositions[i * 3] = Math.cos(a) * 0.28; orbitPositions[i * 3 + 1] = Math.sin(a) * 0.16; }
          orbit.geometry.setAttribute('position', new THREE.BufferAttribute(orbitPositions, 3));
          orbit.rotation.x = index * 0.62; node.add(orbit);
          node.add(new THREE.Mesh(new THREE.IcosahedronGeometry(0.085, 1), new THREE.MeshBasicMaterial({ color: tint,
            transparent: true, opacity: machine.id === null ? 0.3 : 0.8, blending: THREE.AdditiveBlending })));
          const agents = machine.agenti;
          for (let i = 0; i < agents.length; i++) {
            const agent = agents[i];
            const latest = eventi.filter((event) => event.agent_id === agent.id && ['task_started', 'task_completed', 'task_failed', 'agent_error'].includes(event.event_type))
              .sort((a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp))[0];
            const statoAgent = statoAgenteVisuale(agent);
            const active = statoAgent === 'working';
            const waiting = statoAgent === 'approval';
            const error = statoAgent === 'error' && (latest?.event_type === 'task_failed' || latest?.event_type === 'agent_error');
            const age = latest ? Date.now() - Date.parse(latest.timestamp) : Number.POSITIVE_INFINITY;
            const returning = !active && latest?.event_type === 'task_completed' && age >= 0 && age < 1800;
            if (!active && !returning && !waiting && !error) continue;
            const marker = new THREE.Mesh(new THREE.SphereGeometry(error ? 0.045 : 0.035, 10, 8), new THREE.MeshBasicMaterial({ color: error ? 0xffb4a8 : waiting ? 0xffd9a0 : 0x9fe8f5,
              transparent: true, opacity: 0.92, blending: THREE.AdditiveBlending }));
            machineGroup.add(marker);
            activeMarkers.push({ mesh: marker, curve, phase: i / Math.max(1, agents.length),
              beganAt: returning && latest ? Date.parse(latest.timestamp) : active && latest?.event_type === 'task_started' && age >= 0 && age < 2800 ? Date.parse(latest.timestamp) : null,
              direction: waiting || error ? 'hold' : returning ? 'back' : 'out' });
          }
        });

        const rings: Points[] = [];
        for (const [radius, tilt, amount] of [[1.42, 0.38, 112], [1.62, -0.66, 136], [1.28, 1.04, 96]] as const) {
          const positions = new Float32Array(amount * 3);
          for (let i = 0; i < amount; i++) {
            const a = i / amount * Math.PI * 2;
            positions[i * 3] = Math.cos(a) * radius;
            positions[i * 3 + 1] = Math.sin(a) * radius;
          }
          const geometry = new THREE.BufferGeometry(); geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
          const points = new THREE.Points(geometry, new THREE.PointsMaterial({ color: 0xdceBff, size: 0.023, transparent: true,
            opacity: 0.57, blending: THREE.AdditiveBlending, depthWrite: false }));
          points.rotation.x = tilt; neural.add(points); rings.push(points);
        }

        // Campo stellare deterministico: decorazione, non rappresenta dati o traffico.
        const stars = new Float32Array(440 * 3);
        const starPhase = new Float32Array(440); const starPeriod = new Float32Array(440); const starSize = new Float32Array(440);
        let seed = 9173;
        const random = () => { seed = seed * 16807 % 2147483647; return seed / 2147483647; };
        for (let i = 0; i < 440; i++) {
          stars[i * 3] = (random() - 0.5) * 15;
          stars[i * 3 + 1] = (random() - 0.5) * 9;
          stars[i * 3 + 2] = -random() * 8;
          starPhase[i] = random() * Math.PI * 2; starPeriod[i] = 2 + random() * 4; starSize[i] = 0.6 + random() * 0.6;
        }
        const starGeometry = new THREE.BufferGeometry(); starGeometry.setAttribute('position', new THREE.BufferAttribute(stars, 3));
        starGeometry.setAttribute('aPhase', new THREE.BufferAttribute(starPhase, 1));
        starGeometry.setAttribute('aPeriod', new THREE.BufferAttribute(starPeriod, 1));
        starGeometry.setAttribute('aSize', new THREE.BufferAttribute(starSize, 1));
        const starMaterial = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
          uniforms: { uTime: { value: 0 } },
          vertexShader: `attribute float aPhase; attribute float aPeriod; attribute float aSize; uniform float uTime; varying float vAlpha;
            void main() { vec4 viewPosition = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * viewPosition;
              gl_PointSize = aSize; vAlpha = 0.32 * (1.0 + 0.15 * sin(6.28318 * uTime / aPeriod + aPhase)); }`,
          fragmentShader: `varying float vAlpha; void main() { float d = distance(gl_PointCoord, vec2(0.5));
            float shape = 1.0 - smoothstep(0.28, 0.5, d); gl_FragColor = vec4(0.95, 0.97, 1.0, vAlpha * shape); }`,
        });
        const starField = new THREE.Points(starGeometry, starMaterial);
        scene.add(starField);

        const size = () => {
          if (!host.current || !renderer) return;
          const w = host.current.clientWidth || window.innerWidth;
          const h = host.current.clientHeight || window.innerHeight;
          renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
        };
        size();
        const observer = new ResizeObserver(size); observer.observe(host.current);
        const rootEl = host.current.closest('.atlas-sfondo');
        rootEl?.setAttribute('data-three-ready', 'true');
        onReady?.();
        let start = 0; let last = 0; let count = 0; let fpsStart = 0; let fpsLentoDa = 0;
        let ultimoStato = ''; let cambiatoStato = 0;
        let yaw = 0; let pitch = 0; let zoom = 7.2;
        let drag: { x: number; y: number } | null = null;
        let pointerX = 0; let pointerY = 0;
        const free = (target: EventTarget | null) => !(target instanceof Element) || !target.closest('button,a,input,select,textarea,[role="dialog"],.dock,.rail,.header,.palette');
        const down = (event: PointerEvent) => { if (event.button === 0 && free(event.target)) drag = { x: event.clientX, y: event.clientY }; };
        const move = (event: PointerEvent) => {
          pointerX = (event.clientX / Math.max(1, innerWidth) - 0.5) * 2;
          pointerY = (event.clientY / Math.max(1, innerHeight) - 0.5) * 2;
          if (!drag) return;
          if (!free(event.target)) { drag = null; return; }
          yaw += (event.clientX - drag.x) * 0.006; pitch = Math.max(-0.75, Math.min(0.75, pitch + (event.clientY - drag.y) * 0.004));
          drag = { x: event.clientX, y: event.clientY };
          if (ridottoRef.current) ridisegna.current();
        };
        const up = () => { drag = null; };
        const wheel = (event: WheelEvent) => {
          if (!free(event.target)) return;
          zoom = Math.max(4.8, Math.min(10, zoom * Math.exp(event.deltaY * 0.001)));
          if (ridottoRef.current) ridisegna.current();
        };
        const key = (event: KeyboardEvent) => {
          if (event.key === 'Escape') { yaw = 0; pitch = 0; zoom = 7.2; if (ridottoRef.current) ridisegna.current(); }
        };
        window.addEventListener('pointerdown', down); window.addEventListener('pointermove', move);
        window.addEventListener('pointerup', up); window.addEventListener('pointercancel', up);
        window.addEventListener('wheel', wheel, { passive: true }); window.addEventListener('keydown', key);

        const draw = (now: number) => {
          frame = requestAnimationFrame(draw);
          if (document.hidden || now - last < 33) return;
          last = now; start ||= now; fpsStart ||= now; count++;
          const t = (now - start) / 1000;
          const statoAttuale = statoRef.current;
          if (statoAttuale !== ultimoStato) { ultimoStato = statoAttuale; cambiatoStato = now; }
          const color = PALETTE[statoAttuale];
          (core.material as MeshBasicMaterial).color.setHex(color);
          (shellPoints.material as PointsMaterial).color.setHex(color);
          (shellPoints.material as PointsMaterial).opacity = statoAttuale === 'offline' ? 0.24 : 0.62;
          halo.visible = statoAttuale === 'approval' || statoAttuale === 'error';
          haloMaterial.color.setHex(color); haloMaterial.opacity = statoAttuale === 'error' ? 0.09 : 0.07;
          halo.scale.setScalar(1 + (statoAttuale === 'approval' ? Math.sin(t * 0.8) * 0.018 : 0));
          const busy = statoAttuale === 'thinking' || statoAttuale === 'working' || statoAttuale === 'listening' || statoAttuale === 'speaking';
          const pulse = statoAttuale === 'completed' ? 0.055 * Math.max(0, 1 - (now - cambiatoStato) / 950) : 0;
          const breath = 1 + Math.sin(t * (busy ? 1.8 : 0.55)) * (busy ? 0.045 : 0.03) + pulse;
          neural.scale.setScalar(breath);
          neural.rotation.y = t * Math.PI * 2 / 90;
          neural.rotation.x = pitch + Math.sin(t / 13) * 0.06;
          neural.rotation.z = yaw + Math.sin(t / 17) * 0.025;
          rings.forEach((ring, i) => {
            ring.rotation.z = t * (i === 1 ? -0.022 : 0.016);
            if (statoAttuale === 'listening') ring.scale.setScalar(1 + Math.sin(t * 4 + i) * 0.025);
          });
          activeMarkers.forEach(({ mesh, curve, phase, beganAt, direction }) => {
            if (direction === 'hold') {
              const punto = puntoPercorso3D(curve, 1); mesh.position.set(punto.x, punto.y, punto.z);
            } else if (direction === 'back') {
              const age = Math.max(0, Math.min(1, (Date.now() - (beganAt ?? Date.now())) / 1800));
              const punto = puntoPercorso3D(curve, 1 - age); mesh.position.set(punto.x, punto.y, punto.z);
            } else if (beganAt !== null) {
              const progress = Math.max(0, Math.min(1, (Date.now() - beganAt) / 2800));
              const punto = puntoPercorso3D(curve, progress); mesh.position.set(punto.x, punto.y, punto.z);
            } else {
              const base = puntoPercorso3D(curve, 1);
              base.x += Math.cos(t * 0.32 + phase * Math.PI * 2) * 0.16;
              base.y += Math.sin(t * 0.32 + phase * Math.PI * 2) * 0.12;
              mesh.position.set(base.x, base.y, base.z);
            }
          });
          machineGroup.rotation.y = Math.sin(t / 19) * 0.025;
          starField.rotation.z = t * Math.PI * 2 / 450;
          starMaterial.uniforms.uTime.value = t;
          const shiftX = pannelloRef.current ? 0.52 : 0;
          const shiftY = pannelloRef.current && innerWidth < 600 ? -0.82 : 0;
          camera.position.x += (shiftX + pointerX * 0.036 - camera.position.x) * 0.025;
          camera.position.y += (shiftY - pointerY * 0.036 - camera.position.y) * 0.025;
          camera.position.z += (zoom - camera.position.z) * 0.08;
          renderer?.render(scene, camera);
          if (now - fpsStart >= 1000) {
            const fps = Math.round(count * 1000 / (now - fpsStart));
            rootEl?.setAttribute('data-atlas-fps', String(fps));
            if (fps < 24) fpsLentoDa ||= now; else fpsLentoDa = 0;
            if (fpsLentoDa && now - fpsLentoDa > 2000 && starGeometry.drawRange.count > 280) {
              starGeometry.setDrawRange(0, 280); rootEl?.setAttribute('data-atlas-polvere', '280'); fpsLentoDa = 0;
            }
            count = 0; fpsStart = now;
          }
        };
        const drawStill = () => {
          if (ridottoRef.current) {
            neural.rotation.y = 0; neural.rotation.x = pitch; neural.rotation.z = yaw;
            camera.position.x = (pannelloRef.current ? 0.52 : 0) + pointerX * 0.036;
            camera.position.y = (pannelloRef.current && innerWidth < 600 ? -0.82 : 0) - pointerY * 0.036;
            camera.position.z = zoom;
          }
          renderer?.render(scene, camera);
        };
        ridisegna.current = drawStill;
        const visibility = () => {
          if (document.hidden || ridottoRef.current) { cancelAnimationFrame(frame); drawStill(); }
          else { last = 0; frame = requestAnimationFrame(draw); }
        };
        const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
        const changeMotion = () => { if (motion.matches) { cancelAnimationFrame(frame); drawStill(); } else if (!document.hidden) frame = requestAnimationFrame(draw); };
        const contextLost = (event: Event) => { event.preventDefault(); cancelAnimationFrame(frame); rootEl?.setAttribute('data-atlas-fps', '0'); fallback(); };
        renderer?.domElement.addEventListener('webglcontextlost', contextLost);
        document.addEventListener('visibilitychange', visibility); motion.addEventListener('change', changeMotion);
        if (ridottoRef.current) drawStill(); else frame = requestAnimationFrame(draw);
        stop = () => {
          cancelAnimationFrame(frame); observer.disconnect(); document.removeEventListener('visibilitychange', visibility);
          motion.removeEventListener('change', changeMotion); renderer?.domElement.removeEventListener('webglcontextlost', contextLost); window.removeEventListener('pointerdown', down);
          window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up);
          window.removeEventListener('pointercancel', up); window.removeEventListener('wheel', wheel); window.removeEventListener('keydown', key);
          scene.traverse((object) => {
            if (object instanceof THREE.Mesh || object instanceof THREE.Points || object instanceof THREE.LineSegments) {
              object.geometry.dispose();
              const material = object.material;
              if (Array.isArray(material)) material.forEach((item) => item.dispose()); else material.dispose();
            }
          });
          renderer?.dispose(); renderer?.domElement.remove();
          materialiStato.current = []; haloRef.current = null; ridisegna.current = () => {};
          rootEl?.setAttribute('data-three-ready', 'false');
        };
      } catch {
        renderer?.dispose(); renderer?.domElement.remove(); fallback();
      }
    }).catch(fallback);

    return () => { chiuso = true; stop?.(); cancelAnimationFrame(frame); };
  }, [machineData, eventi, onReady, onFallback]);

  useEffect(() => {
    for (const material of materialiStato.current) material.color.setHex(PALETTE[stato]);
    if (haloRef.current) { haloRef.current.color.setHex(PALETTE[stato]); haloRef.current.opacity = stato === 'error' ? 0.09 : 0.07; }
    ridisegna.current();
  }, [stato]);
  useEffect(() => { ridisegna.current(); }, [pannelloAperto]);

  return (
    <div className="three-brain" ref={host} data-stato={stato}>
      <div className="machine-stars" role="group" aria-label="Dispositivi collegati">
        {machineData.map((machine, i) => {
          const posizione = [{ left: '28%', top: '26%' }, { left: '72%', top: '26%' }, { left: '50%', top: '77%' }][i];
          const label = machine.id === null ? 'PC non collegato — Registra un PC' : `${machine.nome}, ${statoMacchinaVisuale(machine)}, ${machine.agenti.length} agenti`;
          return <button key={machine.id ?? `slot-${i}`} className={`machine-star${machine.id === null ? ' is-empty' : ''}`}
            style={posizione} aria-label={label} title={label} onClick={() => onApriDispositivi?.(machine.id)}>
            <span className="machine-star-point" aria-hidden="true" />
            <span className="machine-star-label">{machine.id === null ? `PC ${i + 1} · non collegato` : machine.nome}</span>
            <span className="machine-star-state">{statoMacchinaVisuale(machine)} · {machine.agenti.length} agenti</span>
          </button>;
        })}
        {machineData.flatMap((machine, i) => machine.agenti
          .filter((agent) => ['working', 'approval', 'error'].includes(statoAgenteVisuale(agent)))
          .map((agent, j) => {
            const base = [{ left: '28%', top: '26%' }, { left: '72%', top: '26%' }, { left: '50%', top: '77%' }][i];
            const stato = statoAgenteVisuale(agent);
            const label = `${agent.nome}, ${stato === 'working' ? 'al lavoro' : stato === 'error' ? 'in errore' : 'in attesa di approvazione'}`;
            return <button key={agent.id} className={`agent-star${stato === 'approval' ? ' is-waiting' : stato === 'error' ? ' is-error' : ''}`}
              style={{ left: `calc(${base.left} + ${(j - 1) * 14}px)`, top: `calc(${base.top} + 22px)` }} aria-label={label} title={label}
              onClick={() => onApriAgente?.(agent.id)}>
              <span className="agent-star-point" aria-hidden="true" /><span className="agent-star-name">{agent.nome}</span>
            </button>;
          }))}
      </div>
    </div>
  );
}
