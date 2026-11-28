import { useEffect, useRef } from 'react';

/** Core 3D opzionale: Atlas resta visibile sotto, pronto come fallback WebGL. */
export function ThreeBrain({ attivo }: { attivo: boolean }) {
  const host = useRef<HTMLDivElement>(null);
  const attivoRef = useRef(attivo); attivoRef.current = attivo;
  useEffect(() => {
    let chiuso = false;
    let frame = 0;
    let renderer: import('three').WebGLRenderer | undefined;
    let dispose: (() => void) | undefined;
    void import('three').then((THREE) => {
      if (chiuso || !host.current) return;
      try {
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
        camera.position.z = 8;
        renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' });
        renderer.setPixelRatio(Math.min(1.5, window.devicePixelRatio || 1));
        renderer.setClearColor(0x000000, 0);
        host.current.appendChild(renderer.domElement);
        const gruppo = new THREE.Group(); scene.add(gruppo);
        const core = new THREE.Mesh(new THREE.IcosahedronGeometry(0.72, 3), new THREE.MeshBasicMaterial({ color: 0xf2f6ff }));
        gruppo.add(core);
        const shellGeom = new THREE.SphereGeometry(1.25, 40, 32);
        const count = shellGeom.attributes.position.count;
        const points = new THREE.Points(shellGeom, new THREE.PointsMaterial({ color: 0xdce8ff, size: 0.022, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending, depthWrite: false }));
        gruppo.add(points);
        const rings: THREE.Points[] = [];
        for (const [radius, tilt] of [[1.65, 0.35], [1.85, -0.65], [1.48, 1.05]]) {
          const positions = new Float32Array(120 * 3);
          for (let i = 0; i < 120; i++) { const a = i / 120 * Math.PI * 2; positions[i * 3] = Math.cos(a) * radius; positions[i * 3 + 1] = Math.sin(a) * radius; }
          const geometry = new THREE.BufferGeometry(); geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
          const ring = new THREE.Points(geometry, new THREE.PointsMaterial({ color: 0xcdefff, size: 0.025, transparent: true, opacity: 0.58, blending: THREE.AdditiveBlending }));
          ring.rotation.x = tilt; gruppo.add(ring); rings.push(ring);
        }
        // Polvere lontana stabile, decorativa, resa nello stesso ciclo del nucleo.
        const stars = new Float32Array(420 * 3);
        let seed = 9173; const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
        for (let i = 0; i < 420; i++) { stars[i * 3] = (rnd() - .5) * 15; stars[i * 3 + 1] = (rnd() - .5) * 9; stars[i * 3 + 2] = -rnd() * 8; }
        const starGeo = new THREE.BufferGeometry(); starGeo.setAttribute('position', new THREE.BufferAttribute(stars, 3));
        const starField = new THREE.Points(starGeo, new THREE.PointsMaterial({ color: 0xf2f6ff, size: 0.012, transparent: true, opacity: 0.38 })); scene.add(starField);
        const size = () => { if (!host.current || !renderer) return; const w = host.current.clientWidth || innerWidth; const h = host.current.clientHeight || innerHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); };
        size(); const ro = new ResizeObserver(size); ro.observe(host.current);
        const start = performance.now(); let last = 0;
        const draw = (now: number) => { frame = requestAnimationFrame(draw); if (document.hidden || now - last < 33) return; last = now;
          const t = (now - start) / 1000; gruppo.rotation.y = t * Math.PI * 2 / 90; gruppo.rotation.x = Math.sin(t / 13) * 0.06;
          const breathe = 1 + Math.sin(t * (attivoRef.current ? 1.8 : 0.55)) * (attivoRef.current ? .045 : .03); gruppo.scale.setScalar(breathe);
          rings.forEach((ring, i) => { ring.rotation.z = t * (i % 2 ? -0.025 : 0.018); }); starField.rotation.z = t * 0.0008;
          renderer?.render(scene, camera);
        };
        frame = requestAnimationFrame(draw);
        dispose = () => { cancelAnimationFrame(frame); ro.disconnect(); scene.traverse((o) => { if (o instanceof THREE.Mesh || o instanceof THREE.Points) { o.geometry.dispose(); const m = o.material; Array.isArray(m) ? m.forEach((x) => x.dispose()) : m.dispose(); } }); renderer?.dispose(); renderer?.domElement.remove(); };
        void count;
      } catch { renderer?.dispose(); renderer?.domElement.remove(); }
    }).catch(() => { /* Atlas 2D rimane come fallback */ });
    return () => { chiuso = true; dispose?.(); cancelAnimationFrame(frame); };
  }, []);
  return <div className="three-brain" ref={host} aria-hidden="true" />;
}
