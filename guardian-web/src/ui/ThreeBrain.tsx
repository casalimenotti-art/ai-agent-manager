import { useEffect, useMemo, useRef } from 'react';
import type { MeshBasicMaterial, Points, PointsMaterial } from 'three';
import type { StatoNucleo } from '../logic/guardian';
import { statoAgente } from '../logic/status';
import type { Agent, Device } from '../types';

type Macchina = { id: number | null; nome: string; stato: string; agenti: Agent[] };

function macchinePerScena(dispositivi: Device[], agenti: Agent[]): Macchina[] {
  const elenco = dispositivi.slice(0, 3).map((device) => {
    const perId = agenti.filter((agent) => agent.device_id === device.id);
    const perUtente = dispositivi.filter((d) => d.user_id === device.user_id).length === 1
      ? agenti.filter((agent) => !agent.device_id && agent.user_id === device.user_id) : [];
    return { id: device.id, nome: device.nome, stato: device.stato, agenti: [...perId, ...perUtente] };
  });
  while (elenco.length < 3) elenco.push({ id: null, nome: 'PC non collegato', stato: 'offline', agenti: [] });
  return elenco;
}

function statoMacchina(macchina: Macchina): string {
  if (macchina.id === null) return 'Registra un PC';
  if (macchina.agenti.some((agent) => statoAgente(agent) === 'working')) return 'Al lavoro';
  if (macchina.stato === 'online') return 'Collegato';
  if (['connecting', 'in_collegamento'].includes(macchina.stato)) return 'In collegamento';
  if (macchina.stato === 'error') return 'Errore';
  return 'Scollegato';
}

const PALETTE: Record<StatoNucleo, number> = {
  offline: 0x8a93a6, error: 0xffb4a8, listening: 0xdceBff, speaking: 0xdceBff,
  thinking: 0xf2f6ff, approval: 0xffd9a0, working: 0xf2f6ff, idle: 0xf2f6ff,
};

/** Cervello Three.js caricato solo quando Atlas è già visibile; il Canvas 2D resta il fallback. */
export function ThreeBrain({ stato, ridotto = false, dispositivi = [], agenti = [], onReady, onFallback, onApriDispositivi }: {
  stato: StatoNucleo; ridotto?: boolean; dispositivi?: Device[]; agenti?: Agent[]; onReady?: () => void;
  onFallback?: () => void; onApriDispositivi?: () => void;
}) {
  const host = useRef<HTMLDivElement>(null);
  const statoRef = useRef(stato); statoRef.current = stato;
  const ridottoRef = useRef(ridotto); ridottoRef.current = ridotto;
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
        neural.add(core);
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

        const machinePositions = [new THREE.Vector3(-2.2, 1.05, -0.25), new THREE.Vector3(2.2, 1.05, -0.25), new THREE.Vector3(0, -2.05, 0.12)];
        const machineCurves: import('three').CatmullRomCurve3[] = [];
        const activeMarkers: { mesh: import('three').Mesh; curve: import('three').CatmullRomCurve3; phase: number }[] = [];
        const machineGroup = new THREE.Group(); scene.add(machineGroup);
        machineData.forEach((machine, index) => {
          const point = machinePositions[index];
          const curve = new THREE.CatmullRomCurve3([new THREE.Vector3(0, 0, 0),
            new THREE.Vector3(point.x * 0.44 + (index - 1) * 0.18, point.y * 0.42, 0.18), point]);
          machineCurves.push(curve);
          const pathPoints = curve.getPoints(42);
          const pathGeometry = new THREE.BufferGeometry().setFromPoints(pathPoints);
          const activeCount = machine.agenti.filter((agent) => statoAgente(agent) === 'working').length;
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
          for (let i = 0; i < activeCount; i++) {
            const marker = new THREE.Mesh(new THREE.SphereGeometry(0.035, 10, 8), new THREE.MeshBasicMaterial({ color: 0x9fe8f5,
              transparent: true, opacity: 0.92, blending: THREE.AdditiveBlending }));
            machineGroup.add(marker);
            activeMarkers.push({ mesh: marker, curve, phase: i / Math.max(1, activeCount) });
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
        let seed = 9173;
        const random = () => { seed = seed * 16807 % 2147483647; return seed / 2147483647; };
        for (let i = 0; i < 440; i++) {
          stars[i * 3] = (random() - 0.5) * 15;
          stars[i * 3 + 1] = (random() - 0.5) * 9;
          stars[i * 3 + 2] = -random() * 8;
        }
        const starGeometry = new THREE.BufferGeometry(); starGeometry.setAttribute('position', new THREE.BufferAttribute(stars, 3));
        const starField = new THREE.Points(starGeometry, new THREE.PointsMaterial({ color: 0xf2f6ff, size: 0.012, transparent: true,
          opacity: 0.32, depthWrite: false }));
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
        let start = 0; let last = 0; let count = 0; let fpsStart = 0;
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
        };
        const up = () => { drag = null; };
        const wheel = (event: WheelEvent) => {
          if (!free(event.target)) return;
          zoom = Math.max(4.8, Math.min(10, zoom * Math.exp(event.deltaY * 0.001)));
        };
        const key = (event: KeyboardEvent) => {
          if (event.key === 'Escape') { yaw = 0; pitch = 0; zoom = 7.2; }
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
          const color = PALETTE[statoAttuale];
          (core.material as MeshBasicMaterial).color.setHex(color);
          (shellPoints.material as PointsMaterial).color.setHex(color);
          const busy = statoAttuale === 'thinking' || statoAttuale === 'working' || statoAttuale === 'listening' || statoAttuale === 'speaking';
          const breath = 1 + Math.sin(t * (busy ? 1.8 : 0.55)) * (busy ? 0.045 : 0.03);
          neural.scale.setScalar(breath);
          neural.rotation.y += 0.00072;
          neural.rotation.x = pitch + Math.sin(t / 13) * 0.06;
          neural.rotation.z = yaw + Math.sin(t / 17) * 0.025;
          rings.forEach((ring, i) => { ring.rotation.z = t * (i === 1 ? -0.022 : 0.016); });
          activeMarkers.forEach(({ mesh, curve, phase }) => mesh.position.copy(curve.getPoint((t * 0.045 + phase) % 1)));
          machineGroup.rotation.y = Math.sin(t / 19) * 0.025;
          starField.rotation.z = t * 0.00016;
          camera.position.x += (pointerX * 0.036 - camera.position.x) * 0.025;
          camera.position.y += (-pointerY * 0.036 - camera.position.y) * 0.025;
          camera.position.z += (zoom - camera.position.z) * 0.08;
          renderer?.render(scene, camera);
          if (now - fpsStart >= 1000) {
            rootEl?.setAttribute('data-atlas-fps', String(Math.round(count * 1000 / (now - fpsStart))));
            count = 0; fpsStart = now;
          }
        };
        const drawStill = () => renderer?.render(scene, camera);
        const visibility = () => {
          if (document.hidden || ridottoRef.current) { cancelAnimationFrame(frame); drawStill(); }
          else { last = 0; frame = requestAnimationFrame(draw); }
        };
        const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
        const changeMotion = () => { if (motion.matches) { cancelAnimationFrame(frame); drawStill(); } else if (!document.hidden) frame = requestAnimationFrame(draw); };
        document.addEventListener('visibilitychange', visibility); motion.addEventListener('change', changeMotion);
        if (ridottoRef.current) drawStill(); else frame = requestAnimationFrame(draw);
        stop = () => {
          cancelAnimationFrame(frame); observer.disconnect(); document.removeEventListener('visibilitychange', visibility);
          motion.removeEventListener('change', changeMotion); window.removeEventListener('pointerdown', down);
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
          rootEl?.setAttribute('data-three-ready', 'false');
        };
      } catch {
        renderer?.dispose(); renderer?.domElement.remove(); fallback();
      }
    }).catch(fallback);

    return () => { chiuso = true; stop?.(); cancelAnimationFrame(frame); };
  }, [machineData, onReady, onFallback]);

  return (
    <div className="three-brain" ref={host} data-stato={stato}>
      <div className="machine-stars" aria-label="Dispositivi collegati">
        {machineData.map((machine, i) => {
          const posizione = [{ left: '35%', top: '34%' }, { left: '66%', top: '34%' }, { left: '50%', top: '72%' }][i];
          const label = machine.id === null ? 'PC non collegato — Registra un PC' : `${machine.nome}, ${statoMacchina(machine)}, ${machine.agenti.length} agenti`;
          return <button key={machine.id ?? `slot-${i}`} className={`machine-star${machine.id === null ? ' is-empty' : ''}`}
            style={posizione} aria-label={label} title={label} onClick={onApriDispositivi}>
            <span className="machine-star-point" aria-hidden="true" />
            <span className="machine-star-label">{machine.id === null ? `PC ${i + 1} · non collegato` : machine.nome}</span>
            <span className="machine-star-state">{statoMacchina(machine)} · {machine.agenti.length} agenti</span>
          </button>;
        })}
      </div>
    </div>
  );
}
