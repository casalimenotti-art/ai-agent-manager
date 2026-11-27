import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import './styles/tokens.css';
import './styles/app.css';
import './styles/volto.css';
import '@fontsource/barlow-condensed/600.css';

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);

// Ondata 10: app installabile. Il service worker salva solo la shell statica, mai i dati (vedi public/sw.js).
if (import.meta.env.PROD && 'serviceWorker' in navigator && location.protocol !== 'file:') {
  window.addEventListener('load', () => { navigator.serviceWorker.register('/sw.js').catch(() => { /* senza SW l'app funziona lo stesso */ }); });
}
