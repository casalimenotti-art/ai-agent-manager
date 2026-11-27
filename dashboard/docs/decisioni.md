# Decisioni (registro breve)

## 2026-11-27 · Voce di Guardian (italiana, femminile, frase per frase)
- **Scelta**: voci del sistema nel browser (Web Speech API), `voce_out.py`. Su Windows «Microsoft Elsa» è locale: il testo non esce dal PC. Le voci «online» (Google italiano, Edge «Online») lo mandano al servizio del browser: il pannello Voce le segnala.
- **Ascolto**: locale (faster-whisper / sherpa / Windows). Mani libere: componente `componenti/mic_continuo` (pause rilevate nel browser, WAV 16 kHz), tace mentre Guardian lavora o parla. Il testo capito è sempre mostrato.
- **Non portato**: le chat in parallelo (`lavori.py`) del commit d8097e7: Guardian locale ha già un'interfaccia compatta diversa.
- **Indietro**: toggle «Voce» spento; «Conversazione a voce» spento.
- **Limiti**: audio e microfono reali dipendono dal browser; `components.html` è in dismissione, adattatore `frame.py`.
