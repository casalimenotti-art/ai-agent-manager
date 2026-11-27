# Decisioni (registro breve)

## 2026-11-27 · Voce di Guardian (italiana, femminile, in tempo reale)
- **Contesto**: il titolare vuole parlare con Guardian e sentirlo rispondere a voce, come in una conversazione.
- **Opzioni**: (A) voci del sistema nel browser (Web Speech API) · (B) Piper locale con voce `it_IT-paola-medium` · (C) servizi cloud (ElevenLabs, ecc.).
- **Scelta**: **A subito**. Zero installazioni, funziona frase per frase mentre la risposta arriva, preferisce una voce femminile **locale** (su Windows «Microsoft Elsa»). Le voci «online» (es. «Google italiano», voci Edge «Online») inviano il testo al servizio del browser: il pannello le segnala.
- **Perché non B per ora**: licenza della voce `paola` e dimensione del modello **non verificate** (huggingface.co non raggiungibile durante la ricerca); `piper-tts` è GPL-3.0; serve un controllo del MODEL_CARD prima dell'uso commerciale. Resta l'upgrade di qualità offline, da fare dopo la verifica.
- **Perché non C**: il testo uscirebbe dal PC e costa; non richiesto.
- **Riconoscimento della voce (ascolto)**: locale con `faster-whisper 1.2.1` (versione fissata, solo wheel); l'audio non lascia il PC; il modello (~140 MB) si scarica una volta da Hugging Face.
- **Mani libere**: componente `componenti/mic_continuo` (rilevamento delle pause nel browser, WAV 16 kHz); tace mentre Guardian lavora o parla (niente auto-ascolto).
- **Limiti**: la qualità dipende dalle voci installate nel sistema; audio e microfono reali non sono stati provati in questo ambiente (test con sintesi simulata e microfono finto); `components.html` è in dismissione in Streamlit: adattatore `frame.py` con ripiego su `st.iframe`.
- **Come tornare indietro**: toggle «Guardian parla» spento; il microfono a mani libere si ferma con «Ferma conversazione».
