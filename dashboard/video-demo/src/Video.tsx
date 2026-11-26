import React from 'react';
import {AbsoluteFill, Easing, interpolate, Sequence, spring, useCurrentFrame, useVideoConfig} from 'remotion';

const COLORI = [['#00f0ff', '#0a1a3a'], ['#ff2bd6', '#2a0a2a'], ['#fcee0a', '#2a2a0a'], ['#3dffa0', '#0a2a1a'], ['#7c9cff', '#10143a']];
const SFONDO = 'radial-gradient(900px 500px at 20% 0%, #10244a 0%, #070a14 60%)';
const FONT = 'ui-monospace, Menlo, Consolas, monospace';

const Carta: React.FC<{i: number; rot: number}> = ({i, rot}) => {
  const [a, b] = COLORI[i];
  const ang = i * 72 + rot;
  return (
    <div style={{position: 'absolute', width: 300, height: 400, left: 490, top: 150, transform: `rotateY(${ang}deg) translateZ(430px)`,
      background: `linear-gradient(160deg, ${a}33, ${b})`, border: `2px solid ${a}`, boxShadow: `0 0 40px ${a}55`, display: 'flex',
      flexDirection: 'column', justifyContent: 'flex-end', padding: 24, color: '#e8f1ff', fontFamily: FONT, backfaceVisibility: 'hidden'}}>
      <div style={{fontSize: 14, letterSpacing: 6, color: a}}>FOTO {i + 1}</div>
      <div style={{fontSize: 26, marginTop: 6}}>Segnaposto</div>
    </div>
  );
};

const Carosello: React.FC = () => {
  const f = useCurrentFrame();
  const rot = interpolate(f, [0, 170], [0, -216], {easing: Easing.inOut(Easing.cubic), extrapolateRight: 'clamp'});
  const zoom = interpolate(f, [100, 170], [1, 1.35], {easing: Easing.inOut(Easing.quad), extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const tilt = interpolate(f, [0, 170], [14, 4]);
  return (
    <AbsoluteFill style={{perspective: 1500, transform: `scale(${zoom})`}}>
      <AbsoluteFill style={{transformStyle: 'preserve-3d', transform: `rotateX(${tilt}deg)`}}>
        {COLORI.map((_, i) => <Carta key={i} i={i} rot={rot} />)}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Titolo: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: f, fps, config: {damping: 14}});
  const y = interpolate(s, [0, 1], [60, 0]);
  const op = interpolate(f, [0, 12, 80, 100], [0, 1, 1, 0], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 60, opacity: op, transform: `translateY(${y}px)`}}>
      <div style={{fontFamily: FONT, color: '#e8f1ff', fontSize: 54, letterSpacing: 10, textShadow: '0 0 24px #00f0ff'}}>ESEMPIO · LA TUA ATTIVITÀ</div>
    </AbsoluteFill>
  );
};

const Cta: React.FC = () => {
  const f = useCurrentFrame();
  const w = interpolate(f, [0, 30], [0, 100], {extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const op = interpolate(f, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', background: 'rgba(7,10,20,.88)', opacity: op}}>
      <div style={{fontFamily: FONT, color: '#e8f1ff', fontSize: 64, letterSpacing: 8}}>PRENOTA ORA</div>
      <div style={{height: 6, width: `${w * 4}px`, background: 'linear-gradient(90deg,#00f0ff,#ff2bd6)', marginTop: 24, boxShadow: '0 0 20px #00f0ff'}} />
      <div style={{fontFamily: FONT, color: '#8b97b3', fontSize: 22, marginTop: 28}}>video dimostrativo · foto segnaposto</div>
    </AbsoluteFill>
  );
};

export const Video: React.FC = () => {
  const f = useCurrentFrame();
  const wipe = interpolate(f, [168, 186], [-100, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: SFONDO}}>
      <Carosello />
      <Sequence from={0} durationInFrames={110}><Titolo /></Sequence>
      <AbsoluteFill style={{transform: `translateX(${wipe}%)`, background: 'linear-gradient(90deg,#00f0ff,#ff2bd6)'}} />
      <Sequence from={176}><Cta /></Sequence>
    </AbsoluteFill>
  );
};
